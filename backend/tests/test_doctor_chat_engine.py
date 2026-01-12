"""
Unit tests for doctor chat engine and patient context aggregator.

Tests cover:
- DoctorChatEngine initialization and chat functionality
- PatientContextAggregator data gathering
- Context statistics computation
- Fallback response handling
- Conversation management
"""

import json
from datetime import datetime, date, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserType
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.checkin import DailyCheckin
from app.models.assessment import Assessment, AssessmentType, SeverityLevel
from app.models.conversation import Conversation, ConversationType
from app.models.risk_event import RiskEvent, RiskLevel, RiskType
from app.models.clinical_note import ClinicalNote
from app.models.doctor_conversation import DoctorConversation
from app.services.ai.doctor_chat_engine import DoctorChatEngine, DOCTOR_AI_SYSTEM_PROMPT
from app.services.ai.patient_context_aggregator import (
    PatientContextAggregator,
    PatientFullContext,
)
from app.utils.security import hash_password


# ============================================
# Fixtures
# ============================================

@pytest_asyncio.fixture
async def doctor_with_patient(db_session: AsyncSession):
    """Create a doctor with an assigned patient."""
    # Create doctor user
    doctor_user = User(
        id=str(uuid4()),
        email=f"doctor_{uuid4().hex[:8]}@test.com",
        password_hash=hash_password("testpass"),
        user_type=UserType.DOCTOR,
        is_active=True
    )
    db_session.add(doctor_user)
    await db_session.flush()

    # Create doctor
    doctor = Doctor(
        id=str(uuid4()),
        user_id=doctor_user.id,
        first_name="Dr",
        last_name="Test",
        license_number="LIC123",
        specialty="Psychiatry"
    )
    db_session.add(doctor)
    await db_session.flush()

    # Create patient user
    patient_user = User(
        id=str(uuid4()),
        email=f"patient_{uuid4().hex[:8]}@test.com",
        password_hash=hash_password("testpass"),
        user_type=UserType.PATIENT,
        is_active=True
    )
    db_session.add(patient_user)
    await db_session.flush()

    # Create patient with doctor relationship
    patient = Patient(
        id=str(uuid4()),
        user_id=patient_user.id,
        first_name="Test",
        last_name="Patient",
        date_of_birth=date(1990, 1, 15),
        gender="FEMALE",
        primary_doctor_id=doctor.id,
        preferred_language="en",
        medical_conditions="Anxiety",
        current_medications="None",
        therapy_history="Previous CBT",
        mental_health_goals="Manage anxiety better"
    )
    db_session.add(patient)
    await db_session.commit()

    return {"doctor": doctor, "patient": patient}


@pytest_asyncio.fixture
async def patient_with_data(db_session: AsyncSession, doctor_with_patient):
    """Create a patient with check-ins, assessments, and risk events."""
    patient = doctor_with_patient["patient"]

    # Add check-ins
    for i in range(7):
        checkin = DailyCheckin(
            patient_id=patient.id,
            checkin_date=date.today() - timedelta(days=i),
            mood_score=6 + (i % 3),  # Varying moods
            sleep_hours=7.0 - (i % 3) * 0.5,
            sleep_quality=4 - (i % 2),
            medication_taken=True,
            notes=f"Day {i} notes - feeling okay" if i < 3 else None
        )
        db_session.add(checkin)

    # Add assessments
    phq9 = Assessment(
        patient_id=patient.id,
        assessment_type=AssessmentType.PHQ9,
        total_score=12,
        severity=SeverityLevel.MODERATE,
        responses={"q1": 2, "q2": 1},
        risk_flags={"suicidal_ideation": False}
    )
    db_session.add(phq9)

    gad7 = Assessment(
        patient_id=patient.id,
        assessment_type=AssessmentType.GAD7,
        total_score=8,
        severity=SeverityLevel.MILD,
        responses={"q1": 1, "q2": 2}
    )
    db_session.add(gad7)

    # Add risk event
    risk_event = RiskEvent(
        patient_id=patient.id,
        risk_level=RiskLevel.MEDIUM,
        risk_type=RiskType.SELF_HARM,
        trigger_text="Patient mentioned feeling hopeless",
        doctor_reviewed=False
    )
    db_session.add(risk_event)

    # Add clinical note
    note = ClinicalNote(
        patient_id=patient.id,
        doctor_id=doctor_with_patient["doctor"].id,
        visit_date=date.today(),
        final_note="Patient making good progress with anxiety management.",
        is_reviewed=True
    )
    db_session.add(note)

    # Add conversation with summary
    conversation = Conversation(
        patient_id=patient.id,
        conv_type=ConversationType.SUPPORTIVE_CHAT,
        summary="Patient discussed work stress and coping strategies"
    )
    db_session.add(conversation)

    await db_session.commit()

    return doctor_with_patient


# ============================================
# DoctorChatEngine Tests
# ============================================

class TestDoctorChatEngine:
    """Tests for DoctorChatEngine class."""

    def test_initialization(self, db_session: AsyncSession):
        """Test engine initializes correctly."""
        engine = DoctorChatEngine(db_session)
        assert engine.db == db_session
        assert engine.context_aggregator is not None

    def test_initialization_no_api_key(self, db_session: AsyncSession):
        """Test engine handles missing API key."""
        with patch('app.services.ai.doctor_chat_engine.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = None

            engine = DoctorChatEngine(db_session)
            assert engine.client is None

    @pytest.mark.asyncio
    async def test_verify_relationship_valid(
        self, db_session: AsyncSession, doctor_with_patient
    ):
        """Test verifying valid doctor-patient relationship."""
        doctor = doctor_with_patient["doctor"]
        patient = doctor_with_patient["patient"]

        engine = DoctorChatEngine(db_session)
        result = await engine._verify_relationship(doctor.id, patient.id)

        assert result is not None
        assert result.id == patient.id

    @pytest.mark.asyncio
    async def test_verify_relationship_invalid(
        self, db_session: AsyncSession, doctor_with_patient
    ):
        """Test verifying invalid doctor-patient relationship."""
        doctor = doctor_with_patient["doctor"]

        engine = DoctorChatEngine(db_session)
        result = await engine._verify_relationship(doctor.id, str(uuid4()))

        assert result is None

    @pytest.mark.asyncio
    async def test_get_or_create_conversation_new(
        self, db_session: AsyncSession, doctor_with_patient
    ):
        """Test creating a new conversation."""
        doctor = doctor_with_patient["doctor"]
        patient = doctor_with_patient["patient"]

        engine = DoctorChatEngine(db_session)
        conversation = await engine._get_or_create_conversation(
            doctor.id, patient.id, None
        )

        assert conversation is not None
        assert conversation.doctor_id == doctor.id
        assert conversation.patient_id == patient.id

    @pytest.mark.asyncio
    async def test_get_or_create_conversation_existing(
        self, db_session: AsyncSession, doctor_with_patient
    ):
        """Test retrieving existing conversation."""
        doctor = doctor_with_patient["doctor"]
        patient = doctor_with_patient["patient"]

        # Create existing conversation
        existing = DoctorConversation(
            doctor_id=doctor.id,
            patient_id=patient.id
        )
        db_session.add(existing)
        await db_session.flush()

        engine = DoctorChatEngine(db_session)
        conversation = await engine._get_or_create_conversation(
            doctor.id, patient.id, existing.id
        )

        assert conversation.id == existing.id

    def test_build_messages(self, db_session: AsyncSession):
        """Test building messages from history."""
        engine = DoctorChatEngine(db_session)

        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"},
        ]
        new_message = "New question"

        messages = engine._build_messages(history, new_message)

        assert len(messages) == 3
        assert messages[0]["content"] == "Previous question"
        assert messages[1]["content"] == "Previous answer"
        assert messages[2]["content"] == "New question"

    def test_build_messages_limits_history(self, db_session: AsyncSession):
        """Test that history is limited to last 30 messages."""
        engine = DoctorChatEngine(db_session)

        # Create 40 messages
        history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(40)
        ]

        messages = engine._build_messages(history, "New message")

        # Should have 30 from history + 1 new
        assert len(messages) == 31

    def test_fallback_response(self, db_session: AsyncSession):
        """Test fallback response generation."""
        engine = DoctorChatEngine(db_session)
        response = engine._fallback_response()

        assert "AI 服务暂时不可用" in response
        assert "temporarily unavailable" in response

    @pytest.mark.asyncio
    async def test_chat_no_relationship(
        self, db_session: AsyncSession, doctor_with_patient
    ):
        """Test chat fails without valid relationship."""
        doctor = doctor_with_patient["doctor"]

        engine = DoctorChatEngine(db_session)

        with pytest.raises(PermissionError, match="don't have access"):
            await engine.chat(
                doctor_id=doctor.id,
                patient_id=str(uuid4()),  # Non-existent patient
                message="Test message"
            )

    @pytest.mark.asyncio
    async def test_chat_success_with_mock(
        self, db_session: AsyncSession, doctor_with_patient
    ):
        """Test successful chat with mocked AI."""
        doctor = doctor_with_patient["doctor"]
        patient = doctor_with_patient["patient"]

        engine = DoctorChatEngine(db_session)

        # Mock the AI response
        with patch.object(engine, '_generate_response', new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "AI response about the patient"

            result = await engine.chat(
                doctor_id=doctor.id,
                patient_id=patient.id,
                message="What patterns do you see in the patient's data?"
            )

            assert "response" in result
            assert result["response"] == "AI response about the patient"
            assert "conversation_id" in result
            assert result["patient_name"] == patient.full_name

    @pytest.mark.asyncio
    async def test_generate_response_no_client(
        self, db_session: AsyncSession, doctor_with_patient
    ):
        """Test generate response returns fallback when no client."""
        doctor = doctor_with_patient["doctor"]
        patient = doctor_with_patient["patient"]

        engine = DoctorChatEngine(db_session)
        engine.client = None  # No API client

        # Create a conversation
        conversation = DoctorConversation(
            doctor_id=doctor.id,
            patient_id=patient.id
        )

        # Create mock context
        mock_context = MagicMock()

        response = await engine._generate_response(
            message="Test",
            conversation=conversation,
            patient_context=mock_context
        )

        assert "暂时不可用" in response

    @pytest.mark.asyncio
    async def test_get_conversations(
        self, db_session: AsyncSession, doctor_with_patient
    ):
        """Test getting conversation list."""
        doctor = doctor_with_patient["doctor"]
        patient = doctor_with_patient["patient"]

        # Create multiple conversations
        for i in range(5):
            conv = DoctorConversation(
                doctor_id=doctor.id,
                patient_id=patient.id
            )
            db_session.add(conv)
        await db_session.commit()

        engine = DoctorChatEngine(db_session)
        conversations = await engine.get_conversations(
            doctor.id, patient.id, limit=3
        )

        assert len(conversations) == 3

    @pytest.mark.asyncio
    async def test_generate_conversation_summary_no_client(
        self, db_session: AsyncSession, doctor_with_patient
    ):
        """Test summary generation without client returns empty."""
        doctor = doctor_with_patient["doctor"]
        patient = doctor_with_patient["patient"]

        conversation = DoctorConversation(
            doctor_id=doctor.id,
            patient_id=patient.id
        )
        conversation.add_message("user", "Test question")
        conversation.add_message("assistant", "Test response")

        engine = DoctorChatEngine(db_session)
        engine.client = None

        summary = await engine.generate_conversation_summary(conversation)
        assert summary == ""

    @pytest.mark.asyncio
    async def test_generate_conversation_summary_empty_messages(
        self, db_session: AsyncSession, doctor_with_patient
    ):
        """Test summary generation with empty messages."""
        doctor = doctor_with_patient["doctor"]
        patient = doctor_with_patient["patient"]

        conversation = DoctorConversation(
            doctor_id=doctor.id,
            patient_id=patient.id
        )
        # No messages added

        engine = DoctorChatEngine(db_session)

        summary = await engine.generate_conversation_summary(conversation)
        assert summary == ""


# ============================================
# PatientContextAggregator Tests
# ============================================

class TestPatientContextAggregator:
    """Tests for PatientContextAggregator class."""

    @pytest.mark.asyncio
    async def test_get_full_context(
        self, db_session: AsyncSession, patient_with_data
    ):
        """Test getting full patient context."""
        patient = patient_with_data["patient"]

        aggregator = PatientContextAggregator(db_session)
        context = await aggregator.get_full_context(patient.id)

        assert context.patient.id == patient.id
        assert len(context.checkins) > 0
        assert len(context.assessments) > 0
        assert len(context.risk_events) > 0

    @pytest.mark.asyncio
    async def test_get_full_context_patient_not_found(
        self, db_session: AsyncSession
    ):
        """Test context aggregation fails for non-existent patient."""
        aggregator = PatientContextAggregator(db_session)

        with pytest.raises(ValueError, match="Patient not found"):
            await aggregator.get_full_context(str(uuid4()))

    @pytest.mark.asyncio
    async def test_get_patient(
        self, db_session: AsyncSession, doctor_with_patient
    ):
        """Test fetching patient profile."""
        patient = doctor_with_patient["patient"]

        aggregator = PatientContextAggregator(db_session)
        result = await aggregator._get_patient(patient.id)

        assert result is not None
        assert result.id == patient.id

    @pytest.mark.asyncio
    async def test_get_checkins(
        self, db_session: AsyncSession, patient_with_data
    ):
        """Test fetching check-ins."""
        patient = patient_with_data["patient"]
        cutoff = datetime.utcnow() - timedelta(days=30)

        aggregator = PatientContextAggregator(db_session)
        checkins = await aggregator._get_checkins(patient.id, cutoff)

        assert len(checkins) == 7

    @pytest.mark.asyncio
    async def test_get_assessments(
        self, db_session: AsyncSession, patient_with_data
    ):
        """Test fetching assessments."""
        patient = patient_with_data["patient"]
        cutoff = datetime.utcnow() - timedelta(days=30)

        aggregator = PatientContextAggregator(db_session)
        assessments = await aggregator._get_assessments(patient.id, cutoff)

        assert len(assessments) == 2

    @pytest.mark.asyncio
    async def test_get_risk_events(
        self, db_session: AsyncSession, patient_with_data
    ):
        """Test fetching risk events."""
        patient = patient_with_data["patient"]
        cutoff = datetime.utcnow() - timedelta(days=30)

        aggregator = PatientContextAggregator(db_session)
        events = await aggregator._get_risk_events(patient.id, cutoff)

        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_get_clinical_notes(
        self, db_session: AsyncSession, patient_with_data
    ):
        """Test fetching clinical notes."""
        patient = patient_with_data["patient"]
        cutoff = datetime.utcnow() - timedelta(days=30)

        aggregator = PatientContextAggregator(db_session)
        notes = await aggregator._get_clinical_notes(patient.id, cutoff)

        assert len(notes) == 1


# ============================================
# Statistics Computation Tests
# ============================================

class TestStatisticsComputation:
    """Tests for context statistics computation."""

    def test_compute_mood_stats_no_data(self, db_session: AsyncSession):
        """Test mood stats with no data."""
        aggregator = PatientContextAggregator(db_session)
        stats = aggregator._compute_mood_stats([])

        assert stats["has_data"] is False

    def test_compute_mood_stats_with_data(self, db_session: AsyncSession):
        """Test mood stats computation."""
        aggregator = PatientContextAggregator(db_session)

        # Create mock check-ins
        checkins = []
        for i in range(10):
            checkin = MagicMock()
            checkin.mood_score = 5 + (i % 5)
            checkins.append(checkin)

        stats = aggregator._compute_mood_stats(checkins)

        assert stats["has_data"] is True
        assert "average" in stats
        assert "min" in stats
        assert "max" in stats
        assert "trend" in stats
        assert "low_mood_days" in stats

    def test_compute_mood_stats_declining_trend(self, db_session: AsyncSession):
        """Test declining mood trend detection."""
        aggregator = PatientContextAggregator(db_session)

        # Create declining moods (recent lower, older higher)
        checkins = []
        for i in range(10):
            checkin = MagicMock()
            # First 5 (recent) are low, last 5 (older) are high
            checkin.mood_score = 3 if i < 5 else 8
            checkins.append(checkin)

        stats = aggregator._compute_mood_stats(checkins)

        assert stats["trend"] == "declining"

    def test_compute_mood_stats_improving_trend(self, db_session: AsyncSession):
        """Test improving mood trend detection."""
        aggregator = PatientContextAggregator(db_session)

        checkins = []
        for i in range(10):
            checkin = MagicMock()
            # First 5 (recent) are high, last 5 (older) are low
            checkin.mood_score = 8 if i < 5 else 3
            checkins.append(checkin)

        stats = aggregator._compute_mood_stats(checkins)

        assert stats["trend"] == "improving"

    def test_compute_sleep_stats_no_data(self, db_session: AsyncSession):
        """Test sleep stats with no data."""
        aggregator = PatientContextAggregator(db_session)
        stats = aggregator._compute_sleep_stats([])

        assert stats["has_data"] is False

    def test_compute_sleep_stats_with_data(self, db_session: AsyncSession):
        """Test sleep stats computation."""
        aggregator = PatientContextAggregator(db_session)

        checkins = []
        for i in range(7):
            checkin = MagicMock()
            checkin.sleep_hours = 6.0 + (i * 0.5)
            checkin.sleep_quality = 3 + (i % 2)
            checkins.append(checkin)

        stats = aggregator._compute_sleep_stats(checkins)

        assert stats["has_data"] is True
        assert "average_hours" in stats
        assert "average_quality" in stats
        assert "insufficient_sleep_days" in stats

    def test_compute_assessment_summary_no_data(self, db_session: AsyncSession):
        """Test assessment summary with no data."""
        aggregator = PatientContextAggregator(db_session)
        summary = aggregator._compute_assessment_summary([])

        assert summary["has_data"] is False

    def test_compute_assessment_summary_with_data(self, db_session: AsyncSession):
        """Test assessment summary computation."""
        aggregator = PatientContextAggregator(db_session)

        # Create mock assessments
        phq9 = MagicMock()
        phq9.assessment_type = AssessmentType.PHQ9
        phq9.total_score = 15
        phq9.severity = SeverityLevel.MODERATELY_SEVERE
        phq9.created_at = datetime.utcnow()
        phq9.risk_flags = {"suicidal_ideation": True}

        gad7 = MagicMock()
        gad7.assessment_type = AssessmentType.GAD7
        gad7.total_score = 10
        gad7.severity = SeverityLevel.MODERATE
        gad7.created_at = datetime.utcnow()
        gad7.risk_flags = None

        summary = aggregator._compute_assessment_summary([phq9, gad7])

        assert summary["has_data"] is True
        assert "PHQ9" in summary["assessments"]
        assert "GAD7" in summary["assessments"]
        assert summary["overall_severity"] == "MODERATELY_SEVERE"

    def test_compute_risk_summary_no_data(self, db_session: AsyncSession):
        """Test risk summary with no data."""
        aggregator = PatientContextAggregator(db_session)
        summary = aggregator._compute_risk_summary([])

        assert summary["has_data"] is False
        assert summary["total_events"] == 0

    def test_compute_risk_summary_with_data(self, db_session: AsyncSession):
        """Test risk summary computation."""
        aggregator = PatientContextAggregator(db_session)

        # Create mock risk events
        events = []
        for i, level in enumerate([RiskLevel.HIGH, RiskLevel.MEDIUM, RiskLevel.LOW]):
            event = MagicMock()
            event.risk_level = level
            event.risk_type = RiskType.SELF_HARM
            event.doctor_reviewed = (i == 2)  # Only last one reviewed
            event.created_at = datetime.utcnow() - timedelta(days=i)
            events.append(event)

        summary = aggregator._compute_risk_summary(events)

        assert summary["has_data"] is True
        assert summary["total_events"] == 3
        assert summary["unreviewed_count"] == 2
        assert summary["critical_high_count"] == 1
        assert summary["latest_event"]["level"] == "HIGH"


# ============================================
# Context Prompt Building Tests
# ============================================

class TestContextPromptBuilding:
    """Tests for building context prompts."""

    def test_build_context_prompt_minimal(self, db_session: AsyncSession):
        """Test building prompt with minimal data."""
        aggregator = PatientContextAggregator(db_session)

        # Create minimal patient
        patient = MagicMock()
        patient.full_name = "Test Patient"
        patient.date_of_birth = None
        patient.gender = None
        patient.preferred_language = None
        patient.medical_conditions = None
        patient.current_medications = None
        patient.allergies = None
        patient.therapy_history = None
        patient.mental_health_goals = None
        patient.triggers_notes = None
        patient.coping_strategies = None
        patient.support_system = None

        context = PatientFullContext(
            patient=patient,
            checkins=[],
            assessments=[],
            conversations=[],
            risk_events=[],
            clinical_notes=[],
            mood_stats={"has_data": False},
            sleep_stats={"has_data": False},
            assessment_summary={"has_data": False},
            risk_summary={"has_data": False},
        )

        prompt = aggregator.build_context_prompt(context)

        assert "Patient Profile" in prompt
        assert "Test Patient" in prompt

    def test_build_context_prompt_full(self, db_session: AsyncSession):
        """Test building prompt with full data."""
        aggregator = PatientContextAggregator(db_session)

        patient = MagicMock()
        patient.full_name = "Full Test Patient"
        patient.date_of_birth = date(1990, 1, 1)
        patient.gender = "FEMALE"
        patient.preferred_language = "en"
        patient.medical_conditions = "Anxiety, Depression"
        patient.current_medications = "Sertraline 50mg"
        patient.allergies = "None"
        patient.therapy_history = "Previous CBT"
        patient.mental_health_goals = "Better sleep"
        patient.triggers_notes = "Work stress"
        patient.coping_strategies = "Meditation"
        patient.support_system = "Family"

        # Create conversation with summary
        conv = MagicMock()
        conv.summary = "Discussed anxiety management techniques"

        # Create checkin with notes
        checkin = MagicMock()
        checkin.notes = "Feeling better today after exercise"

        context = PatientFullContext(
            patient=patient,
            checkins=[checkin],
            assessments=[],
            conversations=[conv],
            risk_events=[],
            clinical_notes=[],
            mood_stats={
                "has_data": True,
                "average": 6.5,
                "min": 4,
                "max": 8,
                "trend": "improving",
                "low_mood_days": 2
            },
            sleep_stats={
                "has_data": True,
                "average_hours": 7.2,
                "average_quality": 3.5,
                "insufficient_sleep_days": 1
            },
            assessment_summary={
                "has_data": True,
                "assessments": {
                    "PHQ9": {
                        "score": 12,
                        "severity": "MODERATE",
                        "date": datetime.utcnow().isoformat(),
                        "risk_flags": {"suicidal_ideation": False}
                    }
                },
                "overall_severity": "MODERATE"
            },
            risk_summary={
                "has_data": True,
                "total_events": 2,
                "unreviewed_count": 1,
                "critical_high_count": 1,
                "latest_event": {
                    "level": "HIGH",
                    "type": "SELF_HARM",
                    "date": datetime.utcnow().isoformat()
                }
            },
        )

        prompt = aggregator.build_context_prompt(context)

        # Check all sections present
        assert "Patient Profile" in prompt
        assert "Full Test Patient" in prompt
        assert "FEMALE" in prompt
        assert "Anxiety, Depression" in prompt
        assert "Recent Mood Patterns" in prompt
        assert "6.5/10" in prompt
        assert "improving" in prompt
        assert "Recent Sleep Patterns" in prompt
        assert "7.2 hours" in prompt
        assert "Assessment Results" in prompt
        assert "PHQ-9" in prompt
        assert "Risk Events Summary" in prompt
        assert "Conversation Themes" in prompt
        assert "Check-in Notes" in prompt


# ============================================
# DoctorConversation Model Tests
# ============================================

class TestDoctorConversationModel:
    """Tests for DoctorConversation model."""

    def test_messages_property_empty(self):
        """Test messages property returns empty list."""
        conv = DoctorConversation()
        assert conv.messages == []

    def test_messages_property_with_data(self):
        """Test messages property parses JSON."""
        conv = DoctorConversation()
        conv.messages_json = json.dumps([
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ])

        assert len(conv.messages) == 2
        assert conv.messages[0]["role"] == "user"

    def test_messages_setter(self):
        """Test messages setter serializes to JSON."""
        conv = DoctorConversation()
        conv.messages = [
            {"role": "user", "content": "Test message"}
        ]

        assert "Test message" in conv.messages_json

    def test_add_message(self):
        """Test adding a message."""
        conv = DoctorConversation()
        conv.add_message("user", "First message")
        conv.add_message("assistant", "Response")

        assert len(conv.messages) == 2
        assert conv.messages[0]["content"] == "First message"
        assert conv.messages[1]["content"] == "Response"
        assert "timestamp" in conv.messages[0]

    def test_repr(self):
        """Test string representation."""
        conv = DoctorConversation()
        conv.doctor_id = "doc123"
        conv.patient_id = "pat456"

        repr_str = repr(conv)
        assert "doc123" in repr_str
        assert "pat456" in repr_str


# ============================================
# System Prompt Tests
# ============================================

class TestSystemPrompt:
    """Tests for the system prompt."""

    def test_system_prompt_structure(self):
        """Test system prompt has required sections."""
        assert "Your Role" in DOCTOR_AI_SYSTEM_PROMPT
        assert "What You Can Do" in DOCTOR_AI_SYSTEM_PROMPT
        assert "What You Cannot Do" in DOCTOR_AI_SYSTEM_PROMPT
        assert "Special Considerations" in DOCTOR_AI_SYSTEM_PROMPT
        assert "{patient_context}" in DOCTOR_AI_SYSTEM_PROMPT

    def test_system_prompt_multilingual(self):
        """Test system prompt mentions language handling."""
        assert "Chinese" in DOCTOR_AI_SYSTEM_PROMPT
        assert "English" in DOCTOR_AI_SYSTEM_PROMPT

    def test_system_prompt_patient_context_placeholder(self):
        """Test patient context placeholder can be formatted."""
        formatted = DOCTOR_AI_SYSTEM_PROMPT.format(
            patient_context="## Test Context\n- Name: Test Patient"
        )

        assert "## Test Context" in formatted
        assert "Test Patient" in formatted
