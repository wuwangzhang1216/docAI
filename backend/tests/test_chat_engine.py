"""
Unit tests for Chat Engine Service.

Tests AI chat functionality, risk detection integration, and response handling.
Uses mocking to avoid actual API calls.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import date, datetime

from app.services.ai.chat_engine import ChatEngine
from app.services.ai.risk_detector import RiskResult
from app.models.risk_event import RiskLevel, RiskType
from app.models.conversation import ConversationType
from app.models.patient import Patient
from app.models.assessment import Assessment
from app.models.checkin import DailyCheckin


class TestChatEngineInitialization:
    """Tests for ChatEngine initialization."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        with patch('app.services.ai.chat_engine.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-api-key"
            with patch('app.services.ai.chat_engine.AsyncAnthropic') as mock_client:
                engine = ChatEngine()

                mock_client.assert_called_once_with(api_key="test-api-key")
                assert engine.client is not None

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        with patch('app.services.ai.chat_engine.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = None
            engine = ChatEngine()

            assert engine.client is None

    def test_init_creates_risk_detector(self):
        """Test risk detector is created."""
        with patch('app.services.ai.chat_engine.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = None
            engine = ChatEngine()

            assert engine.risk_detector is not None


class TestChatEngineChat:
    """Tests for chat functionality."""

    @pytest.fixture
    def chat_engine(self):
        """Create chat engine with mocked client."""
        with patch('app.services.ai.chat_engine.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            with patch('app.services.ai.chat_engine.AsyncAnthropic'):
                engine = ChatEngine()
                engine.client = AsyncMock()
                engine.risk_detector = AsyncMock()
                return engine

    @pytest.mark.asyncio
    async def test_chat_normal_message(self, chat_engine):
        """Test normal message gets AI response."""
        # Mock risk detector to return low risk
        chat_engine.risk_detector.detect = AsyncMock(return_value=RiskResult(
            level=RiskLevel.LOW,
            risk_type=None,
            confidence=0.1,
            trigger_text=None
        ))

        # Mock API response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="I'm here to help. How are you feeling?")]
        chat_engine.client.messages.create = AsyncMock(return_value=mock_response)

        reply, risk = await chat_engine.chat(
            message="Hello, I'm feeling okay today.",
            history=[]
        )

        assert reply == "I'm here to help. How are you feeling?"
        assert risk is None  # Low risk is not returned

    @pytest.mark.asyncio
    async def test_chat_critical_risk_returns_crisis_response(self, chat_engine):
        """Test critical risk triggers crisis response."""
        chat_engine.risk_detector.detect = AsyncMock(return_value=RiskResult(
            level=RiskLevel.CRITICAL,
            risk_type=RiskType.SUICIDAL,
            confidence=0.95,
            trigger_text="I want to end it all"
        ))

        reply, risk = await chat_engine.chat(
            message="I want to end it all",
            history=[]
        )

        # Should return crisis response, not call API
        assert "crisis" in reply.lower() or "support" in reply.lower() or "988" in reply or "help" in reply.lower()
        assert risk is not None
        assert risk.level == RiskLevel.CRITICAL
        # API should NOT be called for critical risk
        chat_engine.client.messages.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_chat_high_risk_returns_crisis_response(self, chat_engine):
        """Test high risk triggers crisis response."""
        chat_engine.risk_detector.detect = AsyncMock(return_value=RiskResult(
            level=RiskLevel.HIGH,
            risk_type=RiskType.SELF_HARM,
            confidence=0.85,
            trigger_text="I've been hurting myself"
        ))

        reply, risk = await chat_engine.chat(
            message="I've been hurting myself",
            history=[]
        )

        assert risk is not None
        assert risk.level == RiskLevel.HIGH
        chat_engine.client.messages.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_chat_medium_risk_returns_ai_response_with_risk(self, chat_engine):
        """Test medium risk returns AI response but includes risk info."""
        chat_engine.risk_detector.detect = AsyncMock(return_value=RiskResult(
            level=RiskLevel.MEDIUM,
            risk_type=RiskType.OTHER,
            confidence=0.6,
            trigger_text="Feeling very hopeless"
        ))

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="I hear that you're struggling.")]
        chat_engine.client.messages.create = AsyncMock(return_value=mock_response)

        reply, risk = await chat_engine.chat(
            message="Feeling very hopeless lately",
            history=[]
        )

        assert reply == "I hear that you're struggling."
        assert risk is not None
        assert risk.level == RiskLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_chat_pre_visit_uses_different_prompt(self, chat_engine):
        """Test pre-visit conversation type uses correct system prompt."""
        chat_engine.risk_detector.detect = AsyncMock(return_value=RiskResult(
            level=RiskLevel.LOW,
            risk_type=None,
            confidence=0.1,
            trigger_text=None
        ))

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Let me gather some information.")]
        chat_engine.client.messages.create = AsyncMock(return_value=mock_response)

        await chat_engine.chat(
            message="I have an appointment tomorrow",
            history=[],
            conversation_type=ConversationType.PRE_VISIT
        )

        # Verify API was called
        chat_engine.client.messages.create.assert_called_once()
        call_kwargs = chat_engine.client.messages.create.call_args.kwargs
        assert 'system' in call_kwargs

    @pytest.mark.asyncio
    async def test_chat_with_patient_context(self, chat_engine):
        """Test chat includes patient context when provided."""
        chat_engine.risk_detector.detect = AsyncMock(return_value=RiskResult(
            level=RiskLevel.LOW,
            risk_type=None,
            confidence=0.1,
            trigger_text=None
        ))

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Based on your profile...")]
        chat_engine.client.messages.create = AsyncMock(return_value=mock_response)

        # Create mock patient
        patient = Mock(spec=Patient)
        patient.first_name = "Test"
        patient.last_name = "Patient"

        chat_engine.user_context_builder.build_context = Mock(return_value="Patient context info")

        await chat_engine.chat(
            message="How am I doing?",
            history=[],
            patient=patient
        )

        # Verify context builder was called
        chat_engine.user_context_builder.build_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_api_error_returns_fallback(self, chat_engine):
        """Test API error returns fallback response."""
        chat_engine.risk_detector.detect = AsyncMock(return_value=RiskResult(
            level=RiskLevel.LOW,
            risk_type=None,
            confidence=0.1,
            trigger_text=None
        ))

        chat_engine.client.messages.create = AsyncMock(side_effect=Exception("API Error"))

        reply, risk = await chat_engine.chat(
            message="Hello",
            history=[]
        )

        # Should return fallback response in Chinese
        assert len(reply) > 0
        assert risk is None

    @pytest.mark.asyncio
    async def test_chat_no_client_returns_fallback(self):
        """Test chat without client returns fallback."""
        with patch('app.services.ai.chat_engine.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = None
            engine = ChatEngine()
            engine.risk_detector = AsyncMock()
            engine.risk_detector.detect = AsyncMock(return_value=RiskResult(
                level=RiskLevel.LOW,
                risk_type=None,
                confidence=0.1,
                trigger_text=None
            ))

            reply, risk = await engine.chat(
                message="Hello",
                history=[]
            )

            assert len(reply) > 0


class TestChatEngineMessageBuilding:
    """Tests for message building logic."""

    @pytest.fixture
    def chat_engine(self):
        """Create chat engine."""
        with patch('app.services.ai.chat_engine.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = None
            return ChatEngine()

    def test_build_messages_empty_history(self, chat_engine):
        """Test message building with empty history."""
        messages = chat_engine._build_messages([], "Hello")

        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"

    def test_build_messages_with_history(self, chat_engine):
        """Test message building with history."""
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "I'm well, thanks."},
        ]

        messages = chat_engine._build_messages(history, "That's good")

        assert len(messages) == 5
        assert messages[-1]["content"] == "That's good"
        assert messages[-1]["role"] == "user"

    def test_build_messages_truncates_long_history(self, chat_engine):
        """Test message building truncates history over 20 messages."""
        history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(30)
        ]

        messages = chat_engine._build_messages(history, "Final message")

        # Should have 20 history + 1 new = 21 messages
        assert len(messages) == 21
        # First message should be from recent history
        assert "Message 10" in messages[0]["content"]


class TestChatEngineSummary:
    """Tests for conversation summary generation."""

    @pytest.fixture
    def chat_engine(self):
        """Create chat engine with mocked client."""
        with patch('app.services.ai.chat_engine.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = "test-key"
            with patch('app.services.ai.chat_engine.AsyncAnthropic'):
                engine = ChatEngine()
                engine.client = AsyncMock()
                return engine

    @pytest.mark.asyncio
    async def test_generate_summary_success(self, chat_engine):
        """Test summary generation returns text."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Patient discussed anxiety and sleep issues.")]
        chat_engine.client.messages.create = AsyncMock(return_value=mock_response)

        messages = [
            {"role": "user", "content": "I'm feeling anxious"},
            {"role": "assistant", "content": "I understand. Tell me more."},
            {"role": "user", "content": "I can't sleep well"},
        ]

        summary = await chat_engine.generate_summary(messages)

        assert summary == "Patient discussed anxiety and sleep issues."

    @pytest.mark.asyncio
    async def test_generate_summary_empty_messages(self, chat_engine):
        """Test summary with empty messages returns empty string."""
        summary = await chat_engine.generate_summary([])

        assert summary == ""
        chat_engine.client.messages.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_summary_no_client(self):
        """Test summary without client returns empty string."""
        with patch('app.services.ai.chat_engine.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = None
            engine = ChatEngine()

            summary = await engine.generate_summary([{"role": "user", "content": "Test"}])

            assert summary == ""

    @pytest.mark.asyncio
    async def test_generate_summary_api_error(self, chat_engine):
        """Test summary handles API errors gracefully."""
        chat_engine.client.messages.create = AsyncMock(side_effect=Exception("API Error"))

        summary = await chat_engine.generate_summary([{"role": "user", "content": "Test"}])

        assert summary == ""


class TestChatEngineFallbackResponse:
    """Tests for fallback response."""

    def test_fallback_response_is_supportive(self):
        """Test fallback response is supportive Chinese text."""
        with patch('app.services.ai.chat_engine.settings') as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = None
            engine = ChatEngine()

            response = engine._fallback_response("I'm sad")

            assert len(response) > 0
            # Should be Chinese text
            assert any('\u4e00' <= c <= '\u9fff' for c in response)
