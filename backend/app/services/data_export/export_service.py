"""
Data export service for patient data portability.
"""

import csv
import hashlib
import io
import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from zipfile import ZipFile

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assessment
from app.models.checkin import DailyCheckin
from app.models.conversation import Conversation
from app.models.data_export import DataExportRequest, ExportFormat, ExportStatus
from app.models.messaging import DirectMessage, DoctorPatientThread
from app.models.patient import Patient

logger = logging.getLogger(__name__)


class DataExportService:
    """Service for handling patient data exports."""

    # Rate limiting: 1 export per 24 hours
    EXPORT_COOLDOWN_HOURS = 24

    # Download link expiration: 7 days
    DOWNLOAD_EXPIRY_DAYS = 7

    async def can_request_export(
        self,
        db: AsyncSession,
        patient_id: str,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if patient can request a new export.

        Returns:
            Tuple of (can_request, reason_if_not)
        """
        # Check for recent export requests
        cutoff = datetime.utcnow() - timedelta(hours=self.EXPORT_COOLDOWN_HOURS)

        result = await db.execute(
            select(DataExportRequest)
            .where(
                and_(
                    DataExportRequest.patient_id == patient_id,
                    DataExportRequest.created_at > cutoff,
                    DataExportRequest.status.in_(
                        [
                            ExportStatus.PENDING.value,
                            ExportStatus.PROCESSING.value,
                            ExportStatus.COMPLETED.value,
                        ]
                    ),
                )
            )
            .order_by(DataExportRequest.created_at.desc())
            .limit(1)
        )
        recent_request = result.scalar_one_or_none()

        if recent_request:
            if recent_request.is_processing:
                return False, "您已有一个正在处理的导出请求"

            next_allowed = recent_request.created_at + timedelta(hours=self.EXPORT_COOLDOWN_HOURS)
            if datetime.utcnow() < next_allowed:
                hours_remaining = (next_allowed - datetime.utcnow()).seconds // 3600 + 1
                return False, f"请在 {hours_remaining} 小时后再请求导出"

        return True, None

    async def create_export_request(
        self,
        db: AsyncSession,
        patient_id: str,
        export_format: str,
        include_profile: bool = True,
        include_checkins: bool = True,
        include_assessments: bool = True,
        include_conversations: bool = True,
        include_messages: bool = True,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        request_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> DataExportRequest:
        """Create a new data export request."""
        # Create request
        export_request = DataExportRequest(
            patient_id=patient_id,
            export_format=export_format,
            include_profile=include_profile,
            include_checkins=include_checkins,
            include_assessments=include_assessments,
            include_conversations=include_conversations,
            include_messages=include_messages,
            date_from=date_from,
            date_to=date_to,
            request_ip=request_ip,
            user_agent=user_agent,
        )

        db.add(export_request)
        await db.commit()
        await db.refresh(export_request)

        logger.info(f"Created export request {export_request.id} for patient {patient_id}")

        return export_request

    async def process_export(
        self,
        db: AsyncSession,
        export_request_id: str,
    ) -> DataExportRequest:
        """
        Process an export request and generate the export file.

        This is designed to be called directly (synchronously) for now.
        Can be adapted to run in a background worker later.
        """
        # Get export request
        result = await db.execute(select(DataExportRequest).where(DataExportRequest.id == export_request_id))
        export_request = result.scalar_one_or_none()

        if not export_request:
            raise ValueError(f"Export request not found: {export_request_id}")

        # Update status to processing
        export_request.status = ExportStatus.PROCESSING.value
        export_request.processing_started_at = datetime.utcnow()
        await db.commit()

        try:
            # Collect data
            data = await self._collect_patient_data(db, export_request)
            export_request.progress_percent = 50
            await db.commit()

            # Generate file based on format
            if export_request.export_format == ExportFormat.JSON.value:
                file_content, file_name = self._generate_json(data, export_request.patient_id)
            elif export_request.export_format == ExportFormat.CSV.value:
                file_content, file_name = self._generate_csv(data, export_request.patient_id)
            else:  # PDF_SUMMARY
                file_content, file_name = self._generate_pdf_summary(data, export_request.patient_id)

            export_request.progress_percent = 80
            await db.commit()

            # Calculate checksum
            file_checksum = hashlib.sha256(file_content).hexdigest()

            # For now, store file data directly (in production, upload to S3)
            # This is a simplified implementation - real implementation would use S3
            s3_key = f"exports/{export_request.patient_id}/{export_request.id}/{file_name}"

            # Generate download token
            download_token = secrets.token_urlsafe(32)

            # Update export request
            export_request.status = ExportStatus.COMPLETED.value
            export_request.progress_percent = 100
            export_request.s3_key = s3_key
            export_request.file_size_bytes = len(file_content)
            export_request.file_checksum = file_checksum
            export_request.download_token = download_token
            export_request.download_expires_at = datetime.utcnow() + timedelta(days=self.DOWNLOAD_EXPIRY_DAYS)
            export_request.completed_at = datetime.utcnow()

            await db.commit()
            await db.refresh(export_request)

            logger.info(f"Export completed: {export_request.id}, size: {len(file_content)} bytes")

            # Store file content temporarily (in real implementation, this goes to S3)
            # For now we'll need a simple file storage solution
            self._store_file(s3_key, file_content)

            return export_request

        except Exception as e:
            logger.error(f"Export failed for {export_request_id}: {e}")
            export_request.status = ExportStatus.FAILED.value
            export_request.error_message = str(e)
            await db.commit()
            raise

    async def _collect_patient_data(
        self,
        db: AsyncSession,
        export_request: DataExportRequest,
    ) -> Dict[str, Any]:
        """Collect all requested patient data."""
        data: Dict[str, Any] = {
            "export_info": {
                "export_id": export_request.id,
                "patient_id": export_request.patient_id,
                "export_format": export_request.export_format,
                "exported_at": datetime.utcnow().isoformat(),
                "date_range": {
                    "from": (export_request.date_from.isoformat() if export_request.date_from else None),
                    "to": (export_request.date_to.isoformat() if export_request.date_to else None),
                },
            }
        }

        patient_id = export_request.patient_id

        # Profile
        if export_request.include_profile:
            result = await db.execute(select(Patient).where(Patient.id == patient_id))
            patient = result.scalar_one_or_none()
            if patient:
                data["profile"] = {
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "date_of_birth": (patient.date_of_birth.isoformat() if patient.date_of_birth else None),
                    "gender": patient.gender,
                    "phone": patient.phone,
                    "address": patient.address,
                    "city": patient.city,
                    "country": patient.country,
                    "preferred_language": patient.preferred_language,
                    "emergency_contact": patient.emergency_contact,
                    "emergency_phone": patient.emergency_phone,
                    "emergency_contact_relationship": patient.emergency_contact_relationship,
                    "current_medications": patient.current_medications,
                    "medical_conditions": patient.medical_conditions,
                    "allergies": patient.allergies,
                    "therapy_history": patient.therapy_history,
                    "mental_health_goals": patient.mental_health_goals,
                    "support_system": patient.support_system,
                    "created_at": (patient.created_at.isoformat() if patient.created_at else None),
                }

        # Checkins
        if export_request.include_checkins:
            query = select(DailyCheckin).where(DailyCheckin.patient_id == patient_id)
            if export_request.date_from:
                query = query.where(DailyCheckin.created_at >= export_request.date_from)
            if export_request.date_to:
                query = query.where(DailyCheckin.created_at <= export_request.date_to)
            query = query.order_by(DailyCheckin.checkin_date.desc())

            result = await db.execute(query)
            checkins = result.scalars().all()
            data["checkins"] = [
                {
                    "id": c.id,
                    "checkin_date": (c.checkin_date.isoformat() if c.checkin_date else None),
                    "mood_score": c.mood_score,
                    "sleep_hours": c.sleep_hours,
                    "sleep_quality": c.sleep_quality,
                    "medication_taken": c.medication_taken,
                    "notes": c.notes,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in checkins
            ]

        # Assessments
        if export_request.include_assessments:
            query = select(Assessment).where(Assessment.patient_id == patient_id)
            if export_request.date_from:
                query = query.where(Assessment.created_at >= export_request.date_from)
            if export_request.date_to:
                query = query.where(Assessment.created_at <= export_request.date_to)
            query = query.order_by(Assessment.created_at.desc())

            result = await db.execute(query)
            assessments = result.scalars().all()
            data["assessments"] = [
                {
                    "id": a.id,
                    "assessment_type": a.assessment_type,
                    "total_score": a.total_score,
                    "severity": a.severity,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in assessments
            ]

        # Conversations (AI chat)
        if export_request.include_conversations:
            query = select(Conversation).where(Conversation.patient_id == patient_id)
            if export_request.date_from:
                query = query.where(Conversation.created_at >= export_request.date_from)
            if export_request.date_to:
                query = query.where(Conversation.created_at <= export_request.date_to)
            query = query.order_by(Conversation.created_at.desc())

            result = await db.execute(query)
            conversations = result.scalars().all()
            data["ai_conversations"] = [
                {
                    "id": c.id,
                    "conversation_type": c.conversation_type,
                    "started_at": c.created_at.isoformat() if c.created_at else None,
                    "ended_at": c.ended_at.isoformat() if c.ended_at else None,
                    "message_count": c.message_count,
                }
                for c in conversations
            ]

        # Direct messages with doctor
        if export_request.include_messages:
            # First get threads
            thread_result = await db.execute(
                select(DoctorPatientThread).where(DoctorPatientThread.patient_id == patient_id)
            )
            threads = thread_result.scalars().all()

            thread_ids = [t.id for t in threads]
            if thread_ids:
                query = select(DirectMessage).where(DirectMessage.thread_id.in_(thread_ids))
                if export_request.date_from:
                    query = query.where(DirectMessage.created_at >= export_request.date_from)
                if export_request.date_to:
                    query = query.where(DirectMessage.created_at <= export_request.date_to)
                query = query.order_by(DirectMessage.created_at.asc())

                msg_result = await db.execute(query)
                messages = msg_result.scalars().all()
                data["doctor_messages"] = [
                    {
                        "id": m.id,
                        "sender_type": m.sender_type,
                        "content": m.content,
                        "message_type": m.message_type,
                        "created_at": (m.created_at.isoformat() if m.created_at else None),
                    }
                    for m in messages
                ]
            else:
                data["doctor_messages"] = []

        return data

    def _generate_json(self, data: Dict[str, Any], patient_id: str) -> tuple[bytes, str]:
        """Generate JSON export file."""
        content = json.dumps(data, ensure_ascii=False, indent=2)
        file_name = f"export_{patient_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        return content.encode("utf-8"), file_name

    def _generate_csv(self, data: Dict[str, Any], patient_id: str) -> tuple[bytes, str]:
        """Generate CSV export as a ZIP file containing multiple CSVs."""
        zip_buffer = io.BytesIO()

        with ZipFile(zip_buffer, "w") as zip_file:
            # Export info
            zip_file.writestr(
                "export_info.json",
                json.dumps(data.get("export_info", {}), ensure_ascii=False, indent=2),
            )

            # Profile
            if "profile" in data:
                profile_csv = io.StringIO()
                writer = csv.DictWriter(profile_csv, fieldnames=data["profile"].keys())
                writer.writeheader()
                writer.writerow(data["profile"])
                zip_file.writestr("profile.csv", profile_csv.getvalue())

            # Checkins
            if "checkins" in data and data["checkins"]:
                checkins_csv = io.StringIO()
                writer = csv.DictWriter(checkins_csv, fieldnames=data["checkins"][0].keys())
                writer.writeheader()
                writer.writerows(data["checkins"])
                zip_file.writestr("checkins.csv", checkins_csv.getvalue())

            # Assessments
            if "assessments" in data and data["assessments"]:
                assessments_csv = io.StringIO()
                writer = csv.DictWriter(assessments_csv, fieldnames=data["assessments"][0].keys())
                writer.writeheader()
                writer.writerows(data["assessments"])
                zip_file.writestr("assessments.csv", assessments_csv.getvalue())

            # AI Conversations
            if "ai_conversations" in data and data["ai_conversations"]:
                conv_csv = io.StringIO()
                writer = csv.DictWriter(conv_csv, fieldnames=data["ai_conversations"][0].keys())
                writer.writeheader()
                writer.writerows(data["ai_conversations"])
                zip_file.writestr("ai_conversations.csv", conv_csv.getvalue())

            # Doctor Messages
            if "doctor_messages" in data and data["doctor_messages"]:
                msg_csv = io.StringIO()
                writer = csv.DictWriter(msg_csv, fieldnames=data["doctor_messages"][0].keys())
                writer.writeheader()
                writer.writerows(data["doctor_messages"])
                zip_file.writestr("doctor_messages.csv", msg_csv.getvalue())

        file_name = f"export_{patient_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
        return zip_buffer.getvalue(), file_name

    def _generate_pdf_summary(self, data: Dict[str, Any], patient_id: str) -> tuple[bytes, str]:
        """Generate a PDF summary report."""
        # For now, generate a simple text-based summary
        # In production, use reportlab or similar for proper PDF generation
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            "Title",
            parent=styles["Heading1"],
            fontSize=18,
            spaceAfter=20,
        )
        story.append(Paragraph("患者数据导出报告", title_style))
        story.append(
            Paragraph(
                f"导出时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 20))

        # Profile summary
        if "profile" in data:
            story.append(Paragraph("个人资料", styles["Heading2"]))
            profile = data["profile"]
            story.append(
                Paragraph(
                    f"姓名: {profile.get('first_name', '')} {profile.get('last_name', '')}",
                    styles["Normal"],
                )
            )
            if profile.get("date_of_birth"):
                story.append(Paragraph(f"出生日期: {profile['date_of_birth']}", styles["Normal"]))
            story.append(Spacer(1, 15))

        # Checkins summary
        if "checkins" in data:
            checkins = data["checkins"]
            story.append(Paragraph(f"打卡记录统计 (共 {len(checkins)} 条)", styles["Heading2"]))
            if checkins:
                avg_mood = sum(c.get("mood_score", 0) for c in checkins) / len(checkins)
                story.append(Paragraph(f"平均心情分数: {avg_mood:.1f}/10", styles["Normal"]))
            story.append(Spacer(1, 15))

        # Assessments summary
        if "assessments" in data:
            assessments = data["assessments"]
            story.append(Paragraph(f"评估记录 (共 {len(assessments)} 次)", styles["Heading2"]))
            story.append(Spacer(1, 15))

        # Conversations summary
        if "ai_conversations" in data:
            conversations = data["ai_conversations"]
            story.append(Paragraph(f"AI对话记录 (共 {len(conversations)} 次)", styles["Heading2"]))
            story.append(Spacer(1, 15))

        # Messages summary
        if "doctor_messages" in data:
            messages = data["doctor_messages"]
            story.append(Paragraph(f"医生消息记录 (共 {len(messages)} 条)", styles["Heading2"]))

        doc.build(story)
        file_name = f"summary_{patient_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
        return buffer.getvalue(), file_name

    def _store_file(self, s3_key: str, content: bytes) -> None:
        """
        Store file content.

        In production, this would upload to S3.
        For now, we store locally in a temporary directory.
        """
        import os

        storage_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports")
        os.makedirs(storage_dir, exist_ok=True)

        # Use export ID as filename
        file_path = os.path.join(storage_dir, s3_key.replace("/", "_"))
        with open(file_path, "wb") as f:
            f.write(content)

    def _get_file(self, s3_key: str) -> Optional[bytes]:
        """
        Retrieve file content.

        In production, this would download from S3.
        """
        import os

        storage_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "exports")
        file_path = os.path.join(storage_dir, s3_key.replace("/", "_"))

        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                return f.read()
        return None

    async def get_download_info(
        self,
        db: AsyncSession,
        download_token: str,
    ) -> Optional[tuple[DataExportRequest, bytes, str]]:
        """
        Get export file for download.

        Returns:
            Tuple of (export_request, file_content, file_name) or None
        """
        result = await db.execute(select(DataExportRequest).where(DataExportRequest.download_token == download_token))
        export_request = result.scalar_one_or_none()

        if not export_request:
            return None

        if not export_request.can_download:
            return None

        # Get file content
        file_content = self._get_file(export_request.s3_key)
        if not file_content:
            return None

        # Determine file name
        if export_request.export_format == ExportFormat.JSON.value:
            file_name = f"export_{export_request.patient_id}.json"
        elif export_request.export_format == ExportFormat.CSV.value:
            file_name = f"export_{export_request.patient_id}.zip"
        else:
            file_name = f"summary_{export_request.patient_id}.pdf"

        # Update download count
        export_request.download_count += 1
        export_request.last_downloaded_at = datetime.utcnow()

        if export_request.download_count >= export_request.max_downloads:
            export_request.status = ExportStatus.DOWNLOADED.value

        await db.commit()

        return export_request, file_content, file_name

    async def get_export_requests(
        self,
        db: AsyncSession,
        patient_id: str,
        limit: int = 10,
    ) -> List[DataExportRequest]:
        """Get export request history for a patient."""
        result = await db.execute(
            select(DataExportRequest)
            .where(DataExportRequest.patient_id == patient_id)
            .order_by(DataExportRequest.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()


# Singleton instance
export_service = DataExportService()
