"""AI Tools for hybrid context retrieval.

Provides on-demand context retrieval tools that Claude can call
when it needs specific patient/user information during conversations.

This implements the "Just-in-Time" approach recommended by Anthropic,
where we maintain lightweight identifiers and dynamically load data
into context at runtime using tools.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assessment import Assessment, AssessmentType, SeverityLevel
from app.models.checkin import DailyCheckin
from app.models.conversation import Conversation
from app.models.patient import Patient

# Tool definitions for Claude API
# These follow the Anthropic tool schema format

PATIENT_CONTEXT_TOOLS = [
    {
        "name": "get_mood_trends",
        "description": """Retrieve the user's recent mood patterns and trends.

Use this tool when:
- User mentions feeling different than usual
- User asks about their mood patterns
- You need to understand their emotional baseline
- Discussing changes in how they've been feeling

Returns: Recent mood scores, averages, trends (improving/declining/stable), and any notes.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back (default: 14, max: 30)",
                    "default": 14,
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_sleep_patterns",
        "description": """Retrieve the user's recent sleep data and patterns.

Use this tool when:
- User mentions sleep problems or fatigue
- Discussing energy levels or tiredness
- User asks about their sleep quality
- Understanding factors affecting their wellbeing

Returns: Sleep hours, quality ratings, patterns, and any sleep-related concerns.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back (default: 14, max: 30)",
                    "default": 14,
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_assessment_results",
        "description": """Retrieve the user's clinical assessment results (PHQ-9, GAD-7, PCL-5, etc.).

Use this tool when:
- User mentions specific symptoms (depression, anxiety, trauma)
- You need clinical context for the conversation
- Discussing severity of their experiences
- User asks about their assessment scores

Returns: Latest assessment scores, severity levels, and any flagged concerns.
Note: Use clinical information sensitively - don't quote scores unless user asks.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "assessment_type": {
                    "type": "string",
                    "enum": ["PHQ9", "GAD7", "PCL5", "PSS", "ISI", "all"],
                    "description": "Specific assessment type or 'all' for all recent assessments",
                    "default": "all",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_coping_strategies",
        "description": """Retrieve coping strategies that have worked for this user.

Use this tool when:
- User is struggling and needs suggestions
- Discussing what helps them feel better
- User asks for coping recommendations
- You want to remind them of helpful strategies

Returns: User's known effective coping strategies and support resources.""",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_known_triggers",
        "description": """Retrieve known triggers and sensitive topics for this user.

Use this tool when:
- Before discussing potentially sensitive topics
- User seems distressed and you want to understand why
- You need to navigate the conversation carefully
- Understanding what topics to approach gently

Returns: Known triggers, sensitive topics, and guidance for the conversation.
IMPORTANT: Use this information to be more careful, not to avoid topics entirely.""",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_recent_conversation_summary",
        "description": """Retrieve summary of recent conversations with this user.

Use this tool when:
- User references something from a previous conversation
- You need continuity context
- Understanding ongoing themes in their journey
- User says "like I mentioned before" or similar

Returns: Summaries of recent conversations and key themes discussed.""",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of recent conversations to retrieve (default: 3, max: 5)",
                    "default": 3,
                }
            },
            "required": [],
        },
    },
]


@dataclass
class ToolResult:
    """Result from a tool execution."""

    content: str
    is_error: bool = False


class PatientContextTools:
    """
    Executes context retrieval tools for patient conversations.

    This class provides the actual implementations of tools that Claude
    can call to retrieve patient context on-demand.
    """

    def __init__(self, db: AsyncSession, patient_id: str):
        """
        Initialize with database session and patient ID.

        Args:
            db: Async database session
            patient_id: The patient's ID for context retrieval
        """
        self.db = db
        self.patient_id = patient_id

    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> ToolResult:
        """
        Execute a tool by name with given input.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool

        Returns:
            ToolResult with content or error
        """
        tool_handlers = {
            "get_mood_trends": self._get_mood_trends,
            "get_sleep_patterns": self._get_sleep_patterns,
            "get_assessment_results": self._get_assessment_results,
            "get_coping_strategies": self._get_coping_strategies,
            "get_known_triggers": self._get_known_triggers,
            "get_recent_conversation_summary": self._get_recent_conversation_summary,
        }

        handler = tool_handlers.get(tool_name)
        if not handler:
            return ToolResult(content=f"Unknown tool: {tool_name}", is_error=True)

        try:
            result = await handler(tool_input)
            return ToolResult(content=result)
        except Exception as e:
            return ToolResult(content=f"Error executing {tool_name}: {str(e)}", is_error=True)

    async def _get_mood_trends(self, params: Dict[str, Any]) -> str:
        """Get recent mood trends from check-ins."""
        days = min(params.get("days", 14), 30)
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(DailyCheckin)
            .where(
                and_(
                    DailyCheckin.patient_id == self.patient_id,
                    DailyCheckin.created_at >= cutoff,
                )
            )
            .order_by(desc(DailyCheckin.checkin_date))
        )
        checkins = list(result.scalars().all())

        if not checkins:
            return "No mood data available for this period."

        mood_scores = [c.mood_score for c in checkins if c.mood_score is not None]
        if not mood_scores:
            return "No mood scores recorded in this period."

        avg_mood = sum(mood_scores) / len(mood_scores)
        min_mood = min(mood_scores)
        max_mood = max(mood_scores)
        latest_mood = mood_scores[0]

        # Calculate trend
        trend = "stable"
        if len(mood_scores) >= 4:
            mid = len(mood_scores) // 2
            recent_avg = sum(mood_scores[:mid]) / mid
            older_avg = sum(mood_scores[mid:]) / (len(mood_scores) - mid)
            if recent_avg > older_avg + 0.5:
                trend = "improving"
            elif recent_avg < older_avg - 0.5:
                trend = "declining"

        # Get recent notes
        recent_notes = [c.notes for c in checkins[:3] if c.notes and len(c.notes.strip()) > 10]

        output = f"""Mood data for the last {days} days ({len(mood_scores)} check-ins):
- Current/Latest mood: {latest_mood}/10
- Average mood: {avg_mood:.1f}/10
- Range: {min_mood} - {max_mood}
- Trend: {trend}
- Low mood days (≤3): {sum(1 for m in mood_scores if m <= 3)}"""

        if recent_notes:
            output += f"\n\nRecent notes from user:\n"
            for note in recent_notes[:2]:
                output += f"- \"{note[:150]}{'...' if len(note) > 150 else ''}\"\n"

        return output

    async def _get_sleep_patterns(self, params: Dict[str, Any]) -> str:
        """Get recent sleep patterns from check-ins."""
        days = min(params.get("days", 14), 30)
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(DailyCheckin)
            .where(
                and_(
                    DailyCheckin.patient_id == self.patient_id,
                    DailyCheckin.created_at >= cutoff,
                )
            )
            .order_by(desc(DailyCheckin.checkin_date))
        )
        checkins = list(result.scalars().all())

        if not checkins:
            return "No sleep data available for this period."

        sleep_hours = [c.sleep_hours for c in checkins if c.sleep_hours is not None]
        sleep_quality = [c.sleep_quality for c in checkins if c.sleep_quality is not None]

        if not sleep_hours:
            return "No sleep data recorded in this period."

        avg_hours = sum(sleep_hours) / len(sleep_hours)
        latest_hours = sleep_hours[0] if sleep_hours else None

        output = f"""Sleep data for the last {days} days ({len(sleep_hours)} records):
- Latest sleep: {latest_hours} hours
- Average sleep: {avg_hours:.1f} hours/night
- Days with <6 hours: {sum(1 for h in sleep_hours if h < 6)}"""

        if sleep_quality:
            avg_quality = sum(sleep_quality) / len(sleep_quality)
            quality_desc = (
                "poor"
                if avg_quality < 2
                else ("fair" if avg_quality < 3 else "moderate" if avg_quality < 4 else "good")
            )
            output += f"\n- Average sleep quality: {quality_desc} ({avg_quality:.1f}/5)"

        return output

    async def _get_assessment_results(self, params: Dict[str, Any]) -> str:
        """Get clinical assessment results."""
        assessment_type = params.get("assessment_type", "all")
        cutoff = datetime.utcnow() - timedelta(days=90)  # Last 90 days

        query = select(Assessment).where(
            and_(
                Assessment.patient_id == self.patient_id,
                Assessment.created_at >= cutoff,
            )
        )

        if assessment_type != "all":
            try:
                atype = AssessmentType(assessment_type)
                query = query.where(Assessment.assessment_type == atype)
            except ValueError:
                return f"Unknown assessment type: {assessment_type}"

        result = await self.db.execute(query.order_by(desc(Assessment.created_at)))
        assessments = list(result.scalars().all())

        if not assessments:
            return "No assessment results available."

        # Get latest of each type
        latest_by_type: Dict[AssessmentType, Assessment] = {}
        for a in assessments:
            if a.assessment_type not in latest_by_type:
                latest_by_type[a.assessment_type] = a

        assessment_names = {
            AssessmentType.PHQ9: "Depression (PHQ-9)",
            AssessmentType.GAD7: "Anxiety (GAD-7)",
            AssessmentType.PCL5: "Trauma/PTSD (PCL-5)",
            AssessmentType.PSS: "Stress (PSS)",
            AssessmentType.ISI: "Insomnia (ISI)",
        }

        severity_desc = {
            SeverityLevel.MINIMAL: "minimal",
            SeverityLevel.MILD: "mild",
            SeverityLevel.MODERATE: "moderate",
            SeverityLevel.MODERATELY_SEVERE: "moderately severe",
            SeverityLevel.SEVERE: "severe",
        }

        output = "Recent assessment results:\n"
        for atype, assessment in latest_by_type.items():
            name = assessment_names.get(atype, atype.value)
            severity = severity_desc.get(assessment.severity, "unknown")
            days_ago = (datetime.utcnow() - assessment.created_at).days
            time_desc = "today" if days_ago == 0 else f"{days_ago} days ago"

            output += f"- {name}: {severity} symptoms (score: {assessment.total_score}, {time_desc})\n"

            if assessment.risk_flags:
                flags = assessment.risk_flags
                if isinstance(flags, dict):
                    active_flags = [k for k, v in flags.items() if v]
                    if active_flags:
                        output += f"  ⚠️ Flags: {', '.join(active_flags)}\n"

        return output

    async def _get_coping_strategies(self, params: Dict[str, Any]) -> str:
        """Get user's known coping strategies."""
        result = await self.db.execute(select(Patient).where(Patient.id == self.patient_id))
        patient = result.scalar_one_or_none()

        if not patient:
            return "Unable to retrieve user profile."

        output_parts = []

        if patient.coping_strategies:
            output_parts.append(f"Coping strategies that help this user:\n{patient.coping_strategies}")

        if patient.support_system:
            output_parts.append(f"Support system:\n{patient.support_system}")

        if patient.mental_health_goals:
            output_parts.append(f"Their mental health goals:\n{patient.mental_health_goals}")

        if not output_parts:
            return "No coping strategies or support information recorded for this user."

        return "\n\n".join(output_parts)

    async def _get_known_triggers(self, params: Dict[str, Any]) -> str:
        """Get user's known triggers and sensitive topics."""
        result = await self.db.execute(select(Patient).where(Patient.id == self.patient_id))
        patient = result.scalar_one_or_none()

        if not patient:
            return "Unable to retrieve user profile."

        if not patient.triggers_notes:
            return "No specific triggers documented. Approach sensitive topics with general care for political trauma survivors."

        return f"""Known triggers and sensitive topics for this user:
{patient.triggers_notes}

Guidance: Use this information to approach topics gently, not to avoid them entirely.
The user may still benefit from discussing these areas with proper support."""

    async def _get_recent_conversation_summary(self, params: Dict[str, Any]) -> str:
        """Get summaries of recent conversations."""
        limit = min(params.get("limit", 3), 5)

        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.patient_id == self.patient_id)
            .order_by(desc(Conversation.created_at))
            .limit(limit)
        )
        conversations = list(result.scalars().all())

        if not conversations:
            return "No previous conversations found."

        output = "Recent conversation summaries:\n"
        for i, conv in enumerate(conversations, 1):
            days_ago = (datetime.utcnow() - conv.created_at).days
            time_desc = "today" if days_ago == 0 else f"{days_ago} days ago"

            if conv.summary:
                output += f"{i}. ({time_desc}): {conv.summary}\n"
            else:
                output += f"{i}. ({time_desc}): [No summary available]\n"

        return output


def get_essential_context(patient: Patient) -> str:
    """
    Build minimal essential context that is always included in the system prompt.

    This follows the hybrid approach - only critical information is injected upfront,
    while detailed context is retrieved on-demand via tools.

    Args:
        patient: Patient profile

    Returns:
        Minimal context string for system prompt
    """
    context_parts = []

    # Name for personalization (use first name)
    if patient.full_name:
        first_name = patient.full_name.split()[0]
        context_parts.append(f"User's name: {first_name}")

    # Preferred language - CRITICAL for response language
    if patient.preferred_language:
        lang_map = {
            "en": "English",
            "zh": "中文 (Chinese)",
            "fa": "فارسی (Farsi)",
            "es": "Español (Spanish)",
            "tr": "Türkçe (Turkish)",
            "ar": "العربية (Arabic)",
        }
        lang = lang_map.get(patient.preferred_language, patient.preferred_language)
        context_parts.append(f"User's preferred language: {lang}")

    if not context_parts:
        return ""

    return "\n## Essential User Context\n" + "\n".join(f"- {p}" for p in context_parts)
