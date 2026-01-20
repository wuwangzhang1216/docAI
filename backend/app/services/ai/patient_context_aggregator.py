"""Patient context aggregator for doctor AI conversations.

Aggregates all patient data (profile, check-ins, assessments, conversations,
risk events) into a comprehensive context for doctor-AI discussions.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assessment, AssessmentType, SeverityLevel
from app.models.checkin import DailyCheckin
from app.models.clinical_note import ClinicalNote
from app.models.conversation import Conversation
from app.models.patient import Patient
from app.models.risk_event import RiskEvent, RiskLevel


@dataclass
class PatientFullContext:
    """Complete patient context for doctor AI conversations."""

    patient: Patient
    checkins: List[DailyCheckin]
    assessments: List[Assessment]
    conversations: List[Conversation]
    risk_events: List[RiskEvent]
    clinical_notes: List[ClinicalNote]

    # Computed statistics
    mood_stats: Dict[str, Any]
    sleep_stats: Dict[str, Any]
    assessment_summary: Dict[str, Any]
    risk_summary: Dict[str, Any]


class PatientContextAggregator:
    """
    Aggregates all patient data for comprehensive doctor AI context.

    This class gathers and processes patient information from multiple sources
    to provide a complete picture for the doctor's AI assistant.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_full_context(self, patient_id: str, days_back: int = 30) -> PatientFullContext:
        """
        Get complete patient context for the specified time period.

        Args:
            patient_id: The patient's ID
            days_back: Number of days to look back for data

        Returns:
            PatientFullContext with all aggregated data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Fetch patient profile
        patient = await self._get_patient(patient_id)
        if not patient:
            raise ValueError(f"Patient not found: {patient_id}")

        # Fetch all related data in parallel-style queries
        checkins = await self._get_checkins(patient_id, cutoff_date)
        assessments = await self._get_assessments(patient_id, cutoff_date)
        conversations = await self._get_conversations(patient_id, cutoff_date)
        risk_events = await self._get_risk_events(patient_id, cutoff_date)
        clinical_notes = await self._get_clinical_notes(patient_id, cutoff_date)

        # Compute statistics
        mood_stats = self._compute_mood_stats(checkins)
        sleep_stats = self._compute_sleep_stats(checkins)
        assessment_summary = self._compute_assessment_summary(assessments)
        risk_summary = self._compute_risk_summary(risk_events)

        return PatientFullContext(
            patient=patient,
            checkins=checkins,
            assessments=assessments,
            conversations=conversations,
            risk_events=risk_events,
            clinical_notes=clinical_notes,
            mood_stats=mood_stats,
            sleep_stats=sleep_stats,
            assessment_summary=assessment_summary,
            risk_summary=risk_summary,
        )

    async def _get_patient(self, patient_id: str) -> Optional[Patient]:
        """Fetch patient profile."""
        result = await self.db.execute(select(Patient).where(Patient.id == patient_id))
        return result.scalar_one_or_none()

    async def _get_checkins(self, patient_id: str, cutoff_date: datetime) -> List[DailyCheckin]:
        """Fetch recent check-ins."""
        result = await self.db.execute(
            select(DailyCheckin)
            .where(
                and_(
                    DailyCheckin.patient_id == patient_id,
                    DailyCheckin.created_at >= cutoff_date,
                )
            )
            .order_by(desc(DailyCheckin.checkin_date))
        )
        return list(result.scalars().all())

    async def _get_assessments(self, patient_id: str, cutoff_date: datetime) -> List[Assessment]:
        """Fetch recent assessments."""
        result = await self.db.execute(
            select(Assessment)
            .where(
                and_(
                    Assessment.patient_id == patient_id,
                    Assessment.created_at >= cutoff_date,
                )
            )
            .order_by(desc(Assessment.created_at))
        )
        return list(result.scalars().all())

    async def _get_conversations(self, patient_id: str, cutoff_date: datetime) -> List[Conversation]:
        """Fetch recent conversations."""
        result = await self.db.execute(
            select(Conversation)
            .where(
                and_(
                    Conversation.patient_id == patient_id,
                    Conversation.created_at >= cutoff_date,
                )
            )
            .order_by(desc(Conversation.created_at))
            .limit(10)  # Limit to last 10 conversations
        )
        return list(result.scalars().all())

    async def _get_risk_events(self, patient_id: str, cutoff_date: datetime) -> List[RiskEvent]:
        """Fetch recent risk events."""
        result = await self.db.execute(
            select(RiskEvent)
            .where(
                and_(
                    RiskEvent.patient_id == patient_id,
                    RiskEvent.created_at >= cutoff_date,
                )
            )
            .order_by(desc(RiskEvent.created_at))
        )
        return list(result.scalars().all())

    async def _get_clinical_notes(self, patient_id: str, cutoff_date: datetime) -> List[ClinicalNote]:
        """Fetch recent clinical notes."""
        result = await self.db.execute(
            select(ClinicalNote)
            .where(
                and_(
                    ClinicalNote.patient_id == patient_id,
                    ClinicalNote.created_at >= cutoff_date,
                )
            )
            .order_by(desc(ClinicalNote.created_at))
            .limit(5)  # Limit to last 5 notes
        )
        return list(result.scalars().all())

    def _compute_mood_stats(self, checkins: List[DailyCheckin]) -> Dict[str, Any]:
        """Compute mood statistics from check-ins."""
        if not checkins:
            return {"has_data": False}

        mood_scores = [c.mood_score for c in checkins if c.mood_score is not None]
        if not mood_scores:
            return {"has_data": False}

        avg_mood = sum(mood_scores) / len(mood_scores)
        min_mood = min(mood_scores)
        max_mood = max(mood_scores)

        # Calculate trend (comparing first half to second half)
        trend = "stable"
        if len(mood_scores) >= 4:
            mid = len(mood_scores) // 2
            recent_avg = sum(mood_scores[:mid]) / mid
            older_avg = sum(mood_scores[mid:]) / (len(mood_scores) - mid)
            if recent_avg > older_avg + 0.5:
                trend = "improving"
            elif recent_avg < older_avg - 0.5:
                trend = "declining"

        return {
            "has_data": True,
            "average": round(avg_mood, 2),
            "min": min_mood,
            "max": max_mood,
            "trend": trend,
            "data_points": len(mood_scores),
            "low_mood_days": sum(1 for m in mood_scores if m <= 3),
        }

    def _compute_sleep_stats(self, checkins: List[DailyCheckin]) -> Dict[str, Any]:
        """Compute sleep statistics from check-ins."""
        if not checkins:
            return {"has_data": False}

        sleep_hours = [c.sleep_hours for c in checkins if c.sleep_hours is not None]
        sleep_quality = [c.sleep_quality for c in checkins if c.sleep_quality is not None]

        if not sleep_hours:
            return {"has_data": False}

        avg_hours = sum(sleep_hours) / len(sleep_hours)
        avg_quality = sum(sleep_quality) / len(sleep_quality) if sleep_quality else None

        return {
            "has_data": True,
            "average_hours": round(avg_hours, 1),
            "average_quality": round(avg_quality, 1) if avg_quality else None,
            "insufficient_sleep_days": sum(1 for h in sleep_hours if h < 6),
            "data_points": len(sleep_hours),
        }

    def _compute_assessment_summary(self, assessments: List[Assessment]) -> Dict[str, Any]:
        """Compute assessment summary."""
        if not assessments:
            return {"has_data": False}

        # Group by type and get latest
        latest_by_type: Dict[AssessmentType, Assessment] = {}
        for a in assessments:
            if a.assessment_type not in latest_by_type:
                latest_by_type[a.assessment_type] = a

        summary = {"has_data": True, "assessments": {}}

        severity_order = {
            SeverityLevel.MINIMAL: 0,
            SeverityLevel.MILD: 1,
            SeverityLevel.MODERATE: 2,
            SeverityLevel.MODERATELY_SEVERE: 3,
            SeverityLevel.SEVERE: 4,
        }

        for atype, assessment in latest_by_type.items():
            summary["assessments"][atype.value] = {
                "score": assessment.total_score,
                "severity": assessment.severity.value if assessment.severity else None,
                "date": assessment.created_at.isoformat(),
                "risk_flags": assessment.risk_flags,
            }

        # Overall severity (highest among all)
        if latest_by_type:
            max_severity = max(
                (a.severity for a in latest_by_type.values() if a.severity),
                key=lambda s: severity_order.get(s, 0),
                default=None,
            )
            summary["overall_severity"] = max_severity.value if max_severity else None

        return summary

    def _compute_risk_summary(self, risk_events: List[RiskEvent]) -> Dict[str, Any]:
        """Compute risk event summary."""
        if not risk_events:
            return {"has_data": False, "total_events": 0}

        unreviewed = [e for e in risk_events if not e.doctor_reviewed]
        critical_high = [e for e in risk_events if e.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]]

        return {
            "has_data": True,
            "total_events": len(risk_events),
            "unreviewed_count": len(unreviewed),
            "critical_high_count": len(critical_high),
            "latest_event": (
                {
                    "level": risk_events[0].risk_level.value,
                    "type": (risk_events[0].risk_type.value if risk_events[0].risk_type else None),
                    "date": risk_events[0].created_at.isoformat(),
                }
                if risk_events
                else None
            ),
        }

    def build_context_prompt(self, context: PatientFullContext) -> str:
        """
        Build a comprehensive context prompt for the AI.

        Args:
            context: The aggregated patient context

        Returns:
            A formatted string to include in the AI system prompt
        """
        patient = context.patient
        sections = []

        # Patient Profile Section
        profile_lines = [
            f"## Patient Profile",
            f"- Name: {patient.full_name}",
        ]
        if patient.date_of_birth:
            age = (datetime.utcnow().date() - patient.date_of_birth).days // 365
            profile_lines.append(f"- Age: {age} years old")
        if patient.gender:
            profile_lines.append(f"- Gender: {patient.gender}")
        if patient.preferred_language:
            profile_lines.append(f"- Preferred Language: {patient.preferred_language}")

        # Medical background
        if patient.medical_conditions:
            profile_lines.append(f"- Medical Conditions: {patient.medical_conditions}")
        if patient.current_medications:
            profile_lines.append(f"- Current Medications: {patient.current_medications}")
        if patient.allergies:
            profile_lines.append(f"- Allergies: {patient.allergies}")

        # Mental health context
        if patient.therapy_history:
            profile_lines.append(f"- Therapy History: {patient.therapy_history}")
        if patient.mental_health_goals:
            profile_lines.append(f"- Mental Health Goals: {patient.mental_health_goals}")
        if patient.triggers_notes:
            profile_lines.append(f"- Known Triggers: {patient.triggers_notes}")
        if patient.coping_strategies:
            profile_lines.append(f"- Coping Strategies: {patient.coping_strategies}")
        if patient.support_system:
            profile_lines.append(f"- Support System: {patient.support_system}")

        sections.append("\n".join(profile_lines))

        # Mood & Sleep Statistics
        if context.mood_stats.get("has_data"):
            mood = context.mood_stats
            mood_lines = [
                f"## Recent Mood Patterns (Last 30 Days)",
                f"- Average Mood: {mood['average']}/10",
                f"- Range: {mood['min']} - {mood['max']}",
                f"- Trend: {mood['trend']}",
                f"- Days with Low Mood (≤3): {mood['low_mood_days']}",
            ]
            sections.append("\n".join(mood_lines))

        if context.sleep_stats.get("has_data"):
            sleep = context.sleep_stats
            sleep_lines = [
                f"## Recent Sleep Patterns",
                f"- Average Sleep: {sleep['average_hours']} hours/night",
            ]
            if sleep.get("average_quality"):
                sleep_lines.append(f"- Average Quality: {sleep['average_quality']}/5")
            sleep_lines.append(f"- Days with Insufficient Sleep (<6h): {sleep['insufficient_sleep_days']}")
            sections.append("\n".join(sleep_lines))

        # Assessment Summary
        if context.assessment_summary.get("has_data"):
            assess = context.assessment_summary
            assess_lines = ["## Recent Assessment Results"]

            assessment_names = {
                "PHQ9": "Depression (PHQ-9)",
                "GAD7": "Anxiety (GAD-7)",
                "PCL5": "PTSD (PCL-5)",
                "PSS": "Stress (PSS)",
                "ISI": "Insomnia (ISI)",
            }

            for atype, data in assess.get("assessments", {}).items():
                name = assessment_names.get(atype, atype)
                assess_lines.append(f"- {name}: Score {data['score']}, Severity: {data['severity']}")
                if data.get("risk_flags"):
                    flags = data["risk_flags"]
                    if isinstance(flags, dict):
                        flag_str = ", ".join(f"{k}" for k, v in flags.items() if v)
                        if flag_str:
                            assess_lines.append(f"  Risk Flags: {flag_str}")

            if assess.get("overall_severity"):
                assess_lines.append(f"- Overall Severity Level: {assess['overall_severity']}")

            sections.append("\n".join(assess_lines))

        # Risk Events Summary
        if context.risk_summary.get("has_data"):
            risk = context.risk_summary
            risk_lines = [
                f"## Risk Events Summary",
                f"- Total Events (30 days): {risk['total_events']}",
                f"- Unreviewed: {risk['unreviewed_count']}",
                f"- Critical/High Risk Events: {risk['critical_high_count']}",
            ]
            if risk.get("latest_event"):
                latest = risk["latest_event"]
                risk_lines.append(f"- Most Recent: {latest['level']} ({latest['type'] or 'unspecified'})")
            sections.append("\n".join(risk_lines))

        # Recent Conversation Themes
        if context.conversations:
            conv_summaries = [c.summary for c in context.conversations if c.summary][:3]
            if conv_summaries:
                conv_lines = ["## Recent Conversation Themes"]
                for i, summary in enumerate(conv_summaries, 1):
                    conv_lines.append(f"{i}. {summary[:200]}...")
                sections.append("\n".join(conv_lines))

        # Recent Check-in Notes
        recent_notes = [c.notes for c in context.checkins[:5] if c.notes and len(c.notes.strip()) > 10]
        if recent_notes:
            notes_lines = ["## Recent Check-in Notes"]
            for note in recent_notes[:3]:
                notes_lines.append(f"- \"{note[:150]}{'...' if len(note) > 150 else ''}\"")
            sections.append("\n".join(notes_lines))

        return "\n\n".join(sections)
