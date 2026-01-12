"""Doctor AI chat engine for patient-specific consultations.

Provides AI-assisted conversations for doctors discussing specific patients,
with full access to patient context including medical records, check-ins,
assessments, and conversation history.
"""

from typing import List, Dict, Optional
from anthropic import AsyncAnthropic

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.doctor_conversation import DoctorConversation
from app.services.ai.patient_context_aggregator import (
    PatientContextAggregator,
    PatientFullContext,
)


# System prompt for doctor AI assistant
DOCTOR_AI_SYSTEM_PROMPT = """You are an AI clinical assistant for mental health professionals. You help doctors analyze patient data, identify patterns, and consider treatment approaches.

## Your Role
- You assist licensed mental health professionals (psychiatrists, psychologists, counselors)
- You have access to the patient's comprehensive data including: medical records, daily check-ins, clinical assessments, AI conversation history, and risk events
- You provide data-driven insights while respecting clinical judgment

## What You Can Do
- Analyze trends in patient mood, sleep, and other tracked metrics
- Summarize patient history and recent changes
- Identify potential risk factors or concerning patterns
- Suggest evidence-based questions or topics to explore
- Help interpret standardized assessment results (PHQ-9, GAD-7, PCL-5, etc.)
- Discuss treatment considerations based on clinical guidelines
- Highlight information that may need follow-up

## What You Cannot Do
- Make definitive diagnoses (you can discuss differential considerations)
- Prescribe medications (you can discuss medication classes and considerations)
- Replace clinical judgment
- Make decisions about patient care
- Access information outside what is provided in the patient context

## Special Considerations
- Many patients in this system are political trauma survivors and refugees
- Be aware of culturally-informed care and politically-informed trauma considerations
- Persecution-related trauma may present differently than other trauma types
- Hypervigilance and distrust may be adaptive responses rather than symptoms

## Communication Style
- Be concise and clinically focused
- Use appropriate clinical terminology
- Present information objectively
- Clearly distinguish between data/facts and interpretations
- Always defer final judgment to the treating clinician

## Language - CRITICAL REQUIREMENT
You MUST respond in the SAME language the doctor writes in. This is non-negotiable.
- If the doctor writes in 中文, respond entirely in 中文
- If the doctor writes in English, respond entirely in English
- If the doctor writes in فارسی (Farsi), respond entirely in فارسی
- Apply this rule to ANY language the doctor uses
- NEVER switch languages unless the doctor explicitly requests it

## Current Patient Context
{patient_context}
"""


class DoctorChatEngine:
    """
    AI chat engine for doctor-patient consultations.

    Provides doctors with an AI assistant that has full context about
    a specific patient, enabling data-driven clinical discussions.
    """

    def __init__(self, db: AsyncSession):
        """Initialize chat engine with database session and AI client."""
        self.db = db
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.context_aggregator = PatientContextAggregator(db)

    async def chat(
        self,
        doctor_id: str,
        patient_id: str,
        message: str,
        conversation_id: Optional[str] = None,
    ) -> Dict:
        """
        Process a doctor's message about a specific patient.

        Args:
            doctor_id: The doctor's ID
            patient_id: The patient's ID
            message: The doctor's message/question
            conversation_id: Optional existing conversation ID to continue

        Returns:
            Dict with response, conversation_id, and metadata
        """
        # Verify doctor-patient relationship
        patient = await self._verify_relationship(doctor_id, patient_id)
        if not patient:
            raise PermissionError("You don't have access to this patient")

        # Get or create conversation
        conversation = await self._get_or_create_conversation(
            doctor_id, patient_id, conversation_id
        )

        # Get patient context
        patient_context = await self.context_aggregator.get_full_context(
            patient_id, days_back=30
        )

        # Generate AI response
        response_text = await self._generate_response(
            message=message,
            conversation=conversation,
            patient_context=patient_context,
        )

        # Save the exchange to conversation
        conversation.add_message("user", message)
        conversation.add_message("assistant", response_text)
        await self.db.commit()

        return {
            "response": response_text,
            "conversation_id": conversation.id,
            "patient_name": patient.full_name,
        }

    async def _verify_relationship(
        self, doctor_id: str, patient_id: str
    ) -> Optional[Patient]:
        """
        Verify that the doctor has a relationship with the patient.

        Args:
            doctor_id: The doctor's ID
            patient_id: The patient's ID

        Returns:
            Patient if relationship exists, None otherwise
        """
        result = await self.db.execute(
            select(Patient).where(
                Patient.id == patient_id,
                Patient.primary_doctor_id == doctor_id
            )
        )
        return result.scalar_one_or_none()

    async def _get_or_create_conversation(
        self,
        doctor_id: str,
        patient_id: str,
        conversation_id: Optional[str] = None,
    ) -> DoctorConversation:
        """
        Get existing conversation or create a new one.

        Args:
            doctor_id: The doctor's ID
            patient_id: The patient's ID
            conversation_id: Optional existing conversation ID

        Returns:
            DoctorConversation instance
        """
        if conversation_id:
            # Try to get existing conversation
            result = await self.db.execute(
                select(DoctorConversation).where(
                    DoctorConversation.id == conversation_id,
                    DoctorConversation.doctor_id == doctor_id,
                    DoctorConversation.patient_id == patient_id,
                )
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                return conversation

        # Create new conversation
        conversation = DoctorConversation(
            doctor_id=doctor_id,
            patient_id=patient_id,
        )
        self.db.add(conversation)
        await self.db.flush()  # Get the ID

        return conversation

    async def _generate_response(
        self,
        message: str,
        conversation: DoctorConversation,
        patient_context: PatientFullContext,
    ) -> str:
        """
        Generate AI response using Claude.

        Args:
            message: Doctor's message
            conversation: Current conversation with history
            patient_context: Aggregated patient context

        Returns:
            AI response text
        """
        if not self.client:
            return self._fallback_response()

        try:
            # Build system prompt with patient context
            context_text = self.context_aggregator.build_context_prompt(patient_context)
            system_prompt = DOCTOR_AI_SYSTEM_PROMPT.format(patient_context=context_text)

            # Build messages from history
            messages = self._build_messages(conversation.messages, message)

            # Call Claude API
            response = await self.client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1500,
                system=system_prompt,
                messages=messages,
            )

            return response.content[0].text

        except Exception as e:
            print(f"Doctor chat API error: {e}")
            return self._fallback_response()

    def _build_messages(
        self,
        history: List[Dict[str, str]],
        new_message: str,
    ) -> List[Dict[str, str]]:
        """
        Build messages list for API call.

        Args:
            history: Previous messages from conversation
            new_message: New doctor message

        Returns:
            List of messages for API call
        """
        messages = []

        # Include conversation history (last 30 messages = 15 exchanges)
        for msg in history[-30:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
            })

        # Add new message
        messages.append({
            "role": "user",
            "content": new_message,
        })

        return messages

    def _fallback_response(self) -> str:
        """Generate fallback response when AI is unavailable."""
        return (
            "AI 服务暂时不可用。请稍后重试，或联系技术支持。\n\n"
            "AI service is temporarily unavailable. Please try again later or contact support."
        )

    async def get_conversations(
        self,
        doctor_id: str,
        patient_id: str,
        limit: int = 10,
    ) -> List[DoctorConversation]:
        """
        Get recent conversations for a doctor-patient pair.

        Args:
            doctor_id: The doctor's ID
            patient_id: The patient's ID
            limit: Maximum number of conversations to return

        Returns:
            List of DoctorConversation instances
        """
        from sqlalchemy import desc

        result = await self.db.execute(
            select(DoctorConversation)
            .where(
                DoctorConversation.doctor_id == doctor_id,
                DoctorConversation.patient_id == patient_id,
            )
            .order_by(desc(DoctorConversation.updated_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def generate_conversation_summary(
        self,
        conversation: DoctorConversation,
    ) -> str:
        """
        Generate a summary of a doctor-patient AI conversation.

        Args:
            conversation: The conversation to summarize

        Returns:
            Summary text
        """
        if not self.client or not conversation.messages:
            return ""

        try:
            # Build conversation text
            conv_text = "\n".join([
                f"{'医生' if m.get('role') == 'user' else 'AI'}: {m.get('content', '')}"
                for m in conversation.messages
            ])

            response = await self.client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": f"请用2-3句话总结以下医生与AI助手的对话要点：\n\n{conv_text}"
                }]
            )

            summary = response.content[0].text
            conversation.summary = summary
            await self.db.commit()

            return summary

        except Exception as e:
            print(f"Summary generation error: {e}")
            return ""
