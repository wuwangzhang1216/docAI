"""AI Services module.

Provides AI-powered chat, risk detection, and context retrieval tools
using the Hybrid approach with on-demand context loading.
"""

from app.services.ai.hybrid_chat_engine import HybridChatEngine
from app.services.ai.prompts import (
    CRISIS_RESPONSE_CRITICAL,
    CRISIS_RESPONSE_HIGH,
    NOTE_GENERATION_SYSTEM,
    RISK_DETECTION_PROMPT,
)
from app.services.ai.risk_detector import RiskDetector, RiskResult
from app.services.ai.tools import PATIENT_CONTEXT_TOOLS, PatientContextTools, get_essential_context

__all__ = [
    # Prompts
    "RISK_DETECTION_PROMPT",
    "NOTE_GENERATION_SYSTEM",
    "CRISIS_RESPONSE_CRITICAL",
    "CRISIS_RESPONSE_HIGH",
    # Risk Detection
    "RiskDetector",
    "RiskResult",
    # Chat Engine (Hybrid)
    "HybridChatEngine",
    # Tools
    "PATIENT_CONTEXT_TOOLS",
    "PatientContextTools",
    "get_essential_context",
]
