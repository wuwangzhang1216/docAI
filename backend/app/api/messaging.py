"""
REST API endpoints for doctor-patient messaging.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User, UserType
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.messaging import (
    DoctorPatientThread,
    DirectMessage,
    MessageAttachment,
    MessageType,
)
from app.schemas.messaging import (
    MessageCreate,
    MessageResponse,
    ThreadSummary,
    ThreadDetail,
    UnreadCountResponse,
    ThreadUnreadCount,
    AttachmentResponse,
    AttachmentUploadResponse,
)
from app.schemas.common import PaginatedResponse
from app.utils.deps import (
    get_db,
    get_current_active_user,
    get_current_patient,
    get_current_doctor,
)
from app.services.storage import storage_service
from app.services.websocket_manager import ws_manager


router = APIRouter(prefix="/messaging", tags=["messaging"])


# ==================== Helper Functions ====================

async def get_thread_with_validation(
    thread_id: str,
    user: User,
    db: AsyncSession,
    require_send_permission: bool = False
) -> tuple[DoctorPatientThread, str, str]:
    """
    Get a thread and validate user access.
    Returns (thread, user_role, other_party_user_id).
    """
    # Get the thread
    result = await db.execute(
        select(DoctorPatientThread).where(DoctorPatientThread.id == thread_id)
    )
    thread = result.scalar_one_or_none()

    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    # Determine user's role in the thread
    user_role = None
    other_party_user_id = None

    if user.user_type == UserType.PATIENT:
        # Get patient profile
        patient_result = await db.execute(
            select(Patient).where(Patient.user_id == user.id)
        )
        patient = patient_result.scalar_one_or_none()

        if patient and thread.patient_id == patient.id:
            user_role = "PATIENT"
            # Get doctor's user_id
            doctor_result = await db.execute(
                select(Doctor).where(Doctor.id == thread.doctor_id)
            )
            doctor = doctor_result.scalar_one_or_none()
            if doctor:
                other_party_user_id = doctor.user_id

    elif user.user_type == UserType.DOCTOR:
        # Get doctor profile
        doctor_result = await db.execute(
            select(Doctor).where(Doctor.user_id == user.id)
        )
        doctor = doctor_result.scalar_one_or_none()

        if doctor and thread.doctor_id == doctor.id:
            user_role = "DOCTOR"
            # Get patient's user_id
            patient_result = await db.execute(
                select(Patient).where(Patient.id == thread.patient_id)
            )
            patient = patient_result.scalar_one_or_none()
            if patient:
                other_party_user_id = patient.user_id

    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant in this thread"
        )

    # Check send permission if required
    if require_send_permission:
        can_send = await check_can_send_message(thread, db)
        if not can_send:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot send messages in this thread. The connection may have been terminated."
            )

    return thread, user_role, other_party_user_id


async def check_can_send_message(thread: DoctorPatientThread, db: AsyncSession) -> bool:
    """Check if messages can be sent in this thread (connection still active)."""
    result = await db.execute(
        select(Patient).where(Patient.id == thread.patient_id)
    )
    patient = result.scalar_one_or_none()

    if not patient:
        return False

    # Check if the patient is still connected to this doctor
    return patient.primary_doctor_id == thread.doctor_id


async def build_message_response(
    message: DirectMessage,
    thread: DoctorPatientThread,
    db: AsyncSession
) -> MessageResponse:
    """Build a MessageResponse from a DirectMessage."""
    # Get sender name
    if message.sender_type == "DOCTOR":
        result = await db.execute(
            select(Doctor).where(Doctor.id == message.sender_id)
        )
        sender = result.scalar_one_or_none()
        sender_name = f"{sender.first_name} {sender.last_name}" if sender else "Unknown"
    else:
        result = await db.execute(
            select(Patient).where(Patient.id == message.sender_id)
        )
        sender = result.scalar_one_or_none()
        sender_name = f"{sender.first_name} {sender.last_name}" if sender else "Unknown"

    # Get attachments
    attachments = []
    for att in message.attachments:
        attachments.append(AttachmentResponse(
            id=att.id,
            file_name=att.file_name,
            file_type=att.file_type,
            file_size=att.file_size,
            url=storage_service.get_presigned_url(att.s3_key),
            thumbnail_url=storage_service.get_presigned_url(att.thumbnail_s3_key) if att.thumbnail_s3_key else None
        ))

    return MessageResponse(
        id=message.id,
        thread_id=message.thread_id,
        sender_type=message.sender_type,
        sender_id=message.sender_id,
        sender_name=sender_name,
        content=message.content,
        message_type=message.message_type,
        is_read=message.is_read,
        read_at=message.read_at,
        created_at=message.created_at,
        attachments=attachments
    )


# ==================== Thread Endpoints ====================

@router.get("/threads", response_model=PaginatedResponse[ThreadSummary])
async def get_threads(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="Search by other party's name"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all message threads for the current user with pagination and search.
    Works for both patients and doctors.
    """
    threads = []
    total = 0

    if current_user.user_type == UserType.PATIENT:
        # Get patient profile
        patient_result = await db.execute(
            select(Patient).where(Patient.user_id == current_user.id)
        )
        patient = patient_result.scalar_one_or_none()
        if not patient:
            return PaginatedResponse(items=[], total=0, limit=limit, offset=offset, has_more=False)

        # Build base query
        base_query = (
            select(DoctorPatientThread, Doctor)
            .join(Doctor, DoctorPatientThread.doctor_id == Doctor.id)
            .where(DoctorPatientThread.patient_id == patient.id)
        )

        # Apply search filter if provided
        if search:
            search_pattern = f"%{search}%"
            base_query = base_query.where(
                or_(
                    Doctor.first_name.ilike(search_pattern),
                    Doctor.last_name.ilike(search_pattern),
                    (Doctor.first_name + ' ' + Doctor.last_name).ilike(search_pattern)
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Get paginated threads
        result = await db.execute(
            base_query
            .order_by(desc(DoctorPatientThread.last_message_at))
            .offset(offset)
            .limit(limit)
        )
        rows = result.fetchall()

        for thread, doctor in rows:
            # Get last message
            msg_result = await db.execute(
                select(DirectMessage)
                .where(DirectMessage.thread_id == thread.id)
                .order_by(desc(DirectMessage.created_at))
                .limit(1)
            )
            last_msg = msg_result.scalar_one_or_none()

            # Check if connection is still active
            can_send = patient.primary_doctor_id == doctor.id

            threads.append(ThreadSummary(
                id=thread.id,
                other_party_id=doctor.id,
                other_party_name=f"{doctor.first_name} {doctor.last_name}",
                other_party_type="DOCTOR",
                last_message_preview=last_msg.content[:100] if last_msg and last_msg.content else (
                    f"[{last_msg.message_type.value}]" if last_msg else None
                ),
                last_message_at=thread.last_message_at,
                last_message_type=last_msg.message_type if last_msg else None,
                unread_count=thread.patient_unread_count,
                can_send_message=can_send,
                created_at=thread.created_at
            ))

    elif current_user.user_type == UserType.DOCTOR:
        # Get doctor profile
        doctor_result = await db.execute(
            select(Doctor).where(Doctor.user_id == current_user.id)
        )
        doctor = doctor_result.scalar_one_or_none()
        if not doctor:
            return PaginatedResponse(items=[], total=0, limit=limit, offset=offset, has_more=False)

        # Build base query
        base_query = (
            select(DoctorPatientThread, Patient)
            .join(Patient, DoctorPatientThread.patient_id == Patient.id)
            .where(DoctorPatientThread.doctor_id == doctor.id)
        )

        # Apply search filter if provided
        if search:
            search_pattern = f"%{search}%"
            base_query = base_query.where(
                or_(
                    Patient.first_name.ilike(search_pattern),
                    Patient.last_name.ilike(search_pattern),
                    (Patient.first_name + ' ' + Patient.last_name).ilike(search_pattern)
                )
            )

        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Get paginated threads
        result = await db.execute(
            base_query
            .order_by(desc(DoctorPatientThread.last_message_at))
            .offset(offset)
            .limit(limit)
        )
        rows = result.fetchall()

        for thread, patient in rows:
            # Get last message
            msg_result = await db.execute(
                select(DirectMessage)
                .where(DirectMessage.thread_id == thread.id)
                .order_by(desc(DirectMessage.created_at))
                .limit(1)
            )
            last_msg = msg_result.scalar_one_or_none()

            # Check if connection is still active
            can_send = patient.primary_doctor_id == doctor.id

            threads.append(ThreadSummary(
                id=thread.id,
                other_party_id=patient.id,
                other_party_name=f"{patient.first_name} {patient.last_name}",
                other_party_type="PATIENT",
                last_message_preview=last_msg.content[:100] if last_msg and last_msg.content else (
                    f"[{last_msg.message_type.value}]" if last_msg else None
                ),
                last_message_at=thread.last_message_at,
                last_message_type=last_msg.message_type if last_msg else None,
                unread_count=thread.doctor_unread_count,
                can_send_message=can_send,
                created_at=thread.created_at
            ))

    return PaginatedResponse(
        items=threads,
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + len(threads) < total
    )


@router.get("/threads/{thread_id}", response_model=ThreadDetail)
async def get_thread(
    thread_id: str,
    limit: int = Query(50, ge=1, le=200),
    before: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific thread with messages.
    Supports pagination with 'before' timestamp.
    """
    thread, user_role, _ = await get_thread_with_validation(thread_id, current_user, db)

    # Get other party info
    if user_role == "PATIENT":
        result = await db.execute(
            select(Doctor).where(Doctor.id == thread.doctor_id)
        )
        other = result.scalar_one_or_none()
        other_party_id = other.id if other else ""
        other_party_name = f"{other.first_name} {other.last_name}" if other else "Unknown"
        other_party_type = "DOCTOR"
    else:
        result = await db.execute(
            select(Patient).where(Patient.id == thread.patient_id)
        )
        other = result.scalar_one_or_none()
        other_party_id = other.id if other else ""
        other_party_name = f"{other.first_name} {other.last_name}" if other else "Unknown"
        other_party_type = "PATIENT"

    # Get messages with attachments eagerly loaded
    query = select(DirectMessage).options(
        selectinload(DirectMessage.attachments)
    ).where(DirectMessage.thread_id == thread_id)
    if before:
        query = query.where(DirectMessage.created_at < before)
    query = query.order_by(desc(DirectMessage.created_at)).limit(limit + 1)

    msg_result = await db.execute(query)
    messages_raw = msg_result.scalars().all()

    # Check if there are more messages
    has_more = len(messages_raw) > limit
    if has_more:
        messages_raw = messages_raw[:limit]

    # Build response (reverse to chronological order)
    messages = []
    for msg in reversed(messages_raw):
        messages.append(await build_message_response(msg, thread, db))

    # Check if can send message
    can_send = await check_can_send_message(thread, db)

    return ThreadDetail(
        id=thread.id,
        other_party_id=other_party_id,
        other_party_name=other_party_name,
        other_party_type=other_party_type,
        can_send_message=can_send,
        messages=messages,
        has_more=has_more,
        created_at=thread.created_at
    )


@router.post("/threads/{thread_id}/messages", response_model=MessageResponse)
async def send_message(
    thread_id: str,
    request: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message in a thread.
    Requires active connection between doctor and patient.
    """
    thread, user_role, other_party_user_id = await get_thread_with_validation(
        thread_id, current_user, db, require_send_permission=True
    )

    # Validate message content
    if request.message_type == MessageType.TEXT and not request.content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text messages must have content"
        )

    # Get sender ID
    if user_role == "PATIENT":
        result = await db.execute(
            select(Patient).where(Patient.user_id == current_user.id)
        )
        sender = result.scalar_one_or_none()
        sender_id = sender.id
    else:
        result = await db.execute(
            select(Doctor).where(Doctor.user_id == current_user.id)
        )
        sender = result.scalar_one_or_none()
        sender_id = sender.id

    # Create the message
    message = DirectMessage(
        thread_id=thread_id,
        sender_type=user_role,
        sender_id=sender_id,
        content=request.content,
        message_type=request.message_type
    )
    db.add(message)
    await db.flush()

    # Handle attachments
    if request.attachment_ids:
        for att_id in request.attachment_ids:
            # Get the attachment (should already exist from upload)
            att_result = await db.execute(
                select(MessageAttachment).where(MessageAttachment.id == att_id)
            )
            attachment = att_result.scalar_one_or_none()
            if attachment and attachment.message_id is None:
                attachment.message_id = message.id

    # Update thread
    thread.last_message_at = datetime.utcnow()
    if user_role == "PATIENT":
        thread.doctor_unread_count += 1
    else:
        thread.patient_unread_count += 1

    await db.commit()

    # Re-query message with attachments eagerly loaded to avoid lazy loading issues
    msg_result = await db.execute(
        select(DirectMessage)
        .options(selectinload(DirectMessage.attachments))
        .where(DirectMessage.id == message.id)
    )
    message = msg_result.scalar_one()

    # Build response
    response = await build_message_response(message, thread, db)

    # Send WebSocket notification
    if other_party_user_id:
        await ws_manager.notify_new_message(
            thread_id=thread_id,
            message_data=response.model_dump(),
            recipient_user_id=other_party_user_id
        )

    return response


@router.post("/threads/{thread_id}/read")
async def mark_thread_read(
    thread_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark all messages in a thread as read.
    """
    thread, user_role, other_party_user_id = await get_thread_with_validation(
        thread_id, current_user, db
    )

    now = datetime.utcnow()

    # Determine which messages to mark as read
    if user_role == "PATIENT":
        # Mark doctor's messages as read
        await db.execute(
            DirectMessage.__table__.update()
            .where(
                and_(
                    DirectMessage.thread_id == thread_id,
                    DirectMessage.sender_type == "DOCTOR",
                    DirectMessage.is_read == False
                )
            )
            .values(is_read=True, read_at=now)
        )
        thread.patient_unread_count = 0
    else:
        # Mark patient's messages as read
        await db.execute(
            DirectMessage.__table__.update()
            .where(
                and_(
                    DirectMessage.thread_id == thread_id,
                    DirectMessage.sender_type == "PATIENT",
                    DirectMessage.is_read == False
                )
            )
            .values(is_read=True, read_at=now)
        )
        thread.doctor_unread_count = 0

    await db.commit()

    # Send WebSocket notification
    if other_party_user_id:
        await ws_manager.notify_message_read(
            thread_id=thread_id,
            reader_type=user_role,
            reader_user_id=current_user.id,
            other_party_user_id=other_party_user_id
        )

    return {"status": "ok"}


# ==================== Attachment Endpoint ====================

@router.post("/upload", response_model=AttachmentUploadResponse)
async def upload_attachment(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a file attachment.
    The attachment will be associated with a message when the message is sent.
    """
    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file
    is_valid, error = storage_service.validate_file(
        content_type=file.content_type,
        file_size=file_size
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    # Upload to S3
    try:
        s3_key, thumbnail_key = await storage_service.upload_file(
            file_content=content,
            filename=file.filename,
            content_type=file.content_type,
            folder="message_attachments"
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

    # Create attachment record (without message_id - will be set when message is sent)
    attachment = MessageAttachment(
        message_id=None,  # Will be set when message is sent
        file_name=file.filename,
        file_type=file.content_type,
        file_size=file_size,
        s3_key=s3_key,
        thumbnail_s3_key=thumbnail_key
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    return AttachmentUploadResponse(
        id=attachment.id,
        file_name=attachment.file_name,
        file_type=attachment.file_type,
        file_size=attachment.file_size,
        s3_key=attachment.s3_key,
        thumbnail_s3_key=attachment.thumbnail_s3_key
    )


# ==================== Unread Count Endpoint ====================

@router.get("/unread", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get total unread message count for the current user.
    """
    threads_unread = []
    total = 0

    if current_user.user_type == UserType.PATIENT:
        # Get patient profile
        patient_result = await db.execute(
            select(Patient).where(Patient.user_id == current_user.id)
        )
        patient = patient_result.scalar_one_or_none()
        if not patient:
            return UnreadCountResponse(total_unread=0, threads=[])

        # Get threads with unread messages
        result = await db.execute(
            select(DoctorPatientThread)
            .where(DoctorPatientThread.patient_id == patient.id)
        )
        threads = result.scalars().all()

        for thread in threads:
            if thread.patient_unread_count > 0:
                threads_unread.append(ThreadUnreadCount(
                    thread_id=thread.id,
                    unread_count=thread.patient_unread_count
                ))
                total += thread.patient_unread_count

    elif current_user.user_type == UserType.DOCTOR:
        # Get doctor profile
        doctor_result = await db.execute(
            select(Doctor).where(Doctor.user_id == current_user.id)
        )
        doctor = doctor_result.scalar_one_or_none()
        if not doctor:
            return UnreadCountResponse(total_unread=0, threads=[])

        # Get threads with unread messages
        result = await db.execute(
            select(DoctorPatientThread)
            .where(DoctorPatientThread.doctor_id == doctor.id)
        )
        threads = result.scalars().all()

        for thread in threads:
            if thread.doctor_unread_count > 0:
                threads_unread.append(ThreadUnreadCount(
                    thread_id=thread.id,
                    unread_count=thread.doctor_unread_count
                ))
                total += thread.doctor_unread_count

    return UnreadCountResponse(
        total_unread=total,
        threads=threads_unread
    )


# ==================== Doctor-specific Endpoints ====================

@router.post("/doctor/patients/{patient_id}/thread", response_model=ThreadSummary)
async def start_thread_with_patient(
    patient_id: str,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db)
):
    """
    Get or create a message thread with a patient.
    Only works for patients connected to this doctor.
    """
    # Verify patient exists and is connected to this doctor
    result = await db.execute(
        select(Patient).where(Patient.id == patient_id)
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    if patient.primary_doctor_id != doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This patient is not connected to you"
        )

    # Check if thread already exists
    thread_result = await db.execute(
        select(DoctorPatientThread).where(
            and_(
                DoctorPatientThread.doctor_id == doctor.id,
                DoctorPatientThread.patient_id == patient_id
            )
        )
    )
    thread = thread_result.scalar_one_or_none()

    if not thread:
        # Create new thread
        thread = DoctorPatientThread(
            doctor_id=doctor.id,
            patient_id=patient_id
        )
        db.add(thread)
        await db.commit()
        await db.refresh(thread)

    return ThreadSummary(
        id=thread.id,
        other_party_id=patient.id,
        other_party_name=f"{patient.first_name} {patient.last_name}",
        other_party_type="PATIENT",
        last_message_preview=None,
        last_message_at=thread.last_message_at,
        last_message_type=None,
        unread_count=thread.doctor_unread_count,
        can_send_message=True,
        created_at=thread.created_at
    )
