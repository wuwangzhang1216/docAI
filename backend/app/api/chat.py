"""Chat API endpoints for AI conversations.

Uses the Hybrid Chat Engine with on-demand context retrieval via tools.
This approach reduces token usage by ~84% while maintaining accuracy.
Reference: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
"""

import json
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from app.database import get_db
from app.models.conversation import Conversation, ConversationType
from app.models.patient import Patient
from app.models.risk_event import RiskEvent, RiskLevel
from app.schemas.chat import ChatRequest, ChatResponse, ConversationListItem, ConversationResponse, MessageItem
from app.services.ai.hybrid_chat_engine import HybridChatEngine
from app.utils.deps import get_current_patient

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_engine(db: AsyncSession) -> HybridChatEngine:
    """Get chat engine instance with database session."""
    return HybridChatEngine(db)


@router.post("", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to the AI chat assistant.

    Creates a new conversation if conversation_id is not provided.
    Performs risk detection and creates risk events if needed.
    """
    # Get or create conversation
    if request.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == request.conversation_id,
                Conversation.patient_id == patient.id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    else:
        # Create new conversation
        conversation = Conversation(
            patient_id=patient.id,
            conv_type=ConversationType.SUPPORTIVE_CHAT,
            messages=[],
        )
        db.add(conversation)
        await db.flush()

    # Get conversation history
    history = conversation.messages or []

    # Process message through hybrid chat engine
    chat_engine = get_chat_engine(db)
    reply, risk = await chat_engine.chat(
        message=request.message,
        history=history,
        patient_id=str(patient.id),
        conversation_type=conversation.conv_type,
    )

    # Update conversation messages
    now = datetime.utcnow().isoformat()
    new_messages = history + [
        {"role": "user", "content": request.message, "timestamp": now},
        {
            "role": "assistant",
            "content": reply,
            "timestamp": now,
            "risk_level": risk.level.value if risk else None,
        },
    ]
    conversation.messages = new_messages
    conversation.updated_at = datetime.utcnow()

    # Create risk event if medium or higher risk detected
    risk_alert = False
    risk_event = None
    if risk and risk.level in [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]:
        risk_event = RiskEvent(
            patient_id=patient.id,
            conversation_id=conversation.id,
            risk_level=risk.level,
            risk_type=risk.risk_type,
            trigger_text=risk.trigger_text or request.message[:200],
            ai_confidence=risk.confidence,
        )
        db.add(risk_event)
        risk_alert = risk.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

    await db.commit()

    # Send risk alert email to doctor if high/critical risk detected
    if risk_event and risk.level in [RiskLevel.HIGH, RiskLevel.CRITICAL] and patient.primary_doctor_id:
        try:
            from app.models.doctor import Doctor
            from app.services.email.email_senders import send_risk_alert_email

            doctor_result = await db.execute(select(Doctor).where(Doctor.id == patient.primary_doctor_id))
            doctor = doctor_result.scalar_one_or_none()

            if doctor:
                await db.refresh(risk_event)  # Ensure we have the ID
                await send_risk_alert_email(
                    db=db,
                    risk_event=risk_event,
                    patient=patient,
                    doctor=doctor,
                )
        except Exception as e:
            # Log but don't fail the request if email fails
            import logging

            logging.error(f"Failed to send risk alert email: {e}")

    return ChatResponse(reply=reply, conversation_id=conversation.id, risk_alert=risk_alert)


@router.post("/stream")
async def send_message_stream(
    request: ChatRequest,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to the AI chat assistant with streaming response.

    Returns Server-Sent Events (SSE) with the following event types:
    - risk_check: Risk detection result
    - tool_start: When a tool call begins (shows tool name)
    - tool_end: When a tool call completes (shows result preview)
    - text_delta: Incremental text content
    - message_complete: Final message with full content
    - error: Any errors that occur

    The conversation is saved after streaming completes.
    """
    # Get or create conversation
    if request.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == request.conversation_id,
                Conversation.patient_id == patient.id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    else:
        # Create new conversation
        conversation = Conversation(
            patient_id=patient.id,
            conv_type=ConversationType.SUPPORTIVE_CHAT,
            messages=[],
        )
        db.add(conversation)
        await db.flush()

    # Get conversation history
    history = conversation.messages or []
    chat_engine = get_chat_engine(db)

    async def generate_sse():
        """Generate Server-Sent Events from chat stream."""
        full_response = ""
        risk_level = None
        risk_type = None

        try:
            async for event in chat_engine.chat_stream(
                message=request.message,
                history=history,
                patient_id=str(patient.id),
                conversation_type=conversation.conv_type,
            ):
                event_type = event.get("event", "unknown")
                event_data = event.get("data", {})

                # Track response content
                if event_type == "text_delta":
                    full_response += event_data.get("text", "")
                elif event_type == "risk_check":
                    risk_level = event_data.get("level")
                    risk_type = event_data.get("risk_type")
                elif event_type == "message_complete":
                    full_response = event_data.get("content", full_response)
                    if event_data.get("risk"):
                        risk_level = event_data.get("risk")

                # Send SSE event
                yield f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"

            # Save conversation after streaming completes
            now = datetime.utcnow().isoformat()
            new_messages = history + [
                {"role": "user", "content": request.message, "timestamp": now},
                {
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": now,
                    "risk_level": risk_level,
                },
            ]
            conversation.messages = new_messages
            conversation.updated_at = datetime.utcnow()

            # Create risk event if needed
            if risk_level in ["MEDIUM", "HIGH", "CRITICAL"]:
                risk_event = RiskEvent(
                    patient_id=patient.id,
                    conversation_id=conversation.id,
                    risk_level=RiskLevel(risk_level),
                    risk_type=risk_type,
                    trigger_text=request.message[:200],
                    ai_confidence=0.8,
                )
                db.add(risk_event)

                # Send risk alert email for high/critical
                if risk_level in ["HIGH", "CRITICAL"] and patient.primary_doctor_id:
                    try:
                        from app.models.doctor import Doctor
                        from app.services.email.email_senders import send_risk_alert_email

                        doctor_result = await db.execute(select(Doctor).where(Doctor.id == patient.primary_doctor_id))
                        doctor = doctor_result.scalar_one_or_none()
                        if doctor:
                            await db.refresh(risk_event)
                            await send_risk_alert_email(
                                db=db,
                                risk_event=risk_event,
                                patient=patient,
                                doctor=doctor,
                            )
                    except Exception as e:
                        import logging

                        logging.error(f"Failed to send risk alert email: {e}")

            await db.commit()

            # Send final metadata event with conversation ID
            yield f"event: metadata\ndata: {json.dumps({'conversation_id': str(conversation.id), 'risk_alert': risk_level in ['HIGH', 'CRITICAL']})}\n\n"

        except Exception as e:
            import logging

            logging.error(f"Streaming error: {e}")
            yield f"event: error\ndata: {json.dumps({'message': 'An error occurred during streaming'})}\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/conversations", response_model=List[ConversationListItem])
async def list_conversations(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """List conversations for the current patient with pagination.

    Uses deferred loading to avoid fetching the full messages_json blob
    for every conversation — only lightweight metadata columns are loaded.
    """
    # Query only the columns we need; defer the heavy messages_json
    result = await db.execute(
        select(Conversation)
        .options(defer(Conversation.messages_json))
        .where(Conversation.patient_id == patient.id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    conversations = result.scalars().all()

    # For the listing, we need message_count and last_message_preview.
    # We fetch messages_json only for the returned page (much smaller set).
    conv_ids = [c.id for c in conversations]
    msg_data = {}
    if conv_ids:
        # Use a lightweight query to get just the messages_json for the page
        msg_result = await db.execute(
            select(Conversation.id, Conversation.messages_json).where(Conversation.id.in_(conv_ids))
        )
        for cid, mjson in msg_result.fetchall():
            messages = json.loads(mjson) if mjson else []
            last_msg = messages[-1] if messages else None
            preview = None
            if last_msg:
                content = last_msg.get("content", "")
                preview = content[:50] + "..." if len(content) > 50 else content
            msg_data[cid] = (len(messages), preview)

    items = []
    for conv in conversations:
        message_count, last_preview = msg_data.get(conv.id, (0, None))
        items.append(
            ConversationListItem(
                id=conv.id,
                conv_type=conv.conv_type,
                message_count=message_count,
                last_message_preview=last_preview,
                is_active=conv.is_active,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
        )

    return items


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific conversation with full message history."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.patient_id == patient.id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Convert messages to MessageItem format
    messages = []
    for msg in conversation.messages or []:
        messages.append(
            MessageItem(
                role=msg.get("role", "user"),
                content=msg.get("content", ""),
                timestamp=datetime.fromisoformat(msg.get("timestamp", datetime.utcnow().isoformat())),
                risk_level=msg.get("risk_level"),
            )
        )

    return ConversationResponse(
        id=conversation.id,
        patient_id=conversation.patient_id,
        conv_type=conversation.conv_type,
        messages=messages,
        summary=conversation.summary,
        is_active=conversation.is_active,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.post("/conversations/{conversation_id}/end")
async def end_conversation(
    conversation_id: UUID,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    End a conversation and generate a summary.

    Marks the conversation as inactive and generates an AI summary.
    """
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.patient_id == patient.id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Generate summary
    chat_engine = get_chat_engine(db)
    summary = await chat_engine.generate_summary(conversation.messages or [])

    # Update conversation
    conversation.is_active = False
    conversation.summary = summary

    await db.commit()

    return {
        "status": "ended",
        "conversation_id": str(conversation_id),
        "summary": summary,
    }


@router.post("/pre-visit", response_model=ChatResponse)
async def pre_visit_chat(
    request: ChatRequest,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to the pre-visit information gathering assistant.

    Similar to regular chat but uses the pre-visit system prompt.
    """
    # Get or create pre-visit conversation
    if request.conversation_id:
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == request.conversation_id,
                Conversation.patient_id == patient.id,
                Conversation.conv_type == ConversationType.PRE_VISIT,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pre-visit conversation not found",
            )
    else:
        conversation = Conversation(patient_id=patient.id, conv_type=ConversationType.PRE_VISIT, messages=[])
        db.add(conversation)
        await db.flush()

    # Get conversation history
    history = conversation.messages or []

    # Process message through hybrid chat engine
    chat_engine = get_chat_engine(db)
    reply, risk = await chat_engine.chat(
        message=request.message,
        history=history,
        patient_id=str(patient.id),
        conversation_type=ConversationType.PRE_VISIT,
    )

    # Update conversation
    now = datetime.utcnow().isoformat()
    conversation.messages = history + [
        {"role": "user", "content": request.message, "timestamp": now},
        {"role": "assistant", "content": reply, "timestamp": now},
    ]
    conversation.updated_at = datetime.utcnow()

    await db.commit()

    return ChatResponse(reply=reply, conversation_id=conversation.id, risk_alert=False)
