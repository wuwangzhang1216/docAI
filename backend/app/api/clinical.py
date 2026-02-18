from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, func, literal, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.assessment import Assessment, AssessmentType, SeverityLevel
from app.models.checkin import DailyCheckin
from app.models.connection_request import ConnectionStatus, PatientConnectionRequest
from app.models.doctor import Doctor
from app.models.messaging import DoctorPatientThread
from app.models.patient import Patient
from app.models.risk_event import RiskEvent, RiskLevel
from app.models.user import User, UserType
from app.schemas.clinical import (
    AssessmentCreate,
    AssessmentResponse,
    CheckinCreate,
    CheckinResponse,
    DoctorAIChatRequest,
    DoctorAIChatResponse,
    DoctorConversationListItem,
    DoctorConversationMessage,
    DoctorConversationResponse,
    PatientOverview,
    RiskEventResponse,
)
from app.schemas.common import PaginatedResponse
from app.schemas.connection import (
    ConnectionRequestCreate,
    ConnectionRequestResponse,
    ConnectionRequestStatusResponse,
    DoctorPublicInfo,
    PatientConnectionRequestView,
)
from app.schemas.user import (
    DoctorCreatePatient,
    DoctorCreatePatientResponse,
    DoctorPublicProfile,
    DoctorResponse,
    DoctorUpdate,
    PatientResponse,
)
from app.utils.deps import get_current_doctor, get_current_patient
from app.utils.security import hash_password

router = APIRouter(prefix="/clinical", tags=["clinical"])


# ========== Daily Check-in ==========


@router.post("/checkin", response_model=CheckinResponse)
async def submit_checkin(
    request: CheckinCreate,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit or update daily check-in.

    If a check-in already exists for today, it will be updated.
    """
    today = date.today()

    # Check if already checked in today
    result = await db.execute(
        select(DailyCheckin).where(
            and_(
                DailyCheckin.patient_id == patient.id,
                DailyCheckin.checkin_date == today,
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing check-in
        existing.mood_score = request.mood_score
        existing.sleep_hours = request.sleep_hours
        existing.sleep_quality = request.sleep_quality
        existing.medication_taken = request.medication_taken
        existing.notes = request.notes
        checkin = existing
    else:
        # Create new check-in
        checkin = DailyCheckin(
            patient_id=patient.id,
            checkin_date=today,
            mood_score=request.mood_score,
            sleep_hours=request.sleep_hours,
            sleep_quality=request.sleep_quality,
            medication_taken=request.medication_taken,
            notes=request.notes,
        )
        db.add(checkin)

    await db.commit()
    await db.refresh(checkin)

    return checkin


@router.get("/checkins", response_model=List[CheckinResponse])
async def get_checkins(
    start_date: date = Query(..., description="Start date (inclusive)"),
    end_date: date = Query(..., description="End date (inclusive)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Get check-ins for a date range with pagination."""
    result = await db.execute(
        select(DailyCheckin)
        .where(
            and_(
                DailyCheckin.patient_id == patient.id,
                DailyCheckin.checkin_date >= start_date,
                DailyCheckin.checkin_date <= end_date,
            )
        )
        .order_by(DailyCheckin.checkin_date)
        .limit(limit)
        .offset(offset)
    )
    checkins = result.scalars().all()
    return checkins


@router.get("/checkin/today", response_model=Optional[CheckinResponse])
async def get_today_checkin(patient: Patient = Depends(get_current_patient), db: AsyncSession = Depends(get_db)):
    """Get today's check-in if exists."""
    result = await db.execute(
        select(DailyCheckin).where(
            and_(
                DailyCheckin.patient_id == patient.id,
                DailyCheckin.checkin_date == date.today(),
            )
        )
    )
    return result.scalar_one_or_none()


# ========== Assessments ==========

# PHQ-9 severity thresholds (Depression)
PHQ9_SEVERITY = [
    (4, SeverityLevel.MINIMAL),
    (9, SeverityLevel.MILD),
    (14, SeverityLevel.MODERATE),
    (19, SeverityLevel.MODERATELY_SEVERE),
    (27, SeverityLevel.SEVERE),
]

# GAD-7 severity thresholds (Anxiety)
GAD7_SEVERITY = [
    (4, SeverityLevel.MINIMAL),
    (9, SeverityLevel.MILD),
    (14, SeverityLevel.MODERATE),
    (21, SeverityLevel.SEVERE),
]

# PCL-5 severity thresholds (PTSD)
# Based on VA/DoD Clinical Practice Guidelines
# Score range: 0-80 (20 items x 0-4 scale), simplified version uses 8 items (0-32)
# Cutoff of 31-33 on full scale suggests probable PTSD diagnosis
# For simplified 8-item version, proportional cutoff ~12-13
PCL5_SEVERITY = [
    (7, SeverityLevel.MINIMAL),  # 0-7: Minimal symptoms
    (12, SeverityLevel.MILD),  # 8-12: Mild symptoms
    (19, SeverityLevel.MODERATE),  # 13-19: Moderate symptoms
    (25, SeverityLevel.MODERATELY_SEVERE),  # 20-25: Moderately severe
    (32, SeverityLevel.SEVERE),  # 26-32: Severe symptoms
]


def calculate_severity(score: int, assessment_type: AssessmentType) -> SeverityLevel:
    """Calculate severity level based on score and assessment type."""
    if assessment_type == AssessmentType.PHQ9:
        thresholds = PHQ9_SEVERITY
    elif assessment_type == AssessmentType.GAD7:
        thresholds = GAD7_SEVERITY
    elif assessment_type == AssessmentType.PCL5:
        thresholds = PCL5_SEVERITY
    else:
        # Default to PHQ9 thresholds for unknown types
        thresholds = PHQ9_SEVERITY

    for threshold, level in thresholds:
        if score <= threshold:
            return level

    return SeverityLevel.SEVERE


@router.post("/assessment", response_model=AssessmentResponse)
async def submit_assessment(
    request: AssessmentCreate,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an assessment (PHQ-9, GAD-7, PCL-5, etc.).

    Calculates total score, severity level, and risk flags.
    Supports trauma-specific assessments for political trauma survivors.
    """
    # Calculate total score
    total_score = sum(request.responses.values())

    # Calculate severity
    severity = calculate_severity(total_score, request.assessment_type)

    # Check for risk flags based on assessment type
    risk_flags = {}

    if request.assessment_type == AssessmentType.PHQ9:
        # PHQ-9 question 9 = suicidal ideation
        q9_score = request.responses.get("q9", 0)
        if q9_score > 0:
            risk_flags["suicidal_ideation"] = True
            risk_flags["q9_score"] = q9_score

    elif request.assessment_type == AssessmentType.PCL5:
        # PCL-5 risk assessment for PTSD
        # Check for high hypervigilance (p7) - common in political trauma
        p7_score = request.responses.get("p7", 0)
        if p7_score >= 3:
            risk_flags["high_hypervigilance"] = True
            risk_flags["p7_score"] = p7_score

        # Check for severe avoidance (p3, p4) - may indicate need for support
        avoidance_score = request.responses.get("p3", 0) + request.responses.get("p4", 0)
        if avoidance_score >= 5:
            risk_flags["severe_avoidance"] = True
            risk_flags["avoidance_score"] = avoidance_score

        # Check for negative beliefs (p5) - common in survivor guilt
        p5_score = request.responses.get("p5", 0)
        if p5_score >= 3:
            risk_flags["negative_beliefs"] = True
            risk_flags["p5_score"] = p5_score

        # High total score indicates probable PTSD
        if total_score >= 13:
            risk_flags["probable_ptsd"] = True

    # Create assessment
    assessment = Assessment(
        patient_id=patient.id,
        assessment_type=request.assessment_type,
        responses=request.responses,
        total_score=total_score,
        severity=severity,
        risk_flags=risk_flags if risk_flags else None,
    )
    db.add(assessment)

    # If high risk, create risk event
    if request.assessment_type == AssessmentType.PHQ9:
        if risk_flags.get("suicidal_ideation") and risk_flags.get("q9_score", 0) >= 2:
            risk_event = RiskEvent(
                patient_id=patient.id,
                risk_level=(RiskLevel.HIGH if risk_flags["q9_score"] >= 2 else RiskLevel.MEDIUM),
                risk_type="SUICIDAL",
                trigger_text=f"PHQ-9 Q9 score: {risk_flags['q9_score']}",
                ai_confidence=1.0,  # Direct from assessment
            )
            db.add(risk_event)

    elif request.assessment_type == AssessmentType.PCL5:
        # Create risk event for severe PTSD symptoms
        if risk_flags.get("probable_ptsd") and severity in [
            SeverityLevel.MODERATELY_SEVERE,
            SeverityLevel.SEVERE,
        ]:
            risk_event = RiskEvent(
                patient_id=patient.id,
                risk_level=RiskLevel.MEDIUM,
                risk_type="OTHER",  # PTSD requires clinical follow-up
                trigger_text=f"PCL-5 score: {total_score} - Probable PTSD, severity: {severity.value}",
                ai_confidence=1.0,
            )
            db.add(risk_event)

    await db.commit()
    await db.refresh(assessment)

    return assessment


@router.get("/assessments", response_model=List[AssessmentResponse])
async def get_assessments(
    assessment_type: Optional[AssessmentType] = None,
    limit: int = Query(10, ge=1, le=100),
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """Get assessments with optional type filter."""
    query = select(Assessment).where(Assessment.patient_id == patient.id)

    if assessment_type:
        query = query.where(Assessment.assessment_type == assessment_type)

    query = query.order_by(Assessment.created_at.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


# ========== Doctor Endpoints ==========


@router.get("/doctor/patients", response_model=PaginatedResponse[PatientOverview])
async def get_doctor_patients(
    limit: int = Query(10, ge=1, le=50, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    search: Optional[str] = Query(None, description="Search by patient name"),
    sort_by: str = Query("risk", description="Sort by: risk, name, mood"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Get overview of all patients assigned to the doctor with pagination.

    Returns recent mood average, latest assessment scores, and unreviewed risks.
    Supports search by name, sorting, and pagination.
    """
    seven_days_ago = date.today() - timedelta(days=7)

    # Build subqueries for aggregated stats (eliminates N+1 queries)
    mood_subq = (
        select(
            DailyCheckin.patient_id,
            func.avg(DailyCheckin.mood_score).label("avg_mood"),
        )
        .where(DailyCheckin.checkin_date >= seven_days_ago)
        .group_by(DailyCheckin.patient_id)
        .subquery()
    )

    # Latest PHQ-9: use a correlated subquery for max created_at
    phq9_latest = (
        select(Assessment.total_score)
        .where(
            and_(
                Assessment.patient_id == Patient.id,
                Assessment.assessment_type == AssessmentType.PHQ9,
            )
        )
        .order_by(Assessment.created_at.desc())
        .limit(1)
        .correlate(Patient)
        .scalar_subquery()
        .label("latest_phq9")
    )

    # Latest GAD-7
    gad7_latest = (
        select(Assessment.total_score)
        .where(
            and_(
                Assessment.patient_id == Patient.id,
                Assessment.assessment_type == AssessmentType.GAD7,
            )
        )
        .order_by(Assessment.created_at.desc())
        .limit(1)
        .correlate(Patient)
        .scalar_subquery()
        .label("latest_gad7")
    )

    # Unreviewed risk count subquery
    risk_subq = (
        select(
            RiskEvent.patient_id,
            func.count(RiskEvent.id).label("unreviewed_risks"),
        )
        .where(RiskEvent.doctor_reviewed == False)
        .group_by(RiskEvent.patient_id)
        .subquery()
    )

    # Main query: single query with all stats via LEFT JOINs
    base_query = (
        select(
            Patient.id,
            (Patient.first_name + " " + Patient.last_name).label("patient_name"),
            mood_subq.c.avg_mood,
            phq9_latest,
            gad7_latest,
            func.coalesce(risk_subq.c.unreviewed_risks, literal(0)).label("unreviewed_risks"),
        )
        .outerjoin(mood_subq, mood_subq.c.patient_id == Patient.id)
        .outerjoin(risk_subq, risk_subq.c.patient_id == Patient.id)
        .where(Patient.primary_doctor_id == doctor.id)
    )

    # Apply search filter
    if search:
        search_term = f"%{search.lower()}%"
        base_query = base_query.where(func.lower(Patient.first_name + " " + Patient.last_name).like(search_term))

    # Get total count
    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar() or 0

    # Apply sorting at database level
    reverse = sort_order.lower() == "desc"
    if sort_by == "name":
        order_col = func.lower(Patient.first_name + " " + Patient.last_name)
        base_query = base_query.order_by(order_col.desc() if reverse else order_col.asc())
    elif sort_by == "mood":
        order_col = func.coalesce(mood_subq.c.avg_mood, literal(-1))
        base_query = base_query.order_by(order_col.desc() if reverse else order_col.asc())
    else:
        # Default: sort by risk count
        order_col = func.coalesce(risk_subq.c.unreviewed_risks, literal(0))
        base_query = base_query.order_by(order_col.desc() if reverse else order_col.asc())

    # Apply pagination at database level
    base_query = base_query.offset(offset).limit(limit)

    result = await db.execute(base_query)
    rows = result.fetchall()

    paginated_items = [
        PatientOverview(
            patient_id=row.id,
            patient_name=row.patient_name,
            recent_mood_avg=float(row.avg_mood) if row.avg_mood is not None else None,
            latest_phq9=row.latest_phq9,
            latest_gad7=row.latest_gad7,
            unreviewed_risks=row.unreviewed_risks,
        )
        for row in rows
    ]

    return PaginatedResponse(
        items=paginated_items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + limit < total,
    )


@router.get("/doctor/risk-queue", response_model=PaginatedResponse[RiskEventResponse])
async def get_risk_queue(
    limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level: CRITICAL, HIGH, MEDIUM, LOW"),
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    search: Optional[str] = Query(None, description="Search in trigger text"),
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Get unreviewed risk events for the doctor's patients with pagination.

    Ordered by risk level (critical first) and creation time.
    Supports filtering by risk level, patient, and search in trigger text.
    """
    # Get patient IDs for this doctor
    patient_result = await db.execute(select(Patient.id).where(Patient.primary_doctor_id == doctor.id))
    patient_ids = [row[0] for row in patient_result.fetchall()]

    if not patient_ids:
        return PaginatedResponse(items=[], total=0, limit=limit, offset=offset, has_more=False)

    # Build base query - concatenate first_name and last_name since full_name is a property
    base_query = (
        select(
            RiskEvent,
            (Patient.first_name + " " + Patient.last_name).label("patient_name"),
        )
        .join(Patient, RiskEvent.patient_id == Patient.id)
        .where(
            and_(
                RiskEvent.patient_id.in_(patient_ids),
                RiskEvent.doctor_reviewed == False,
            )
        )
    )

    # Apply filters
    if risk_level:
        try:
            level_enum = RiskLevel(risk_level.upper())
            base_query = base_query.where(RiskEvent.risk_level == level_enum)
        except ValueError:
            pass  # Invalid risk level, ignore filter

    if patient_id:
        base_query = base_query.where(RiskEvent.patient_id == patient_id)

    if search:
        search_term = f"%{search.lower()}%"
        base_query = base_query.where(func.lower(RiskEvent.trigger_text).like(search_term))

    # Get total count - reuse base_query filters to avoid duplication
    count_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
    total = count_result.scalar() or 0

    # Apply ordering and pagination
    base_query = (
        base_query.order_by(RiskEvent.risk_level.desc(), RiskEvent.created_at.desc()).offset(offset).limit(limit)
    )

    result = await db.execute(base_query)

    risk_events = []
    for row in result.fetchall():
        event = row[0]
        patient_name = row[1]
        risk_events.append(
            RiskEventResponse(
                id=event.id,
                patient_id=event.patient_id,
                patient_name=patient_name,
                conversation_id=event.conversation_id,
                risk_level=event.risk_level,
                risk_type=event.risk_type,
                trigger_text=event.trigger_text,
                ai_confidence=(float(event.ai_confidence) if event.ai_confidence else None),
                doctor_reviewed=event.doctor_reviewed,
                doctor_notes=event.doctor_notes,
                created_at=event.created_at,
            )
        )

    return PaginatedResponse(
        items=risk_events,
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + limit < total,
    )


@router.post("/doctor/risk-events/{event_id}/review")
async def review_risk_event(
    event_id: str,
    notes: Optional[str] = None,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Mark a risk event as reviewed by the doctor."""
    result = await db.execute(select(RiskEvent).where(RiskEvent.id == event_id))
    event = result.scalar_one_or_none()

    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk event not found")

    # Verify the patient belongs to this doctor
    patient_result = await db.execute(select(Patient).where(Patient.id == event.patient_id))
    patient = patient_result.scalar_one_or_none()

    if not patient or patient.primary_doctor_id != doctor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to review this risk event",
        )

    event.doctor_reviewed = True
    event.doctor_notes = notes
    await db.commit()

    return {"status": "reviewed", "event_id": str(event_id)}


@router.get("/doctor/patients/{patient_id}/checkins", response_model=List[CheckinResponse])
async def get_patient_checkins(
    patient_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Get check-ins for a specific patient (doctor view) with pagination."""
    # Verify patient belongs to doctor
    patient_result = await db.execute(
        select(Patient).where(and_(Patient.id == patient_id, Patient.primary_doctor_id == doctor.id))
    )
    if not patient_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this patient",
        )

    result = await db.execute(
        select(DailyCheckin)
        .where(
            and_(
                DailyCheckin.patient_id == patient_id,
                DailyCheckin.checkin_date >= start_date,
                DailyCheckin.checkin_date <= end_date,
            )
        )
        .order_by(DailyCheckin.checkin_date)
        .limit(limit)
        .offset(offset)
    )

    return result.scalars().all()


@router.get("/doctor/patients/{patient_id}/profile", response_model=PatientResponse)
async def get_patient_profile(
    patient_id: str,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Get full profile for a specific patient (doctor view)."""
    # Verify patient belongs to doctor
    result = await db.execute(
        select(Patient).where(and_(Patient.id == patient_id, Patient.primary_doctor_id == doctor.id))
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this patient",
        )

    return patient


@router.get("/doctor/patients/{patient_id}/pre-visit-summaries")
async def get_patient_pre_visit_summaries(
    patient_id: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """Get pre-visit summaries for a patient (doctor view) with pagination."""
    from sqlalchemy import desc

    from app.models.pre_visit_summary import PreVisitSummary

    # Verify patient belongs to doctor
    result = await db.execute(
        select(Patient).where(and_(Patient.id == patient_id, Patient.primary_doctor_id == doctor.id))
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this patient",
        )

    # Get pre-visit summaries with pagination
    summaries_result = await db.execute(
        select(PreVisitSummary)
        .where(PreVisitSummary.patient_id == patient_id)
        .order_by(desc(PreVisitSummary.created_at))
        .limit(limit)
        .offset(offset)
    )
    summaries = summaries_result.scalars().all()

    return [
        {
            "id": s.id,
            "patient_id": s.patient_id,
            "conversation_id": s.conversation_id,
            "scheduled_visit": (s.scheduled_visit.isoformat() if s.scheduled_visit else None),
            "chief_complaint": s.chief_complaint,
            "phq9_score": s.phq9_score,
            "gad7_score": s.gad7_score,
            "doctor_viewed": s.doctor_viewed,
            "doctor_viewed_at": (s.doctor_viewed_at.isoformat() if s.doctor_viewed_at else None),
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in summaries
    ]


# ========== Doctor Connection Request Endpoints ==========


@router.post("/doctor/connection-requests", response_model=ConnectionRequestResponse)
async def send_connection_request(
    request: ConnectionRequestCreate,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a connection request to a patient by email.

    The patient must exist in the system and not already be connected to this doctor.
    Only one PENDING request can exist per doctor-patient pair.
    """
    # Find patient by email (case-insensitive)
    result = await db.execute(
        select(Patient)
        .join(User, Patient.user_id == User.id)
        .where(func.lower(User.email) == func.lower(request.patient_email))
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No patient found with this email address",
        )

    # Check if patient is already connected to this doctor
    if patient.primary_doctor_id == doctor.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This patient is already connected to you",
        )

    # Check for existing pending request
    existing_result = await db.execute(
        select(PatientConnectionRequest).where(
            and_(
                PatientConnectionRequest.doctor_id == doctor.id,
                PatientConnectionRequest.patient_id == patient.id,
                PatientConnectionRequest.status == ConnectionStatus.PENDING,
            )
        )
    )
    existing_request = existing_result.scalar_one_or_none()

    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A pending connection request already exists for this patient",
        )

    # Get patient's email for response
    user_result = await db.execute(select(User).where(User.id == patient.user_id))
    patient_user = user_result.scalar_one()

    # Create connection request
    connection_request = PatientConnectionRequest(
        doctor_id=doctor.id,
        patient_id=patient.id,
        message=request.message,
        status=ConnectionStatus.PENDING,
    )
    db.add(connection_request)
    await db.commit()
    await db.refresh(connection_request)

    return ConnectionRequestResponse(
        id=connection_request.id,
        doctor_id=connection_request.doctor_id,
        patient_id=connection_request.patient_id,
        patient_name=patient.full_name,
        patient_email=patient_user.email,
        status=connection_request.status,
        message=connection_request.message,
        created_at=connection_request.created_at,
        updated_at=connection_request.updated_at,
        responded_at=connection_request.responded_at,
    )


@router.get(
    "/doctor/connection-requests",
    response_model=PaginatedResponse[ConnectionRequestResponse],
)
async def get_doctor_connection_requests(
    limit: int = Query(20, ge=1, le=50, description="Number of items per page"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    status_filter: Optional[ConnectionStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None, description="Search by patient name or email"),
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Get connection requests sent by this doctor with pagination.

    Optionally filter by status (PENDING, ACCEPTED, REJECTED, CANCELLED).
    Supports search by patient name or email.
    """
    # Build base query
    base_query = (
        select(PatientConnectionRequest, Patient, User)
        .join(Patient, PatientConnectionRequest.patient_id == Patient.id)
        .join(User, Patient.user_id == User.id)
        .where(PatientConnectionRequest.doctor_id == doctor.id)
    )

    # Apply status filter
    if status_filter:
        base_query = base_query.where(PatientConnectionRequest.status == status_filter)

    # Apply search filter
    if search:
        search_term = f"%{search.lower()}%"
        base_query = base_query.where(
            (func.lower(Patient.first_name + " " + Patient.last_name).like(search_term))
            | (func.lower(User.email).like(search_term))
        )

    # Build count query with same filters
    count_query = (
        select(PatientConnectionRequest.id)
        .join(Patient, PatientConnectionRequest.patient_id == Patient.id)
        .join(User, Patient.user_id == User.id)
        .where(PatientConnectionRequest.doctor_id == doctor.id)
    )

    if status_filter:
        count_query = count_query.where(PatientConnectionRequest.status == status_filter)

    if search:
        search_term = f"%{search.lower()}%"
        count_query = count_query.where(
            (func.lower(Patient.first_name + " " + Patient.last_name).like(search_term))
            | (func.lower(User.email).like(search_term))
        )

    count_result = await db.execute(select(func.count()).select_from(count_query.subquery()))
    total = count_result.scalar() or 0

    # Apply ordering and pagination
    base_query = base_query.order_by(PatientConnectionRequest.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(base_query)
    rows = result.fetchall()

    items = [
        ConnectionRequestResponse(
            id=req.id,
            doctor_id=req.doctor_id,
            patient_id=req.patient_id,
            patient_name=patient.full_name,
            patient_email=user.email,
            status=req.status,
            message=req.message,
            created_at=req.created_at,
            updated_at=req.updated_at,
            responded_at=req.responded_at,
        )
        for req, patient, user in rows
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + limit < total,
    )


@router.delete(
    "/doctor/connection-requests/{request_id}",
    response_model=ConnectionRequestStatusResponse,
)
async def cancel_connection_request(
    request_id: str,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel a pending connection request.

    Only PENDING requests can be cancelled.
    """
    result = await db.execute(
        select(PatientConnectionRequest).where(
            and_(
                PatientConnectionRequest.id == request_id,
                PatientConnectionRequest.doctor_id == doctor.id,
            )
        )
    )
    connection_request = result.scalar_one_or_none()

    if not connection_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection request not found")

    if connection_request.status != ConnectionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel request with status {connection_request.status}",
        )

    connection_request.status = ConnectionStatus.CANCELLED
    connection_request.updated_at = datetime.utcnow()
    await db.commit()

    return ConnectionRequestStatusResponse(
        status="cancelled",
        request_id=request_id,
        message="Connection request has been cancelled",
    )


# ========== Patient Connection Request Endpoints ==========


@router.get("/patient/connection-requests", response_model=List[PatientConnectionRequestView])
async def get_patient_connection_requests(
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Get pending connection requests for the current patient with pagination.

    Only returns PENDING requests.
    """
    result = await db.execute(
        select(PatientConnectionRequest, Doctor)
        .join(Doctor, PatientConnectionRequest.doctor_id == Doctor.id)
        .where(
            and_(
                PatientConnectionRequest.patient_id == patient.id,
                PatientConnectionRequest.status == ConnectionStatus.PENDING,
            )
        )
        .order_by(PatientConnectionRequest.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = result.fetchall()

    return [
        PatientConnectionRequestView(
            id=req.id,
            doctor_id=req.doctor_id,
            doctor_name=doctor.full_name,
            doctor_specialty=doctor.specialty,
            message=req.message,
            created_at=req.created_at,
        )
        for req, doctor in rows
    ]


@router.post(
    "/patient/connection-requests/{request_id}/accept",
    response_model=ConnectionRequestStatusResponse,
)
async def accept_connection_request(
    request_id: str,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Accept a connection request from a doctor.

    Sets the doctor as the patient's primary doctor and updates the request status.
    """
    result = await db.execute(
        select(PatientConnectionRequest).where(
            and_(
                PatientConnectionRequest.id == request_id,
                PatientConnectionRequest.patient_id == patient.id,
            )
        )
    )
    connection_request = result.scalar_one_or_none()

    if not connection_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection request not found")

    if connection_request.status != ConnectionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot accept request with status {connection_request.status}",
        )

    # Update the patient's primary doctor
    patient.primary_doctor_id = connection_request.doctor_id

    # Update the request status
    connection_request.status = ConnectionStatus.ACCEPTED
    connection_request.responded_at = datetime.utcnow()
    connection_request.updated_at = datetime.utcnow()

    # Create message thread for doctor-patient communication
    existing_thread = await db.execute(
        select(DoctorPatientThread).where(
            and_(
                DoctorPatientThread.doctor_id == connection_request.doctor_id,
                DoctorPatientThread.patient_id == patient.id,
            )
        )
    )
    if not existing_thread.scalar_one_or_none():
        new_thread = DoctorPatientThread(doctor_id=connection_request.doctor_id, patient_id=patient.id)
        db.add(new_thread)

    await db.commit()

    return ConnectionRequestStatusResponse(
        status="accepted",
        request_id=request_id,
        message="You are now connected with the doctor",
    )


@router.post(
    "/patient/connection-requests/{request_id}/reject",
    response_model=ConnectionRequestStatusResponse,
)
async def reject_connection_request(
    request_id: str,
    patient: Patient = Depends(get_current_patient),
    db: AsyncSession = Depends(get_db),
):
    """
    Reject a connection request from a doctor.
    """
    result = await db.execute(
        select(PatientConnectionRequest).where(
            and_(
                PatientConnectionRequest.id == request_id,
                PatientConnectionRequest.patient_id == patient.id,
            )
        )
    )
    connection_request = result.scalar_one_or_none()

    if not connection_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection request not found")

    if connection_request.status != ConnectionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject request with status {connection_request.status}",
        )

    connection_request.status = ConnectionStatus.REJECTED
    connection_request.responded_at = datetime.utcnow()
    connection_request.updated_at = datetime.utcnow()

    await db.commit()

    return ConnectionRequestStatusResponse(
        status="rejected",
        request_id=request_id,
        message="Connection request has been rejected",
    )


@router.get("/patient/my-doctor", response_model=Optional[DoctorPublicInfo])
async def get_patient_doctor(patient: Patient = Depends(get_current_patient), db: AsyncSession = Depends(get_db)):
    """
    Get the current patient's assigned doctor.

    Returns null if no doctor is assigned.
    """
    if not patient.primary_doctor_id:
        return None

    result = await db.execute(select(Doctor).where(Doctor.id == patient.primary_doctor_id))
    doctor = result.scalar_one_or_none()

    if not doctor:
        return None

    return DoctorPublicInfo(id=doctor.id, full_name=doctor.full_name, specialty=doctor.specialty)


@router.delete("/patient/disconnect-doctor", response_model=ConnectionRequestStatusResponse)
async def disconnect_from_doctor(patient: Patient = Depends(get_current_patient), db: AsyncSession = Depends(get_db)):
    """
    Disconnect from the current doctor.

    Sets primary_doctor_id to NULL. The doctor will no longer have access to the patient's data.
    Historical data remains intact.
    """
    if not patient.primary_doctor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not connected to any doctor",
        )

    patient.primary_doctor_id = None
    await db.commit()

    return ConnectionRequestStatusResponse(
        status="disconnected",
        request_id="",
        message="You have been disconnected from your doctor",
    )


# ========== Doctor Profile Endpoints ==========


@router.get("/doctor/profile", response_model=DoctorResponse)
async def get_doctor_profile(doctor: Doctor = Depends(get_current_doctor), db: AsyncSession = Depends(get_db)):
    """
    Get the current doctor's profile.
    """
    return doctor


@router.put("/doctor/profile", response_model=DoctorResponse)
async def update_doctor_profile(
    request: DoctorUpdate,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Update the current doctor's profile.

    Only provided fields will be updated.
    """
    update_data = request.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(doctor, field, value)

    await db.commit()
    await db.refresh(doctor)

    return doctor


@router.get("/patient/my-doctor/profile", response_model=Optional[DoctorPublicProfile])
async def get_patient_doctor_profile(
    patient: Patient = Depends(get_current_patient), db: AsyncSession = Depends(get_db)
):
    """
    Get the full profile of the patient's assigned doctor.

    Returns null if no doctor is assigned.
    """
    if not patient.primary_doctor_id:
        return None

    result = await db.execute(select(Doctor).where(Doctor.id == patient.primary_doctor_id))
    doctor = result.scalar_one_or_none()

    if not doctor:
        return None

    return DoctorPublicProfile(
        id=doctor.id,
        first_name=doctor.first_name,
        last_name=doctor.last_name,
        full_name=doctor.full_name,
        specialty=doctor.specialty,
        phone=doctor.phone,
        bio=doctor.bio,
        years_of_experience=doctor.years_of_experience,
        education=doctor.education,
        languages=doctor.languages,
        clinic_name=doctor.clinic_name,
        clinic_address=doctor.clinic_address,
        clinic_city=doctor.clinic_city,
        clinic_country=doctor.clinic_country,
        consultation_hours=doctor.consultation_hours,
    )


# ========== Doctor Create Patient Endpoints ==========


@router.post("/doctor/patients", response_model=DoctorCreatePatientResponse)
async def create_patient_by_doctor(
    request: DoctorCreatePatient,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new patient account by a doctor.

    This endpoint allows doctors to create patient accounts for their patients,
    typically used in clinic/offline scenarios where patients may not register themselves.

    The patient will be created with:
    - A default password (configured in settings)
    - password_must_change flag set to True
    - Automatically connected to the creating doctor

    Returns the patient details including the default password for the doctor to share.
    """
    # Check if email already exists
    existing_user = await db.execute(select(User).where(func.lower(User.email) == func.lower(request.email)))
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists",
        )

    # Create the User account with default password
    default_password = settings.DEFAULT_PATIENT_PASSWORD
    user = User(
        email=request.email.lower(),
        password_hash=hash_password(default_password),
        user_type=UserType.PATIENT,
        is_active=True,
        password_must_change=True,
        created_by_doctor_id=doctor.id,
    )
    db.add(user)
    await db.flush()  # Get user.id without committing

    # Create the Patient profile with all provided information
    patient = Patient(
        user_id=user.id,
        first_name=request.first_name,
        last_name=request.last_name,
        date_of_birth=request.date_of_birth,
        gender=request.gender,
        phone=request.phone,
        address=request.address,
        city=request.city,
        country=request.country,
        preferred_language=request.preferred_language,
        emergency_contact=request.emergency_contact,
        emergency_phone=request.emergency_phone,
        emergency_contact_relationship=request.emergency_contact_relationship,
        current_medications=request.current_medications,
        medical_conditions=request.medical_conditions,
        allergies=request.allergies,
        therapy_history=request.therapy_history,
        mental_health_goals=request.mental_health_goals,
        support_system=request.support_system,
        triggers_notes=request.triggers_notes,
        coping_strategies=request.coping_strategies,
        primary_doctor_id=doctor.id,  # Automatically connect to creating doctor
        consent_signed=False,
    )
    db.add(patient)

    # Create message thread for doctor-patient communication
    message_thread = DoctorPatientThread(doctor_id=doctor.id, patient_id=patient.id)
    db.add(message_thread)

    await db.commit()
    await db.refresh(patient)

    # Send invitation email to the patient
    try:
        from app.services.email.email_senders import send_patient_invitation_email

        await send_patient_invitation_email(
            db=db,
            patient=patient,
            doctor=doctor,
            user=user,
            temp_password=default_password,
        )
    except Exception as e:
        # Log but don't fail the request if email fails
        import logging

        logging.error(f"Failed to send patient invitation email: {e}")

    return DoctorCreatePatientResponse(
        patient_id=patient.id,
        user_id=user.id,
        email=user.email,
        full_name=patient.full_name,
        default_password=default_password,
        message="Patient account created successfully. An invitation email has been sent to the patient.",
    )


# ========== Doctor AI Chat Endpoints ==========


@router.post("/doctor/patients/{patient_id}/ai-chat", response_model=DoctorAIChatResponse)
async def doctor_ai_chat(
    patient_id: str,
    request: DoctorAIChatRequest,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to the AI assistant about a specific patient.

    The AI has access to the patient's comprehensive data including:
    - Patient profile and medical records
    - Daily check-ins and mood/sleep patterns
    - Clinical assessments (PHQ-9, GAD-7, PCL-5)
    - AI conversation history
    - Risk events

    The doctor can ask questions like:
    - "Analyze this patient's mood trends over the past 2 weeks"
    - "What risk factors should I be aware of?"
    - "Summarize the patient's recent activities"

    Set conversation_id to continue an existing conversation.
    """
    from app.services.ai.doctor_chat_engine import DoctorChatEngine

    try:
        chat_engine = DoctorChatEngine(db)
        result = await chat_engine.chat(
            doctor_id=doctor.id,
            patient_id=patient_id,
            message=request.message,
            conversation_id=request.conversation_id,
        )

        return DoctorAIChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"],
            patient_name=result["patient_name"],
        )

    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        print(f"Doctor AI chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request",
        )


@router.get(
    "/doctor/patients/{patient_id}/ai-conversations",
    response_model=List[DoctorConversationListItem],
)
async def get_patient_ai_conversations(
    patient_id: str,
    limit: int = Query(10, ge=1, le=50),
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI conversation history for a specific patient.

    Returns a list of conversations ordered by most recent first.
    """
    from app.services.ai.doctor_chat_engine import DoctorChatEngine

    # Verify patient belongs to doctor
    patient_result = await db.execute(
        select(Patient).where(and_(Patient.id == patient_id, Patient.primary_doctor_id == doctor.id))
    )
    patient = patient_result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this patient",
        )

    chat_engine = DoctorChatEngine(db)
    conversations = await chat_engine.get_conversations(
        doctor_id=doctor.id,
        patient_id=patient_id,
        limit=limit,
    )

    return [
        DoctorConversationListItem(
            id=conv.id,
            patient_id=conv.patient_id,
            patient_name=patient.full_name,
            message_count=len(conv.messages),
            summary=conv.summary,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
        )
        for conv in conversations
    ]


@router.get(
    "/doctor/patients/{patient_id}/ai-conversations/{conversation_id}",
    response_model=DoctorConversationResponse,
)
async def get_ai_conversation_detail(
    patient_id: str,
    conversation_id: str,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the full detail of a specific AI conversation.

    Includes all messages in the conversation.
    """
    from app.models.doctor_conversation import DoctorConversation

    # Verify patient belongs to doctor
    patient_result = await db.execute(
        select(Patient).where(and_(Patient.id == patient_id, Patient.primary_doctor_id == doctor.id))
    )
    patient = patient_result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this patient",
        )

    # Get conversation
    result = await db.execute(
        select(DoctorConversation).where(
            and_(
                DoctorConversation.id == conversation_id,
                DoctorConversation.doctor_id == doctor.id,
                DoctorConversation.patient_id == patient_id,
            )
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    return DoctorConversationResponse(
        id=conversation.id,
        doctor_id=conversation.doctor_id,
        patient_id=conversation.patient_id,
        patient_name=patient.full_name,
        messages=[DoctorConversationMessage(role=m["role"], content=m["content"]) for m in conversation.messages],
        summary=conversation.summary,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.post("/doctor/patients/{patient_id}/ai-conversations/{conversation_id}/summarize")
async def summarize_ai_conversation(
    patient_id: str,
    conversation_id: str,
    doctor: Doctor = Depends(get_current_doctor),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate or update a summary for an AI conversation.

    Returns the generated summary.
    """
    from app.models.doctor_conversation import DoctorConversation
    from app.services.ai.doctor_chat_engine import DoctorChatEngine

    # Verify patient belongs to doctor
    patient_result = await db.execute(
        select(Patient).where(and_(Patient.id == patient_id, Patient.primary_doctor_id == doctor.id))
    )
    if not patient_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this patient",
        )

    # Get conversation
    result = await db.execute(
        select(DoctorConversation).where(
            and_(
                DoctorConversation.id == conversation_id,
                DoctorConversation.doctor_id == doctor.id,
                DoctorConversation.patient_id == patient_id,
            )
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    chat_engine = DoctorChatEngine(db)
    summary = await chat_engine.generate_conversation_summary(conversation)

    return {"summary": summary}
