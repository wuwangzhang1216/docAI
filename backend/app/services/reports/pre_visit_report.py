"""
Pre-Visit Report Service for generating clinical summary PDFs.
"""

import json
import uuid
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assessment import Assessment
from app.models.checkin import DailyCheckin
from app.models.conversation import Conversation
from app.models.doctor import Doctor
from app.models.generated_report import GeneratedReport, ReportType
from app.models.patient import Patient
from app.models.pre_visit_summary import PreVisitSummary
from app.models.risk_event import RiskEvent
from app.models.user import User
from app.schemas.reports import ReportGenerateRequest
from app.services.reports.pdf_generator import pdf_generator
from app.services.storage import storage_service


class PreVisitReportService:
    """
    Service for generating Pre-Visit Clinical Summary PDF reports.
    """

    def __init__(self):
        self.pdf_generator = pdf_generator
        self.storage = storage_service

    async def generate_report(
        self,
        db: AsyncSession,
        summary_id: str,
        generated_by: User,
        options: ReportGenerateRequest,
    ) -> Dict[str, Any]:
        """
        Generate a Pre-Visit Summary PDF report.

        Args:
            db: Database session
            summary_id: PreVisitSummary ID
            generated_by: User generating the report
            options: Report generation options

        Returns:
            Dict containing report_id, pdf_url, expires_at, generated_at

        Raises:
            ValueError: If summary not found
            PermissionError: If user doesn't have access to patient
        """
        # 1. Get PreVisitSummary with patient info
        summary = await self._get_summary(db, summary_id)
        if not summary:
            raise ValueError(f"Pre-visit summary not found: {summary_id}")

        patient = summary.patient
        if not patient:
            raise ValueError(f"Patient not found for summary: {summary_id}")

        # 2. Verify access (doctor must be assigned to patient)
        await self._verify_access(db, patient.id, generated_by.id)

        # 3. Aggregate data
        assessments = await self._get_assessments(db, patient.id, limit=5)
        risk_events = []
        if options.include_risk_events:
            risk_events = await self._get_risk_events(db, patient.id, unreviewed_only=False)

        checkin_trend = None
        if options.include_checkin_trend:
            checkin_trend = await self._get_checkin_trend(db, patient.id, days=options.days_for_trend)

        conversation_summary = None
        if summary.conversation_id:
            conversation_summary = await self._get_conversation_summary(db, summary.conversation_id)

        # 4. Build report content
        report_id = str(uuid.uuid4())[:8].upper()
        generated_at = datetime.utcnow()

        content = self._build_report_content(
            report_id=report_id,
            generated_at=generated_at,
            patient=patient,
            summary=summary,
            assessments=assessments,
            risk_events=risk_events,
            checkin_trend=checkin_trend,
            conversation_summary=conversation_summary,
        )

        # 5. Generate PDF
        pdf_bytes = self.pdf_generator.generate_pre_visit_report(content)

        # 6. Upload to S3
        s3_key = self._generate_s3_key(patient.id, report_id)
        self.storage.s3_client.put_object(
            Bucket=self.storage.bucket,
            Key=s3_key,
            Body=pdf_bytes,
            ContentType="application/pdf",
        )

        # 7. Create GeneratedReport record
        report = GeneratedReport(
            id=str(uuid.uuid4()),
            patient_id=patient.id,
            pre_visit_summary_id=summary.id,
            report_type=ReportType.PRE_VISIT_SUMMARY,
            s3_key=s3_key,
            generated_by_id=generated_by.id,
            metadata_json=json.dumps(
                {
                    "options": {
                        "include_risk_events": options.include_risk_events,
                        "include_checkin_trend": options.include_checkin_trend,
                        "days_for_trend": options.days_for_trend,
                    },
                    "report_id_display": report_id,
                }
            ),
            created_at=generated_at,
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)

        # 8. Generate presigned URL
        pdf_url = self.storage.get_presigned_url(s3_key)
        expires_at = datetime.utcnow() + timedelta(seconds=self.storage.PRESIGNED_URL_EXPIRY)

        return {
            "report_id": report.id,
            "patient_id": patient.id,
            "report_type": ReportType.PRE_VISIT_SUMMARY,
            "pdf_url": pdf_url,
            "expires_at": expires_at,
            "generated_at": generated_at,
        }

    async def get_report(self, db: AsyncSession, report_id: str, user: User) -> Optional[Dict[str, Any]]:
        """
        Get report details and refresh presigned URL.

        Args:
            db: Database session
            report_id: GeneratedReport ID
            user: User requesting the report

        Returns:
            Dict with report details or None if not found
        """
        stmt = select(GeneratedReport).where(GeneratedReport.id == report_id)
        result = await db.execute(stmt)
        report = result.scalar_one_or_none()

        if not report:
            return None

        # Verify access
        await self._verify_access(db, report.patient_id, user.id)

        # Generate fresh presigned URL
        pdf_url = self.storage.get_presigned_url(report.s3_key)
        expires_at = datetime.utcnow() + timedelta(seconds=self.storage.PRESIGNED_URL_EXPIRY)

        return {
            "report_id": report.id,
            "patient_id": report.patient_id,
            "report_type": report.report_type,
            "pdf_url": pdf_url,
            "expires_at": expires_at,
            "generated_at": report.created_at,
        }

    async def list_reports(
        self,
        db: AsyncSession,
        user: User,
        patient_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        List generated reports.

        Args:
            db: Database session
            user: User requesting the list
            patient_id: Filter by patient ID
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Dict with reports list and total count
        """
        # Build query
        stmt = select(GeneratedReport).order_by(desc(GeneratedReport.created_at))

        if patient_id:
            # Verify access to patient
            await self._verify_access(db, patient_id, user.id)
            stmt = stmt.where(GeneratedReport.patient_id == patient_id)
        else:
            # Get all patients for this doctor
            doctor_stmt = select(Doctor).where(Doctor.user_id == user.id)
            doctor_result = await db.execute(doctor_stmt)
            doctor = doctor_result.scalar_one_or_none()

            if doctor:
                patient_stmt = select(Patient.id).where(Patient.primary_doctor_id == doctor.id)
                patient_result = await db.execute(patient_stmt)
                patient_ids = [p.id for p in patient_result.fetchall()]
                stmt = stmt.where(GeneratedReport.patient_id.in_(patient_ids))

        # Count total
        count_stmt = (
            select(GeneratedReport).where(stmt.whereclause) if stmt.whereclause is not None else select(GeneratedReport)
        )
        count_result = await db.execute(count_stmt)
        total = len(count_result.scalars().all())

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)
        result = await db.execute(stmt)
        reports = result.scalars().all()

        # Fetch patient names
        report_list = []
        for report in reports:
            patient_stmt = select(Patient).where(Patient.id == report.patient_id)
            patient_result = await db.execute(patient_stmt)
            patient = patient_result.scalar_one_or_none()

            report_list.append(
                {
                    "report_id": report.id,
                    "patient_id": report.patient_id,
                    "patient_name": patient.full_name if patient else "Unknown",
                    "report_type": report.report_type,
                    "generated_at": report.created_at,
                }
            )

        return {
            "reports": report_list,
            "total": total,
        }

    async def _get_summary(self, db: AsyncSession, summary_id: str) -> Optional[PreVisitSummary]:
        """Get PreVisitSummary by ID."""
        stmt = (
            select(PreVisitSummary)
            .options(selectinload(PreVisitSummary.patient))
            .where(PreVisitSummary.id == summary_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _verify_access(self, db: AsyncSession, patient_id: str, user_id: str) -> None:
        """
        Verify user has access to patient.

        Raises:
            PermissionError: If user doesn't have access
        """
        # Get doctor by user_id
        doctor_stmt = select(Doctor).where(Doctor.user_id == user_id)
        doctor_result = await db.execute(doctor_stmt)
        doctor = doctor_result.scalar_one_or_none()

        if not doctor:
            raise PermissionError("Only doctors can generate reports")

        # Verify patient belongs to doctor
        patient_stmt = select(Patient).where(and_(Patient.id == patient_id, Patient.primary_doctor_id == doctor.id))
        patient_result = await db.execute(patient_stmt)
        patient = patient_result.scalar_one_or_none()

        if not patient:
            raise PermissionError("Patient not assigned to this doctor")

    async def _get_assessments(self, db: AsyncSession, patient_id: str, limit: int = 5) -> List[Assessment]:
        """Get recent assessments for patient."""
        stmt = (
            select(Assessment)
            .where(Assessment.patient_id == patient_id)
            .order_by(desc(Assessment.created_at))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def _get_risk_events(
        self, db: AsyncSession, patient_id: str, unreviewed_only: bool = False
    ) -> List[RiskEvent]:
        """Get risk events for patient, prioritizing high-risk."""
        stmt = (
            select(RiskEvent)
            .where(RiskEvent.patient_id == patient_id)
            .order_by(
                # Sort by risk level (CRITICAL > HIGH > MEDIUM > LOW)
                desc(RiskEvent.risk_level),
                desc(RiskEvent.created_at),
            )
            .limit(10)
        )

        if unreviewed_only:
            stmt = stmt.where(RiskEvent.doctor_reviewed == False)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def _get_checkin_trend(self, db: AsyncSession, patient_id: str, days: int = 7) -> Dict[str, Any]:
        """Calculate check-in trends for the specified period."""
        start_date = date.today() - timedelta(days=days)

        stmt = (
            select(DailyCheckin)
            .where(
                and_(
                    DailyCheckin.patient_id == patient_id,
                    DailyCheckin.checkin_date >= start_date,
                )
            )
            .order_by(desc(DailyCheckin.checkin_date))
        )
        result = await db.execute(stmt)
        checkins = list(result.scalars().all())

        if not checkins:
            return {
                "days": days,
                "checkin_count": 0,
                "avg_mood": None,
                "avg_sleep": None,
                "avg_sleep_quality": None,
            }

        # Calculate averages
        mood_scores = [c.mood_score for c in checkins if c.mood_score is not None]
        sleep_hours = [c.sleep_hours for c in checkins if c.sleep_hours is not None]
        sleep_quality = [c.sleep_quality for c in checkins if c.sleep_quality is not None]

        return {
            "days": days,
            "checkin_count": len(checkins),
            "avg_mood": sum(mood_scores) / len(mood_scores) if mood_scores else None,
            "avg_sleep": sum(sleep_hours) / len(sleep_hours) if sleep_hours else None,
            "avg_sleep_quality": (sum(sleep_quality) / len(sleep_quality) if sleep_quality else None),
        }

    async def _get_conversation_summary(self, db: AsyncSession, conversation_id: str) -> Optional[str]:
        """Get conversation summary."""
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()
        return conversation.summary if conversation else None

    def _build_report_content(
        self,
        report_id: str,
        generated_at: datetime,
        patient: Patient,
        summary: PreVisitSummary,
        assessments: List[Assessment],
        risk_events: List[RiskEvent],
        checkin_trend: Optional[Dict[str, Any]],
        conversation_summary: Optional[str],
    ) -> Dict[str, Any]:
        """Build the content dictionary for PDF generation."""
        # Calculate age
        age = None
        if patient.date_of_birth:
            today = date.today()
            age = today.year - patient.date_of_birth.year
            if (today.month, today.day) < (
                patient.date_of_birth.month,
                patient.date_of_birth.day,
            ):
                age -= 1

        # Format scheduled visit
        scheduled_visit = None
        if summary.scheduled_visit:
            scheduled_visit = summary.scheduled_visit.strftime("%Y-%m-%d")

        # Format assessments
        assessment_list = []
        for a in assessments:
            assessment_list.append(
                {
                    "type": a.assessment_type.value if a.assessment_type else "Unknown",
                    "score": a.total_score,
                    "severity": a.severity.value if a.severity else None,
                    "date": a.created_at,
                }
            )

        # Format risk events
        risk_list = []
        for r in risk_events:
            risk_list.append(
                {
                    "level": r.risk_level.value if r.risk_level else "MEDIUM",
                    "type": r.risk_type.value if r.risk_type else "OTHER",
                    "trigger_text": r.trigger_text,
                }
            )

        return {
            "report_id": report_id,
            "generated_at": generated_at,
            "patient": {
                "name": patient.full_name,
                "gender": patient.gender or "Not specified",
                "age": f"{age} years" if age else "Not specified",
                "scheduled_visit": scheduled_visit or "Not scheduled",
            },
            "chief_complaint": summary.chief_complaint,
            "assessments": assessment_list,
            "risk_events": risk_list,
            "checkin_trend": checkin_trend,
            "conversation_summary": conversation_summary,
        }

    def _generate_s3_key(self, patient_id: str, report_id: str) -> str:
        """Generate S3 key for the report."""
        timestamp = datetime.utcnow().strftime("%Y/%m/%d")
        return f"reports/pre_visit_summaries/{timestamp}/{report_id}_{patient_id[:8]}.pdf"


# Singleton instance
pre_visit_report_service = PreVisitReportService()
