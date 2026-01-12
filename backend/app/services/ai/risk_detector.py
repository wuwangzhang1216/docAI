"""Risk detection service using rules and LLM."""

import re
import json
from typing import Optional, Tuple, List
from pydantic import BaseModel
from anthropic import AsyncAnthropic

from app.config import settings
from app.services.ai.prompts import RISK_DETECTION_PROMPT
from app.models.risk_event import RiskLevel, RiskType


class RiskResult(BaseModel):
    """Result of risk detection."""
    level: RiskLevel
    risk_type: Optional[RiskType] = None
    confidence: float = 1.0
    trigger_text: Optional[str] = None
    reasoning: Optional[str] = None


class RiskDetector:
    """
    Risk detector that combines rule-based and LLM-based detection.

    Rule-based detection is fast and catches obvious high-risk patterns.
    LLM-based detection provides more nuanced analysis.

    Designed for political trauma survivors - includes patterns for:
    - Exile despair
    - Survivor guilt
    - Meaning loss
    - Persecution fear

    Multilingual support: Chinese, English, Farsi, Turkish, Spanish
    """

    # Critical risk patterns - immediate danger
    CRITICAL_PATTERNS: List[Tuple[str, str]] = [
        # Chinese - 中文
        (r"(今晚|今天|马上|现在就).*(死|自杀|结束|了结)", "SUICIDAL"),
        (r"(准备|买|找)好了.*(药|刀|绳|农药)", "SUICIDAL"),
        (r"(要|想)(杀|伤害).*(他|她|那个人)", "VIOLENCE"),
        (r"(写好|留下).*遗书", "SUICIDAL"),
        # English
        (r"(tonight|today|right now|going to).*(kill myself|end it|suicide)", "SUICIDAL"),
        (r"(have|got|prepared).*(pills|knife|rope|gun)", "SUICIDAL"),
        (r"(want to|going to).*(kill|hurt).*(him|her|them|someone)", "VIOLENCE"),
        (r"(written|leaving).*(suicide note|goodbye letter)", "SUICIDAL"),
        # Farsi - فارسی
        (r"(امشب|الان|همین الان).*(خودکشی|بکشم)", "SUICIDAL"),
        # Turkish - Türkçe
        (r"(bu gece|şimdi).*(intihar|öldürmek)", "SUICIDAL"),
        # Spanish - Español
        (r"(esta noche|ahora mismo).*(suicidarme|matarme)", "SUICIDAL"),
    ]

    # High risk patterns - serious concern
    HIGH_PATTERNS: List[Tuple[str, str]] = [
        # Chinese - 中文
        (r"(想|要|打算)(死|自杀|结束生命)", "SUICIDAL"),
        (r"不想活", "SUICIDAL"),
        (r"(割|划|伤害)自己", "SELF_HARM"),
        (r"活着没有意义", "SUICIDAL"),
        # English
        (r"(want to|thinking about|planning).*(die|suicide|end my life)", "SUICIDAL"),
        (r"don't want to (live|be alive|exist)", "SUICIDAL"),
        (r"(cut|hurt|harm) myself", "SELF_HARM"),
        (r"life (has no|is without) meaning", "SUICIDAL"),
        # Political trauma - Exile despair (Chinese)
        (r"(回不去|无法回去).*(也|但).*(没有意义|活不下去)", "SUICIDAL"),
        (r"(流亡|逃出来).*(毫无意义|白费了|没有价值)", "SUICIDAL"),
        (r"我的牺牲.*没有(价值|意义)", "SUICIDAL"),
        # Political trauma - Exile despair (English)
        (r"can't go back.*(no point|meaningless|why live)", "SUICIDAL"),
        (r"(exile|escaped).*(pointless|worthless|waste)", "SUICIDAL"),
        (r"my sacrifice.*(meaningless|worthless|for nothing)", "SUICIDAL"),
        # Political trauma - Survivor guilt (Chinese)
        (r"(背叛|对不起).*(还在里面|留下的人|同志)", "SUICIDAL"),
        (r"应该.*死的是我", "SUICIDAL"),
        (r"(不配|没资格).*活着", "SUICIDAL"),
        # Political trauma - Survivor guilt (English)
        (r"(betrayed|abandoned).*(those inside|people back home|comrades)", "SUICIDAL"),
        (r"should (have been|be) me.*(died|dead)", "SUICIDAL"),
        (r"(don't deserve|not worthy).*(to live|to be alive)", "SUICIDAL"),
    ]

    # Medium risk patterns - needs attention
    MEDIUM_PATTERNS: List[Tuple[str, str]] = [
        # Chinese - 中文
        (r"活着没(意思|意义|劲)", "SUICIDAL"),
        (r"(消失|不存在)就好", "SUICIDAL"),
        (r"(厌世|厌倦)", "SUICIDAL"),
        (r"(想|会)(割|划)", "SELF_HARM"),
        # English
        (r"(life|living) (is|feels) (meaningless|pointless)", "SUICIDAL"),
        (r"(wish I could|better if I).*(disappear|didn't exist)", "SUICIDAL"),
        (r"(tired of|sick of) (living|life|everything)", "SUICIDAL"),
        # Political trauma - Meaning loss (Chinese)
        (r"(一切|所有努力).*都是徒劳", "SUICIDAL"),
        (r"(永远|再也).*不会.*(好|改变|有希望)", "SUICIDAL"),
        (r"看不到.*希望", "SUICIDAL"),
        (r"没有人.*理解.*经历", "SUICIDAL"),
        # Political trauma - Meaning loss (English)
        (r"(everything|all my efforts).*(futile|pointless|in vain)", "SUICIDAL"),
        (r"(never|will never).*(get better|change|be okay)", "SUICIDAL"),
        (r"(can't|cannot) see.*(hope|future|point)", "SUICIDAL"),
        (r"no one.*(understands|can understand).*what I.*(went through|experienced)", "SUICIDAL"),
        # Political trauma - Persecution fear (Chinese)
        (r"(他们|那边的人|政府).*会找到我", "PERSECUTION_FEAR"),
        (r"(到哪里|在哪).*都不安全", "PERSECUTION_FEAR"),
        # Political trauma - Persecution fear (English)
        (r"(they|government|agents).*(will find|are watching|tracking) me", "PERSECUTION_FEAR"),
        (r"(nowhere|not).*(safe|can hide)", "PERSECUTION_FEAR"),
        # Farsi patterns
        (r"(زندگی|هیچ).*(معنی|ارزش).*ندار", "SUICIDAL"),
        (r"(امید|آینده).*ندار", "SUICIDAL"),
        # Turkish patterns
        (r"(hayat|yaşam).*(anlamsız|değersiz)", "SUICIDAL"),
        (r"(umut|gelecek).*yok", "SUICIDAL"),
        # Spanish patterns
        (r"(vida|vivir).*(no tiene sentido|sin sentido)", "SUICIDAL"),
        (r"(no hay|sin).*(esperanza|futuro)", "SUICIDAL"),
    ]

    def __init__(self):
        """Initialize risk detector with Anthropic client."""
        self.client = None
        if settings.ANTHROPIC_API_KEY:
            self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def detect(self, text: str) -> RiskResult:
        """
        Detect risk level in the given text.

        Uses a two-stage approach:
        1. Rule-based detection for fast, high-confidence results
        2. LLM-based detection for nuanced analysis

        Args:
            text: The text to analyze

        Returns:
            RiskResult with level, type, confidence, and trigger text
        """
        # Stage 1: Rule-based detection
        rule_result = self._rule_check(text)

        # If critical or high risk detected by rules, return immediately
        if rule_result.level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            return rule_result

        # Stage 2: LLM-based detection (if available and rules didn't catch high risk)
        if self.client:
            try:
                llm_result = await self._llm_check(text)

                # Take the higher risk level
                if self._level_value(llm_result.level) > self._level_value(rule_result.level):
                    return llm_result
            except Exception as e:
                # Log error but don't fail - return rule result
                print(f"LLM risk detection failed: {e}")

        return rule_result

    def _rule_check(self, text: str) -> RiskResult:
        """
        Check text against predefined risk patterns.

        Args:
            text: The text to check

        Returns:
            RiskResult based on pattern matching
        """
        # Check critical patterns (case-insensitive for English text)
        for pattern, risk_type in self.CRITICAL_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return RiskResult(
                    level=RiskLevel.CRITICAL,
                    risk_type=RiskType(risk_type),
                    confidence=0.95,
                    trigger_text=match.group(),
                    reasoning="Critical pattern detected"
                )

        # Check high risk patterns (case-insensitive for English text)
        for pattern, risk_type in self.HIGH_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return RiskResult(
                    level=RiskLevel.HIGH,
                    risk_type=RiskType(risk_type),
                    confidence=0.9,
                    trigger_text=match.group(),
                    reasoning="High risk pattern detected"
                )

        # Check medium risk patterns (case-insensitive for English text)
        for pattern, risk_type in self.MEDIUM_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return RiskResult(
                    level=RiskLevel.MEDIUM,
                    risk_type=RiskType(risk_type),
                    confidence=0.8,
                    trigger_text=match.group(),
                    reasoning="Medium risk pattern detected"
                )

        # No risk detected
        return RiskResult(level=RiskLevel.LOW, confidence=1.0)

    async def _llm_check(self, text: str) -> RiskResult:
        """
        Use LLM to analyze text for risk.

        Args:
            text: The text to analyze

        Returns:
            RiskResult from LLM analysis
        """
        if not self.client:
            return RiskResult(level=RiskLevel.LOW)

        try:
            response = await self.client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": RISK_DETECTION_PROMPT.format(text=text)
                }]
            )

            # Parse JSON response
            result_text = response.content[0].text.strip()

            # Try to extract JSON from response
            json_match = re.search(r'\{[^}]+\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(result_text)

            # Map to RiskResult
            risk_level = result.get("risk_level", "LOW")
            if risk_level == "NONE":
                risk_level = "LOW"

            risk_type = result.get("risk_type")
            if risk_type and risk_type != "null":
                risk_type = RiskType(risk_type)
            else:
                risk_type = None

            return RiskResult(
                level=RiskLevel(risk_level),
                risk_type=risk_type,
                confidence=result.get("confidence", 0.8),
                reasoning=result.get("reasoning")
            )

        except json.JSONDecodeError:
            return RiskResult(level=RiskLevel.LOW, confidence=0.5)
        except Exception as e:
            print(f"LLM check error: {e}")
            return RiskResult(level=RiskLevel.LOW, confidence=0.5)

    @staticmethod
    def _level_value(level: RiskLevel) -> int:
        """Convert risk level to numeric value for comparison."""
        return {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3
        }.get(level, 0)
