"""
Tests for risk detection service.

Covers:
- Rule-based risk detection patterns
- Multilingual support (Chinese, English, Farsi, Turkish, Spanish)
- Political trauma specific patterns
- Risk level classification
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.ai.risk_detector import RiskDetector, RiskResult
from app.models.risk_event import RiskLevel, RiskType


class TestRuleBasedDetection:
    """Test rule-based risk pattern detection."""

    @pytest.fixture
    def detector(self):
        """Create a RiskDetector without LLM (for rule-only tests)."""
        with patch.object(RiskDetector, '__init__', lambda x: None):
            d = RiskDetector()
            d.client = None  # Disable LLM
            return d

    # ============ Critical Risk Tests ============

    @pytest.mark.asyncio
    async def test_critical_chinese_immediate_suicide(self, detector):
        """Test critical Chinese suicide pattern."""
        result = await detector.detect("我今晚就要去死了")
        assert result.level == RiskLevel.CRITICAL
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_critical_english_immediate_suicide(self, detector):
        """Test critical English suicide pattern."""
        result = await detector.detect("I'm going to kill myself tonight")
        assert result.level == RiskLevel.CRITICAL
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_critical_prepared_means(self, detector):
        """Test critical pattern with prepared means (Chinese)."""
        result = await detector.detect("我已经准备好了药物")
        assert result.level == RiskLevel.CRITICAL
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_critical_english_prepared_means(self, detector):
        """Test critical pattern with prepared means (English)."""
        result = await detector.detect("I have the pills ready")
        assert result.level == RiskLevel.CRITICAL
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_critical_violence_threat(self, detector):
        """Test critical violence threat pattern."""
        result = await detector.detect("I'm going to hurt him badly")
        assert result.level == RiskLevel.CRITICAL
        assert result.risk_type == RiskType.VIOLENCE

    @pytest.mark.asyncio
    async def test_critical_chinese_violence(self, detector):
        """Test critical Chinese violence pattern."""
        result = await detector.detect("我要杀了那个人")
        assert result.level == RiskLevel.CRITICAL
        assert result.risk_type == RiskType.VIOLENCE

    @pytest.mark.asyncio
    async def test_critical_suicide_note(self, detector):
        """Test critical suicide note pattern."""
        result = await detector.detect("I've written my goodbye letter")
        assert result.level == RiskLevel.CRITICAL
        assert result.risk_type == RiskType.SUICIDAL

    # ============ High Risk Tests ============

    @pytest.mark.asyncio
    async def test_high_chinese_suicidal_ideation(self, detector):
        """Test high risk Chinese suicidal ideation."""
        result = await detector.detect("我想自杀")
        assert result.level == RiskLevel.HIGH
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_high_english_suicidal_ideation(self, detector):
        """Test high risk English suicidal ideation."""
        result = await detector.detect("I've been thinking about suicide")
        assert result.level == RiskLevel.HIGH
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_high_dont_want_to_live(self, detector):
        """Test high risk - don't want to live."""
        result = await detector.detect("I don't want to be alive anymore")
        assert result.level == RiskLevel.HIGH
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_high_chinese_dont_want_to_live(self, detector):
        """Test high risk Chinese - don't want to live."""
        result = await detector.detect("我不想活了")
        assert result.level == RiskLevel.HIGH
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_high_self_harm(self, detector):
        """Test high risk self-harm pattern."""
        result = await detector.detect("I want to cut myself")
        assert result.level == RiskLevel.HIGH
        assert result.risk_type == RiskType.SELF_HARM

    @pytest.mark.asyncio
    async def test_high_chinese_self_harm(self, detector):
        """Test high risk Chinese self-harm."""
        result = await detector.detect("我想割自己的手腕")
        assert result.level == RiskLevel.HIGH
        assert result.risk_type == RiskType.SELF_HARM

    # ============ Political Trauma - High Risk ============

    @pytest.mark.asyncio
    async def test_high_exile_despair_chinese(self, detector):
        """Test high risk exile despair (Chinese)."""
        result = await detector.detect("回不去了，活着也没有意义了")
        assert result.level == RiskLevel.HIGH
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_high_exile_despair_english(self, detector):
        """Test high risk exile despair (English)."""
        result = await detector.detect("I can't go back home, there's no point in living")
        assert result.level == RiskLevel.HIGH
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_high_survivor_guilt_chinese(self, detector):
        """Test high risk survivor guilt (Chinese)."""
        result = await detector.detect("应该死的是我，不是还在里面的同志们")
        assert result.level == RiskLevel.HIGH
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_high_survivor_guilt_english(self, detector):
        """Test high risk survivor guilt (English)."""
        result = await detector.detect("I don't deserve to live when my comrades are still suffering")
        assert result.level == RiskLevel.HIGH
        assert result.risk_type == RiskType.SUICIDAL

    # ============ Medium Risk Tests ============

    @pytest.mark.asyncio
    async def test_medium_meaningless_chinese(self, detector):
        """Test medium risk - life meaningless (Chinese)."""
        result = await detector.detect("活着没意思")
        assert result.level == RiskLevel.MEDIUM
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_medium_meaningless_english(self, detector):
        """Test medium risk - life meaningless (English)."""
        result = await detector.detect("Life feels pointless")
        assert result.level == RiskLevel.MEDIUM
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_medium_wish_disappear(self, detector):
        """Test medium risk - wish to disappear."""
        result = await detector.detect("I wish I could just disappear")
        assert result.level == RiskLevel.MEDIUM
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_medium_tired_of_living(self, detector):
        """Test medium risk - tired of living."""
        result = await detector.detect("I'm so tired of everything")
        assert result.level == RiskLevel.MEDIUM
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_medium_persecution_fear_chinese(self, detector):
        """Test medium risk persecution fear (Chinese)."""
        result = await detector.detect("他们会找到我的，到哪里都不安全")
        assert result.level == RiskLevel.MEDIUM
        assert result.risk_type == RiskType.PERSECUTION_FEAR

    @pytest.mark.asyncio
    async def test_medium_persecution_fear_english(self, detector):
        """Test medium risk persecution fear (English)."""
        result = await detector.detect("Government agents are tracking me, nowhere is safe")
        assert result.level == RiskLevel.MEDIUM
        assert result.risk_type == RiskType.PERSECUTION_FEAR

    @pytest.mark.asyncio
    async def test_medium_no_hope_chinese(self, detector):
        """Test medium risk - no hope (Chinese)."""
        result = await detector.detect("看不到任何希望了")
        assert result.level == RiskLevel.MEDIUM
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_medium_no_hope_english(self, detector):
        """Test medium risk - no hope (English)."""
        result = await detector.detect("I can't see any hope for the future")
        assert result.level == RiskLevel.MEDIUM
        assert result.risk_type == RiskType.SUICIDAL

    # ============ Multilingual Tests ============

    @pytest.mark.asyncio
    async def test_farsi_suicidal(self, detector):
        """Test Farsi suicidal pattern."""
        result = await detector.detect("زندگی معنی ندارد")
        assert result.level == RiskLevel.MEDIUM
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_turkish_suicidal(self, detector):
        """Test Turkish suicidal pattern."""
        result = await detector.detect("hayat anlamsız")
        assert result.level == RiskLevel.MEDIUM
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_spanish_suicidal(self, detector):
        """Test Spanish suicidal pattern."""
        result = await detector.detect("la vida no tiene sentido")
        assert result.level == RiskLevel.MEDIUM
        assert result.risk_type == RiskType.SUICIDAL

    # ============ Low Risk / Safe Tests ============

    @pytest.mark.asyncio
    async def test_low_risk_normal_text(self, detector):
        """Test normal text returns low risk."""
        result = await detector.detect("I had a good day today, went for a walk")
        assert result.level == RiskLevel.LOW

    @pytest.mark.asyncio
    async def test_low_risk_chinese_normal(self, detector):
        """Test normal Chinese text returns low risk."""
        result = await detector.detect("今天天气很好，心情不错")
        assert result.level == RiskLevel.LOW

    @pytest.mark.asyncio
    async def test_low_risk_discussion_of_topic(self, detector):
        """Test discussing suicide topic without intent is lower risk."""
        result = await detector.detect("I read an article about suicide prevention")
        assert result.level == RiskLevel.LOW

    @pytest.mark.asyncio
    async def test_low_risk_empty_text(self, detector):
        """Test empty text returns low risk."""
        result = await detector.detect("")
        assert result.level == RiskLevel.LOW


class TestLLMDetection:
    """Test LLM-based risk detection."""

    @pytest.fixture
    def detector_with_mock_llm(self):
        """Create RiskDetector with mocked LLM client."""
        with patch.object(RiskDetector, '__init__', lambda x: None):
            d = RiskDetector()
            d.client = MagicMock()
            return d

    @pytest.mark.asyncio
    async def test_llm_elevates_risk(self, detector_with_mock_llm):
        """Test LLM can elevate risk level from rules."""
        detector = detector_with_mock_llm

        # Mock LLM response that elevates risk
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"risk_level": "HIGH", "risk_type": "SUICIDAL", "confidence": 0.85, "reasoning": "Detected hopelessness"}')]
        detector.client.messages.create = AsyncMock(return_value=mock_response)

        # Text that rules would classify as LOW but LLM as HIGH
        result = await detector.detect("I feel completely empty inside, nothing matters anymore")

        assert result.level == RiskLevel.HIGH
        assert result.risk_type == RiskType.SUICIDAL

    @pytest.mark.asyncio
    async def test_llm_failure_fallback_to_rules(self, detector_with_mock_llm):
        """Test fallback to rule-based when LLM fails."""
        detector = detector_with_mock_llm

        # Mock LLM failure
        detector.client.messages.create = AsyncMock(side_effect=Exception("API Error"))

        # Text with clear pattern
        result = await detector.detect("I want to die")

        # Should still detect via rules
        assert result.level == RiskLevel.HIGH


class TestRiskResultModel:
    """Test RiskResult model."""

    def test_risk_result_defaults(self):
        """Test RiskResult default values."""
        result = RiskResult(level=RiskLevel.LOW)
        assert result.level == RiskLevel.LOW
        assert result.risk_type is None
        assert result.confidence == 1.0
        assert result.trigger_text is None
        assert result.reasoning is None

    def test_risk_result_full(self):
        """Test RiskResult with all fields."""
        result = RiskResult(
            level=RiskLevel.HIGH,
            risk_type=RiskType.SUICIDAL,
            confidence=0.9,
            trigger_text="I want to die",
            reasoning="Direct suicidal statement"
        )
        assert result.level == RiskLevel.HIGH
        assert result.risk_type == RiskType.SUICIDAL
        assert result.confidence == 0.9


class TestRiskLevelComparison:
    """Test risk level comparison logic."""

    def test_level_value_ordering(self):
        """Test that risk level values are correctly ordered."""
        assert RiskDetector._level_value(RiskLevel.LOW) < RiskDetector._level_value(RiskLevel.MEDIUM)
        assert RiskDetector._level_value(RiskLevel.MEDIUM) < RiskDetector._level_value(RiskLevel.HIGH)
        assert RiskDetector._level_value(RiskLevel.HIGH) < RiskDetector._level_value(RiskLevel.CRITICAL)

    def test_level_values(self):
        """Test specific level values."""
        assert RiskDetector._level_value(RiskLevel.LOW) == 0
        assert RiskDetector._level_value(RiskLevel.MEDIUM) == 1
        assert RiskDetector._level_value(RiskLevel.HIGH) == 2
        assert RiskDetector._level_value(RiskLevel.CRITICAL) == 3
