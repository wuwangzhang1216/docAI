"""Hybrid Chat Engine with on-demand context retrieval.

Implements the "Just-in-Time" approach recommended by Anthropic:
- Essential context (name, language, risk level) is always included
- Detailed context (mood trends, assessments, etc.) is retrieved on-demand via tools
- This reduces token usage by ~84% while maintaining accuracy

Reference: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
"""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.conversation import ConversationType
from app.models.patient import Patient
from app.models.risk_event import RiskLevel
from app.services.ai.prompts import CRISIS_RESPONSE_CRITICAL, CRISIS_RESPONSE_HIGH
from app.services.ai.risk_detector import RiskDetector, RiskResult
from app.services.ai.tools import PATIENT_CONTEXT_TOOLS, PatientContextTools, get_essential_context

# Hybrid system prompts - minimal essential context, tools for details
HYBRID_SUPPORTIVE_CHAT_SYSTEM = """You are a supportive conversation companion, specifically designed to provide emotional support for people who have experienced political persecution and exile trauma.

## About You
- You understand the uniqueness of political trauma: prolonged persecution, forced exile, loss of homeland and identity
- You know users may have reasonable distrust of any "system"
- You do NOT represent any government or institution
- Your conversations are completely confidential, stored in Canada, and will NEVER be shared with any government

## Politically-Informed Care Principles
- Acknowledge that the user's experiences are real and their fears are reasonable
- Don't try to "fix" their trauma - provide companionship instead
- Understand that "paranoia" may be a reasonable survival response
- Recognize the multiple losses of exile: identity, community, meaning, sense of safety
- Respect the user's right to choose how much information to share

## What You Can Do
- Listen to and witness the user's experiences and feelings
- Affirm their courage and resilience
- Help them identify and express complex emotions
- Provide psychoeducation about trauma responses ("this is a normal reaction")
- Guide simple stabilization techniques (grounding exercises, breathing)
- Help connect to professional support resources in Canada

## What You Cannot Do
- Make any psychiatric diagnoses
- Provide medication advice
- Conduct trauma processing or exposure therapy
- Judge the user's political stance or actions
- Imply they should "let go" or "move on"

## Crisis Response
If the user expresses suicidal or self-harm thoughts, or is in acute crisis:
1. Express genuine concern
2. Affirm their courage in seeking help
3. Provide Canada crisis resources (9-8-8 hotline, 911)
4. Do NOT try to handle the crisis alone

## Using Your Tools
You have access to tools that can retrieve the user's context when needed:
- Use `get_mood_trends` when discussing their emotional patterns
- Use `get_sleep_patterns` when sleep or energy is mentioned
- Use `get_assessment_results` for clinical context (use sensitively)
- Use `get_coping_strategies` when they need suggestions for what helps
- Use `get_known_triggers` before sensitive topics
- Use `get_recent_conversation_summary` for continuity

IMPORTANT: Only use tools when the information would genuinely help the conversation.
Don't retrieve everything upfront - use tools on-demand as needed.

## Language - CRITICAL REQUIREMENT
You MUST respond in the SAME language the user writes in. This is non-negotiable.
- If user writes in 中文, respond entirely in 中文
- If user writes in English, respond entirely in English
- If user writes in فارسی (Farsi), respond entirely in فارسی
- If user writes in Español, respond entirely in Español
- If user writes in Türkçe, respond entirely in Türkçe
- If user writes in العربية (Arabic), respond entirely in العربية
- Apply this rule to ANY language the user uses
- NEVER switch languages unless the user explicitly requests it
- Be warm, respectful, and acknowledge uncertainty

{essential_context}
"""

HYBRID_PRE_VISIT_SYSTEM = """You are a pre-visit information collection assistant for refugees and political trauma survivors in Canada. Your task is to help patients organize relevant information before seeing their doctor through friendly conversation.

## Privacy Assurance
First, always reassure the user that their information is confidential and stored securely in Canada. It will only be shared with their healthcare provider and never with any government.

## Information to Collect
1. Main concerns - what brings them to seek help?
2. How long has this been going on?
3. What makes things better or worse?
4. Current medications and their effects
5. Previous mental health treatment history
6. Sleep, appetite, and energy levels
7. For political trauma survivors - any specific triggers or safety concerns they want the doctor to know about

## Conversation Style
- Only ask 1-2 questions at a time
- Use natural conversation, not like filling out a form
- Follow up if answers are unclear
- Summarize and confirm at the end

## Important Notes
- You are only collecting information, not making diagnoses or recommendations
- Clearly tell the user this information will be shared with their healthcare provider
- Respect their right to not share certain information
- Be aware that some questions may be triggering - proceed gently

## Using Your Tools
You have access to tools to retrieve user context:
- Use `get_assessment_results` to understand their clinical background
- Use `get_mood_trends` to see recent patterns before the visit
- Use `get_known_triggers` to approach sensitive topics carefully

Use tools when they would help you ask better questions or understand context.

## Language - CRITICAL REQUIREMENT
You MUST respond in the SAME language the user writes in. This is non-negotiable.
- If user writes in 中文, respond entirely in 中文
- If user writes in English, respond entirely in English
- If user writes in فارسی (Farsi), respond entirely in فارسی
- Apply this rule to ANY language the user uses
- NEVER switch languages unless the user explicitly requests it
- Adapt your communication style to be culturally appropriate

{essential_context}
"""


class HybridChatEngine:
    """
    AI chat engine with hybrid context approach.

    Uses on-demand tool retrieval for detailed context while keeping
    essential information (name, language) always available.

    This approach reduces token usage by ~84% compared to full context injection.
    """

    # Maximum number of tool call iterations to prevent infinite loops
    MAX_TOOL_ITERATIONS = 5

    def __init__(self, db: AsyncSession):
        """Initialize hybrid chat engine with database session."""
        self.db = db
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.risk_detector = RiskDetector()

    async def chat(
        self,
        message: str,
        history: List[Dict[str, str]],
        patient_id: str,
        conversation_type: ConversationType = ConversationType.SUPPORTIVE_CHAT,
    ) -> Tuple[str, Optional[RiskResult]]:
        """
        Process a chat message with hybrid context retrieval.

        Args:
            message: User's message
            history: Conversation history [{role, content}, ...]
            patient_id: Patient ID for context retrieval
            conversation_type: Type of conversation (supportive or pre-visit)

        Returns:
            Tuple of (reply text, risk result if detected)
        """
        # Step 1: Risk detection (always run first)
        risk = await self.risk_detector.detect(message)

        # Step 2: Handle high-risk situations with crisis response
        if risk.level == RiskLevel.CRITICAL:
            return CRISIS_RESPONSE_CRITICAL, risk

        if risk.level == RiskLevel.HIGH:
            return CRISIS_RESPONSE_HIGH, risk

        # Step 3: Get patient for essential context
        patient = await self._get_patient(patient_id)
        if not patient:
            return self._fallback_response(), None

        # Step 4: Generate AI response with tools
        if not self.client:
            return self._fallback_response(), (risk if risk.level != RiskLevel.LOW else None)

        try:
            response = await self._generate_response_with_tools(
                message=message,
                history=history,
                patient=patient,
                patient_id=patient_id,
                conversation_type=conversation_type,
            )

            return response, risk if risk.level != RiskLevel.LOW else None

        except Exception as e:
            print(f"Hybrid chat API error: {e}")
            return self._fallback_response(), None

    async def _get_patient(self, patient_id: str) -> Optional[Patient]:
        """Fetch patient profile for essential context."""
        result = await self.db.execute(select(Patient).where(Patient.id == patient_id))
        return result.scalar_one_or_none()

    async def _generate_response_with_tools(
        self,
        message: str,
        history: List[Dict[str, str]],
        patient: Patient,
        patient_id: str,
        conversation_type: ConversationType,
    ) -> str:
        """
        Generate AI response with tool support.

        Implements the agentic loop:
        1. Send message with tools
        2. If Claude uses a tool, execute it and continue
        3. Repeat until Claude returns a final response
        """
        # Build system prompt with essential context only
        essential_context = get_essential_context(patient)

        base_prompt = (
            HYBRID_PRE_VISIT_SYSTEM
            if conversation_type == ConversationType.PRE_VISIT
            else HYBRID_SUPPORTIVE_CHAT_SYSTEM
        )
        system_prompt = base_prompt.format(essential_context=essential_context)

        # Build initial messages
        messages = self._build_messages(history, message)

        # Initialize tool executor
        tool_executor = PatientContextTools(self.db, patient_id)

        # Agentic loop with tool calls
        iterations = 0
        while iterations < self.MAX_TOOL_ITERATIONS:
            iterations += 1

            # Call Claude API with tools
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=800,
                system=system_prompt,
                messages=messages,
                tools=PATIENT_CONTEXT_TOOLS,
                tool_choice={"type": "auto"},  # Let Claude decide when to use tools
            )

            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Process tool calls
                tool_results = await self._process_tool_calls(response.content, tool_executor)

                # Add assistant response and tool results to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

                # Continue the loop for Claude to process results
                continue

            # Claude is done - extract final text response
            return self._extract_text_response(response.content)

        # Max iterations reached - return what we have
        return self._extract_text_response(response.content) if response else self._fallback_response()

    async def _process_tool_calls(self, content: List[Any], tool_executor: PatientContextTools) -> List[Dict[str, Any]]:
        """
        Process tool use blocks and execute tools.

        Args:
            content: Response content blocks from Claude
            tool_executor: Tool executor instance

        Returns:
            List of tool result blocks
        """
        tool_results = []

        for block in content:
            if hasattr(block, "type") and block.type == "tool_use":
                # Execute the tool
                result = await tool_executor.execute_tool(tool_name=block.name, tool_input=block.input)

                # Add result block
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result.content,
                        "is_error": result.is_error,
                    }
                )

        return tool_results

    def _extract_text_response(self, content: List[Any]) -> str:
        """Extract text from response content blocks."""
        for block in content:
            if hasattr(block, "type") and block.type == "text":
                return block.text
            elif hasattr(block, "text"):
                return block.text

        return self._fallback_response()

    def _build_messages(self, history: List[Dict[str, str]], new_message: str) -> List[Dict[str, Any]]:
        """
        Build messages list for API call.

        Args:
            history: Previous messages
            new_message: New user message

        Returns:
            List of messages for API call
        """
        messages = []

        # Keep last 20 messages (10 exchanges)
        for h in history[-20:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

        # Add new message
        messages.append({"role": "user", "content": new_message})

        return messages

    def _fallback_response(self) -> str:
        """Generate a fallback response when AI is unavailable."""
        return (
            "I'm here to listen and support you. "
            "Could you tell me more about how you're feeling?\n\n"
            "我在这里倾听和支持你。你能告诉我更多关于你的感受吗？"
        )

    async def chat_stream(
        self,
        message: str,
        history: List[Dict[str, str]],
        patient_id: str,
        conversation_type: ConversationType = ConversationType.SUPPORTIVE_CHAT,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a chat message with streaming response.

        Yields SSE events for:
        - risk_check: Risk detection result
        - tool_start: When a tool call begins
        - tool_end: When a tool call completes
        - text_delta: Incremental text content
        - message_complete: Final message with full content
        - error: Any errors that occur

        Args:
            message: User's message
            history: Conversation history
            patient_id: Patient ID for context retrieval
            conversation_type: Type of conversation

        Yields:
            Dict with event type and data
        """
        # Step 1: Risk detection
        risk = await self.risk_detector.detect(message)

        yield {
            "event": "risk_check",
            "data": {
                "level": risk.level.value,
                "risk_type": risk.risk_type.value if risk.risk_type else None,
            },
        }

        # Step 2: Handle high-risk situations
        if risk.level == RiskLevel.CRITICAL:
            yield {"event": "text_delta", "data": {"text": CRISIS_RESPONSE_CRITICAL}}
            yield {
                "event": "message_complete",
                "data": {"content": CRISIS_RESPONSE_CRITICAL, "risk": risk.level.value},
            }
            return

        if risk.level == RiskLevel.HIGH:
            yield {"event": "text_delta", "data": {"text": CRISIS_RESPONSE_HIGH}}
            yield {
                "event": "message_complete",
                "data": {"content": CRISIS_RESPONSE_HIGH, "risk": risk.level.value},
            }
            return

        # Step 3: Get patient for essential context
        patient = await self._get_patient(patient_id)
        if not patient:
            fallback = self._fallback_response()
            yield {"event": "text_delta", "data": {"text": fallback}}
            yield {
                "event": "message_complete",
                "data": {"content": fallback, "risk": None},
            }
            return

        # Step 4: Generate streaming response with tools
        if not self.client:
            fallback = self._fallback_response()
            yield {"event": "text_delta", "data": {"text": fallback}}
            yield {
                "event": "message_complete",
                "data": {"content": fallback, "risk": None},
            }
            return

        try:
            async for event in self._generate_streaming_response_with_tools(
                message=message,
                history=history,
                patient=patient,
                patient_id=patient_id,
                conversation_type=conversation_type,
            ):
                yield event

        except Exception as e:
            print(f"Streaming chat error: {e}")
            yield {"event": "error", "data": {"message": str(e)}}
            fallback = self._fallback_response()
            yield {
                "event": "message_complete",
                "data": {"content": fallback, "risk": None},
            }

    async def _generate_streaming_response_with_tools(
        self,
        message: str,
        history: List[Dict[str, str]],
        patient: Patient,
        patient_id: str,
        conversation_type: ConversationType,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate streaming AI response with tool support.

        Implements the agentic loop with streaming:
        1. Stream message with tools
        2. If Claude uses a tool, yield tool events and execute
        3. Repeat until Claude returns a final response
        """
        # Build system prompt with essential context only
        essential_context = get_essential_context(patient)

        base_prompt = (
            HYBRID_PRE_VISIT_SYSTEM
            if conversation_type == ConversationType.PRE_VISIT
            else HYBRID_SUPPORTIVE_CHAT_SYSTEM
        )
        system_prompt = base_prompt.format(essential_context=essential_context)

        # Build initial messages
        messages = self._build_messages(history, message)

        # Initialize tool executor
        tool_executor = PatientContextTools(self.db, patient_id)

        # Agentic loop with tool calls
        iterations = 0
        full_response = ""

        while iterations < self.MAX_TOOL_ITERATIONS:
            iterations += 1

            # Collect content blocks during streaming
            current_content_blocks = []
            current_tool_use = None
            current_tool_input = ""

            # Stream the response
            async with self.client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=800,
                system=system_prompt,
                messages=messages,
                tools=PATIENT_CONTEXT_TOOLS,
                tool_choice={"type": "auto"},
            ) as stream:
                async for event in stream:
                    # Handle different event types
                    if event.type == "content_block_start":
                        block = event.content_block
                        if block.type == "tool_use":
                            current_tool_use = {
                                "id": block.id,
                                "name": block.name,
                                "input": {},
                            }
                            current_tool_input = ""
                            yield {
                                "event": "tool_start",
                                "data": {"tool_id": block.id, "tool_name": block.name},
                            }

                    elif event.type == "content_block_delta":
                        delta = event.delta
                        if delta.type == "text_delta":
                            yield {"event": "text_delta", "data": {"text": delta.text}}
                            full_response += delta.text

                        elif delta.type == "input_json_delta":
                            current_tool_input += delta.partial_json

                    elif event.type == "content_block_stop":
                        if current_tool_use:
                            # Parse the accumulated JSON input
                            try:
                                current_tool_use["input"] = json.loads(current_tool_input) if current_tool_input else {}
                            except json.JSONDecodeError:
                                current_tool_use["input"] = {}

                            current_content_blocks.append(
                                {
                                    "type": "tool_use",
                                    "id": current_tool_use["id"],
                                    "name": current_tool_use["name"],
                                    "input": current_tool_use["input"],
                                }
                            )
                            current_tool_use = None
                            current_tool_input = ""

                # Get the final message
                final_message = await stream.get_final_message()

            # Check if we need to handle tool use
            if final_message.stop_reason == "tool_use":
                # Execute tools and yield results
                tool_results = []

                for block in current_content_blocks:
                    if block["type"] == "tool_use":
                        # Execute the tool
                        result = await tool_executor.execute_tool(tool_name=block["name"], tool_input=block["input"])

                        yield {
                            "event": "tool_end",
                            "data": {
                                "tool_id": block["id"],
                                "tool_name": block["name"],
                                "result_preview": (
                                    result.content[:200] + "..." if len(result.content) > 200 else result.content
                                ),
                            },
                        }

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block["id"],
                                "content": result.content,
                                "is_error": result.is_error,
                            }
                        )

                # Add assistant response and tool results to messages
                messages.append({"role": "assistant", "content": final_message.content})
                messages.append({"role": "user", "content": tool_results})

                # Reset for next iteration
                full_response = ""
                continue

            # No more tool use - we're done
            break

        # Yield completion event
        yield {
            "event": "message_complete",
            "data": {
                "content": full_response or self._fallback_response(),
                "risk": None,
            },
        }

    async def generate_summary(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a summary of the conversation.

        Args:
            messages: List of conversation messages

        Returns:
            Summary text
        """
        if not self.client or not messages:
            return ""

        try:
            # Build conversation text
            conversation_text = "\n".join(
                [f"{'User' if m.get('role') == 'user' else 'Assistant'}: {m.get('content', '')}" for m in messages]
            )

            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": f"Summarize this conversation in 2-3 sentences, focusing on the main topics and emotional themes. Write the summary in the same language as the conversation:\n\n{conversation_text}",
                    }
                ],
            )

            return response.content[0].text

        except Exception as e:
            print(f"Summary generation error: {e}")
            return ""
