"""
Appointment management API endpoints.

Provides endpoints for doctors and patients to manage appointments.
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.appointment import Appointment, AppointmentStatus, CancelledBy
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.schemas.appointment import (
    AppointmentCancel,
    AppointmentComplete,
    AppointmentCreate,
    AppointmentListItem,
    AppointmentResponse,
    AppointmentStats,
    AppointmentStatusEnum,
    AppointmentTypeEnum,
    AppointmentUpdate,
    CalendarDay,
    CalendarDaySlot,
    CalendarMonthView,
    CalendarWeekView,
    PatientNotesUpdate,
)
from app.utils.deps import get_current_doctor, get_current_patient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/appointments", tags=["appointments"])


# ============================================
# Helper Functions
# ============================================


def appointment_to_response(appointment: Appointment) -> AppointmentResponse:
    """Convert appointment model to response schema."""
    from app.schemas.appointment import DoctorSummary, PatientSummary

    patient_data = None
    if appointment.patient:
        patient_data = PatientSummary(
            id=appointment.patient.id,
            first_name=appointment.patient.first_name,
            last_name=appointment.patient.last_name,
            full_name=appointment.patient.full_name,
        )

    doctor_data = None
    if appointment.doctor:
        doctor_data = DoctorSummary(
            id=appointment.doctor.id,
            first_name=appointment.doctor.first_name,
            last_name=appointment.doctor.last_name,
            full_name=appointment.doctor.full_name,
            specialty=appointment.doctor.specialty,
        )

    return AppointmentResponse(
        id=appointment.id,
        doctor_id=appointment.doctor_id,
        patient_id=appointment.patient_id,
        pre_visit_summary_id=appointment.pre_visit_summary_id,
        appointment_date=appointment.appointment_date,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        duration_minutes=appointment.duration_minutes,
        appointment_type=appointment.appointment_type,
        status=appointment.status,
        reason=appointment.reason,
        notes=appointment.notes,
        patient_notes=appointment.patient_notes,
        reminder_24h_sent=appointment.reminder_24h_sent,
        reminder_1h_sent=appointment.reminder_1h_sent,
        cancelled_by=appointment.cancelled_by,
        cancel_reason=appointment.cancel_reason,
        cancelled_at=appointment.cancelled_at,
        completed_at=appointment.completed_at,
        completion_notes=appointment.completion_notes,
        is_past=appointment.is_past,
        is_cancellable=appointment.is_cancellable,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
        patient=patient_data,
        doctor=doctor_data,
    )


def appointment_to_list_item(appointment: Appointment) -> AppointmentListItem:
    """Convert appointment model to list item schema."""
    from app.schemas.appointment import DoctorSummary, PatientSummary

    patient_data = None
    if appointment.patient:
        patient_data = PatientSummary(
            id=appointment.patient.id,
            first_name=appointment.patient.first_name,
            last_name=appointment.patient.last_name,
            full_name=appointment.patient.full_name,
        )

    doctor_data = None
    if appointment.doctor:
        doctor_data = DoctorSummary(
            id=appointment.doctor.id,
            first_name=appointment.doctor.first_name,
            last_name=appointment.doctor.last_name,
            full_name=appointment.doctor.full_name,
            specialty=appointment.doctor.specialty,
        )

    return AppointmentListItem(
        id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        appointment_date=appointment.appointment_date,
        start_time=appointment.start_time,
        end_time=appointment.end_time,
        appointment_type=appointment.appointment_type,
        status=appointment.status,
        reason=appointment.reason,
        is_past=appointment.is_past,
        is_cancellable=appointment.is_cancellable,
        patient=patient_data,
        doctor=doctor_data,
    )


async def check_time_conflict(
    db: AsyncSession,
    doctor_id: str,
    appointment_date: date,
    start_time,
    end_time,
    exclude_appointment_id: Optional[str] = None,
) -> bool:
    """Check if there's a time conflict with existing appointments."""
    query = select(Appointment).where(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date == appointment_date,
            Appointment.status.in_(
                [
                    AppointmentStatus.PENDING.value,
                    AppointmentStatus.CONFIRMED.value,
                ]
            ),
            or_(
                # New appointment starts during existing
                and_(
                    Appointment.start_time <= start_time,
                    Appointment.end_time > start_time,
                ),
                # New appointment ends during existing
                and_(
                    Appointment.start_time < end_time,
                    Appointment.end_time >= end_time,
                ),
                # New appointment contains existing
                and_(
                    Appointment.start_time >= start_time,
                    Appointment.end_time <= end_time,
                ),
            ),
        )
    )

    if exclude_appointment_id:
        query = query.where(Appointment.id != exclude_appointment_id)

    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


# ============================================
# Doctor Endpoints
# ============================================


@router.post("/doctor", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    request: AppointmentCreate,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new appointment.

    Only doctors can create appointments for their patients.
    """
    # Verify patient belongs to this doctor
    result = await db.execute(
        select(Patient).where(
            and_(
                Patient.id == request.patient_id,
                Patient.primary_doctor_id == doctor.id,
            )
        )
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or not assigned to you",
        )

    # Check for time conflicts
    if await check_time_conflict(db, doctor.id, request.appointment_date, request.start_time, request.end_time):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot conflicts with an existing appointment",
        )

    # Create appointment
    appointment = Appointment(
        doctor_id=doctor.id,
        patient_id=request.patient_id,
        appointment_date=request.appointment_date,
        start_time=request.start_time,
        end_time=request.end_time,
        appointment_type=request.appointment_type.value,
        reason=request.reason,
        notes=request.notes,
        pre_visit_summary_id=request.pre_visit_summary_id,
    )

    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)

    # Load relationships
    result = await db.execute(
        select(Appointment)
        .where(Appointment.id == appointment.id)
        .options(selectinload(Appointment.patient), selectinload(Appointment.doctor))
    )
    appointment = result.scalar_one()

    logger.info(f"Appointment created: {appointment.id} for patient {patient.id}")

    return appointment_to_response(appointment)


@router.get("/doctor/calendar", response_model=CalendarMonthView)
async def get_doctor_calendar(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Get calendar view of appointments for a month.

    Returns all appointments for the specified month grouped by day.
    """
    # Calculate date range
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    # Query appointments
    result = await db.execute(
        select(Appointment)
        .where(
            and_(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date <= end_date,
            )
        )
        .options(selectinload(Appointment.patient))
        .order_by(Appointment.appointment_date, Appointment.start_time)
    )
    appointments = result.scalars().all()

    # Group by date
    days_dict = {}
    for apt in appointments:
        apt_date = apt.appointment_date
        if apt_date not in days_dict:
            days_dict[apt_date] = []

        days_dict[apt_date].append(
            CalendarDaySlot(
                id=apt.id,
                start_time=apt.start_time,
                end_time=apt.end_time,
                status=apt.status,
                appointment_type=apt.appointment_type,
                patient_name=apt.patient.full_name if apt.patient else "Unknown",
                patient_id=apt.patient_id,
            )
        )

    # Build response
    days = [
        CalendarDay(
            date=d,
            appointments=slots,
            total_count=len(slots),
        )
        for d, slots in sorted(days_dict.items())
    ]

    return CalendarMonthView(
        year=year,
        month=month,
        days=days,
        total_appointments=len(appointments),
    )


@router.get("/doctor/week", response_model=CalendarWeekView)
async def get_doctor_week_view(
    start_date: date = Query(...),
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Get calendar view of appointments for a week.

    Returns all appointments for the 7 days starting from start_date.
    """
    end_date = start_date + timedelta(days=6)

    # Query appointments
    result = await db.execute(
        select(Appointment)
        .where(
            and_(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date >= start_date,
                Appointment.appointment_date <= end_date,
            )
        )
        .options(selectinload(Appointment.patient))
        .order_by(Appointment.appointment_date, Appointment.start_time)
    )
    appointments = result.scalars().all()

    # Group by date
    days_dict = {}
    for apt in appointments:
        apt_date = apt.appointment_date
        if apt_date not in days_dict:
            days_dict[apt_date] = []

        days_dict[apt_date].append(
            CalendarDaySlot(
                id=apt.id,
                start_time=apt.start_time,
                end_time=apt.end_time,
                status=apt.status,
                appointment_type=apt.appointment_type,
                patient_name=apt.patient.full_name if apt.patient else "Unknown",
                patient_id=apt.patient_id,
            )
        )

    # Build response
    days = [
        CalendarDay(
            date=d,
            appointments=slots,
            total_count=len(slots),
        )
        for d, slots in sorted(days_dict.items())
    ]

    return CalendarWeekView(
        start_date=start_date,
        end_date=end_date,
        days=days,
        total_appointments=len(appointments),
    )


@router.get("/doctor/list", response_model=List[AppointmentListItem])
async def get_doctor_appointments(
    status: Optional[AppointmentStatusEnum] = None,
    appointment_type: Optional[AppointmentTypeEnum] = None,
    patient_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Get filtered list of appointments for a doctor.

    Supports filtering by status, type, patient, and date range.
    """
    query = select(Appointment).where(Appointment.doctor_id == doctor.id)

    # Apply filters
    if status:
        query = query.where(Appointment.status == status.value)
    if appointment_type:
        query = query.where(Appointment.appointment_type == appointment_type.value)
    if patient_id:
        query = query.where(Appointment.patient_id == patient_id)
    if start_date:
        query = query.where(Appointment.appointment_date >= start_date)
    if end_date:
        query = query.where(Appointment.appointment_date <= end_date)

    # Order and paginate
    query = (
        query.options(selectinload(Appointment.patient))
        .order_by(Appointment.appointment_date.desc(), Appointment.start_time.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)
    appointments = result.scalars().all()

    return [appointment_to_list_item(apt) for apt in appointments]


@router.get("/doctor/stats", response_model=AppointmentStats)
async def get_doctor_appointment_stats(
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Get appointment statistics for the doctor's dashboard."""
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Get counts by status
    result = await db.execute(
        select(Appointment.status, func.count(Appointment.id))
        .where(Appointment.doctor_id == doctor.id)
        .group_by(Appointment.status)
    )
    status_counts = dict(result.all())

    # Get today's count
    today_result = await db.execute(
        select(func.count(Appointment.id)).where(
            and_(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date == today,
            )
        )
    )
    today_count = today_result.scalar() or 0

    # Get this week's count
    week_result = await db.execute(
        select(func.count(Appointment.id)).where(
            and_(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date >= week_start,
                Appointment.appointment_date <= today,
            )
        )
    )
    week_count = week_result.scalar() or 0

    # Get this month's count
    month_result = await db.execute(
        select(func.count(Appointment.id)).where(
            and_(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date >= month_start,
                Appointment.appointment_date <= today,
            )
        )
    )
    month_count = month_result.scalar() or 0

    return AppointmentStats(
        total=sum(status_counts.values()),
        pending=status_counts.get(AppointmentStatus.PENDING.value, 0),
        confirmed=status_counts.get(AppointmentStatus.CONFIRMED.value, 0),
        completed=status_counts.get(AppointmentStatus.COMPLETED.value, 0),
        cancelled=status_counts.get(AppointmentStatus.CANCELLED.value, 0),
        no_show=status_counts.get(AppointmentStatus.NO_SHOW.value, 0),
        today_count=today_count,
        this_week_count=week_count,
        this_month_count=month_count,
    )


@router.get("/doctor/{appointment_id}", response_model=AppointmentResponse)
async def get_doctor_appointment_detail(
    appointment_id: str,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed appointment information for a doctor."""
    result = await db.execute(
        select(Appointment)
        .where(
            and_(
                Appointment.id == appointment_id,
                Appointment.doctor_id == doctor.id,
            )
        )
        .options(selectinload(Appointment.patient), selectinload(Appointment.doctor))
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    return appointment_to_response(appointment)


@router.put("/doctor/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    request: AppointmentUpdate,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an appointment.

    Only doctors can update appointment details.
    Cannot update cancelled or completed appointments.
    """
    result = await db.execute(
        select(Appointment)
        .where(
            and_(
                Appointment.id == appointment_id,
                Appointment.doctor_id == doctor.id,
            )
        )
        .options(selectinload(Appointment.patient), selectinload(Appointment.doctor))
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if appointment.status in [
        AppointmentStatus.CANCELLED.value,
        AppointmentStatus.COMPLETED.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update cancelled or completed appointments",
        )

    # Check for time conflicts if date/time is being changed
    new_date = request.appointment_date or appointment.appointment_date
    new_start = request.start_time or appointment.start_time
    new_end = request.end_time or appointment.end_time

    if request.appointment_date or request.start_time or request.end_time:
        if await check_time_conflict(db, doctor.id, new_date, new_start, new_end, appointment.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Time slot conflicts with an existing appointment",
            )

    # Update fields
    update_data = request.model_dump(exclude_unset=True)
    if "appointment_type" in update_data and update_data["appointment_type"]:
        update_data["appointment_type"] = update_data["appointment_type"].value

    for field, value in update_data.items():
        setattr(appointment, field, value)

    await db.commit()
    await db.refresh(appointment)

    logger.info(f"Appointment updated: {appointment.id}")

    return appointment_to_response(appointment)


@router.post("/doctor/{appointment_id}/confirm", response_model=AppointmentResponse)
async def confirm_appointment(
    appointment_id: str,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Confirm a pending appointment."""
    result = await db.execute(
        select(Appointment)
        .where(
            and_(
                Appointment.id == appointment_id,
                Appointment.doctor_id == doctor.id,
            )
        )
        .options(selectinload(Appointment.patient), selectinload(Appointment.doctor))
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if appointment.status != AppointmentStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot confirm appointment with status: {appointment.status}",
        )

    appointment.status = AppointmentStatus.CONFIRMED.value
    await db.commit()
    await db.refresh(appointment)

    logger.info(f"Appointment confirmed: {appointment.id}")

    return appointment_to_response(appointment)


@router.post("/doctor/{appointment_id}/complete", response_model=AppointmentResponse)
async def complete_appointment(
    appointment_id: str,
    request: AppointmentComplete,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Mark an appointment as completed."""
    result = await db.execute(
        select(Appointment)
        .where(
            and_(
                Appointment.id == appointment_id,
                Appointment.doctor_id == doctor.id,
            )
        )
        .options(selectinload(Appointment.patient), selectinload(Appointment.doctor))
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if appointment.status not in [
        AppointmentStatus.PENDING.value,
        AppointmentStatus.CONFIRMED.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete appointment with status: {appointment.status}",
        )

    appointment.status = AppointmentStatus.COMPLETED.value
    appointment.completed_at = datetime.utcnow()
    appointment.completion_notes = request.completion_notes

    await db.commit()
    await db.refresh(appointment)

    logger.info(f"Appointment completed: {appointment.id}")

    return appointment_to_response(appointment)


@router.post("/doctor/{appointment_id}/no-show", response_model=AppointmentResponse)
async def mark_appointment_no_show(
    appointment_id: str,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Mark an appointment as no-show (patient didn't attend)."""
    result = await db.execute(
        select(Appointment)
        .where(
            and_(
                Appointment.id == appointment_id,
                Appointment.doctor_id == doctor.id,
            )
        )
        .options(selectinload(Appointment.patient), selectinload(Appointment.doctor))
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if appointment.status not in [
        AppointmentStatus.PENDING.value,
        AppointmentStatus.CONFIRMED.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot mark as no-show for appointment with status: {appointment.status}",
        )

    appointment.status = AppointmentStatus.NO_SHOW.value
    await db.commit()
    await db.refresh(appointment)

    logger.info(f"Appointment marked as no-show: {appointment.id}")

    return appointment_to_response(appointment)


@router.post("/doctor/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment_by_doctor(
    appointment_id: str,
    request: AppointmentCancel,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an appointment as a doctor."""
    result = await db.execute(
        select(Appointment)
        .where(
            and_(
                Appointment.id == appointment_id,
                Appointment.doctor_id == doctor.id,
            )
        )
        .options(selectinload(Appointment.patient), selectinload(Appointment.doctor))
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if not appointment.is_cancellable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This appointment cannot be cancelled",
        )

    appointment.status = AppointmentStatus.CANCELLED.value
    appointment.cancelled_by = CancelledBy.DOCTOR.value
    appointment.cancel_reason = request.cancel_reason
    appointment.cancelled_at = datetime.utcnow()

    await db.commit()
    await db.refresh(appointment)

    logger.info(f"Appointment cancelled by doctor: {appointment.id}")

    return appointment_to_response(appointment)


# ============================================
# Patient Endpoints
# ============================================


@router.get("/patient/list", response_model=List[AppointmentListItem])
async def get_patient_appointments(
    status: Optional[AppointmentStatusEnum] = None,
    upcoming_only: bool = False,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of appointments for a patient.

    Can filter by status or show only upcoming appointments.
    """
    query = select(Appointment).where(Appointment.patient_id == patient.id)

    if status:
        query = query.where(Appointment.status == status.value)

    if upcoming_only:
        query = query.where(
            and_(
                Appointment.appointment_date >= date.today(),
                Appointment.status.in_(
                    [
                        AppointmentStatus.PENDING.value,
                        AppointmentStatus.CONFIRMED.value,
                    ]
                ),
            )
        )

    query = (
        query.options(selectinload(Appointment.doctor))
        .order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)
    appointments = result.scalars().all()

    return [appointment_to_list_item(apt) for apt in appointments]


@router.get("/patient/upcoming", response_model=List[AppointmentListItem])
async def get_patient_upcoming_appointments(
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Get next upcoming appointments for a patient (max 5)."""
    query = (
        select(Appointment)
        .where(
            and_(
                Appointment.patient_id == patient.id,
                Appointment.appointment_date >= date.today(),
                Appointment.status.in_(
                    [
                        AppointmentStatus.PENDING.value,
                        AppointmentStatus.CONFIRMED.value,
                    ]
                ),
            )
        )
        .options(selectinload(Appointment.doctor))
        .order_by(Appointment.appointment_date.asc(), Appointment.start_time.asc())
        .limit(5)
    )

    result = await db.execute(query)
    appointments = result.scalars().all()

    return [appointment_to_list_item(apt) for apt in appointments]


@router.get("/patient/{appointment_id}", response_model=AppointmentResponse)
async def get_patient_appointment_detail(
    appointment_id: str,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed appointment information for a patient."""
    result = await db.execute(
        select(Appointment)
        .where(
            and_(
                Appointment.id == appointment_id,
                Appointment.patient_id == patient.id,
            )
        )
        .options(selectinload(Appointment.patient), selectinload(Appointment.doctor))
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    return appointment_to_response(appointment)


@router.put("/patient/{appointment_id}/notes", response_model=AppointmentResponse)
async def update_patient_notes(
    appointment_id: str,
    request: PatientNotesUpdate,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Update patient notes for an appointment."""
    result = await db.execute(
        select(Appointment)
        .where(
            and_(
                Appointment.id == appointment_id,
                Appointment.patient_id == patient.id,
            )
        )
        .options(selectinload(Appointment.patient), selectinload(Appointment.doctor))
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if appointment.status in [
        AppointmentStatus.CANCELLED.value,
        AppointmentStatus.COMPLETED.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update notes for cancelled or completed appointments",
        )

    appointment.patient_notes = request.patient_notes
    await db.commit()
    await db.refresh(appointment)

    logger.info(f"Patient notes updated for appointment: {appointment.id}")

    return appointment_to_response(appointment)


@router.post("/patient/{appointment_id}/cancel", response_model=AppointmentResponse)
async def cancel_appointment_by_patient(
    appointment_id: str,
    request: AppointmentCancel,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Cancel an appointment as a patient."""
    result = await db.execute(
        select(Appointment)
        .where(
            and_(
                Appointment.id == appointment_id,
                Appointment.patient_id == patient.id,
            )
        )
        .options(selectinload(Appointment.patient), selectinload(Appointment.doctor))
    )
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if not appointment.is_cancellable:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This appointment cannot be cancelled",
        )

    appointment.status = AppointmentStatus.CANCELLED.value
    appointment.cancelled_by = CancelledBy.PATIENT.value
    appointment.cancel_reason = request.cancel_reason
    appointment.cancelled_at = datetime.utcnow()

    await db.commit()
    await db.refresh(appointment)

    logger.info(f"Appointment cancelled by patient: {appointment.id}")

    return appointment_to_response(appointment)
