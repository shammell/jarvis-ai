"""Intent Envelope — normalized input from voice/whatsapp/api, structured for downstream processing."""

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List, Union
from enum import Enum


class Channel(Enum):
    """Input source channel."""
    VOICE = "voice"
    WHATSAPP = "whatsapp"
    API = "api"
    TEXT = "text"


class InputType(Enum):
    """Normalized input categories."""
    COMMAND = "command"
    QUESTION = "question"
    PROJECT_REQUEST = "project_request"  # "build frontend + backend + supabase"
    STATUS = "status"
    APPROVAL = "approval"
    OTHER = "other"


@dataclass
class ActionEnvelope:
    """
    Universal normalized action envelope for all inputs.
    Structure: {request_id, channel, original_text, normalized_intent, context_timestamp}
    """
    request_id: str
    correlation_id: str
    channel: Channel
    original_text: str
    normalized_intent: str  # LLM-normalized canonical command
    input_type: InputType
    language: str = "en"  # en/ur/hi
    confidence: float = 0.5
    timestamp: str = None
    context: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        self.context = self.context or {}


@dataclass
class IntentAnalysis:
    """LLM-derived intent analysis for routing."""
    intent: str
    action_category: str  # planning/implementation/testing/verification
    complexity: str  # low/medium/high
    requires_approval: bool
    estimated_steps: int
    confidence: float


def create_envelope(
    text: str,
    channel: Channel = Channel.TEXT,
    original_text: str = None,
    context: Dict[str, Any] = None,
) -> ActionEnvelope:
    """Factory function to create normalized envelope."""
    return ActionEnvelope(
        request_id=str(uuid.uuid4()),
        correlation_id=str(uuid.uuid4()),
        channel=channel,
        original_text=original_text or text,
        normalized_intent=text,  # Placeholder — LLM normalizes later
        input_type=InputType.OTHER,
        confidence=1.0,
        context=context or {},
    )


def normalize_intent(
    envelope: ActionEnvelope,
    llm_analyzer,
) -> tuple[ActionEnvelope, IntentAnalysis]:
    """Normalize raw text to canonical intent using LLM."""
    # Placeholder for LLC-based normalization
    intent = llm_analyzer.analyze(envelope.original_text)
    analysis = IntentAnalysis(
        intent=intent.intent,
        action_category=intent.category,
        complexity="medium",
        requires_approval=False,
        estimated_steps=3,
        confidence=intent.confidence,
    )
    envelope.normalized_intent = intent.intent
    envelope.confidence = intent.confidence
    return envelope, analysis
