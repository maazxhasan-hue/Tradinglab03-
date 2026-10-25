"""Production safety and acceptance gates for Nexora agent deliverables.

This module is deliberately provider- and platform-neutral. It makes task completion
conditional on evidence and required gates; it does not pretend to publish, deploy,
charge a client, or render a video when no verified connector performed that action.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class DeliveryStage(str, Enum):
    LEAD = "lead"
    INTEREST_CONFIRMED = "interest_confirmed"
    DEMO_APPROVED = "demo_approved"
    PAYMENT_VERIFIED = "payment_verified"
    PRODUCTION_QA = "production_qa"
    HANDED_OVER = "handed_over"


class GateError(ValueError):
    """Raised when a workflow attempts an unverified or unauthorized transition."""


@dataclass(frozen=True)
class GateResult:
    allowed: bool
    reason: str
    required_evidence: tuple[str, ...] = ()


# Events must be recorded by trusted server-side integrations, not asserted by an LLM.
_STAGE_REQUIREMENTS: dict[DeliveryStage, tuple[str, ...]] = {
    DeliveryStage.LEAD: (),
    DeliveryStage.INTEREST_CONFIRMED: ("client_interest_record",),
    DeliveryStage.DEMO_APPROVED: ("client_interest_record", "demo_scope_approval"),
    DeliveryStage.PAYMENT_VERIFIED: (
        "client_interest_record", "demo_scope_approval", "payment_provider_verification"
    ),
    DeliveryStage.PRODUCTION_QA: (
        "payment_provider_verification", "production_build_passed",
        "security_checks_passed", "client_acceptance_checks_passed"
    ),
    DeliveryStage.HANDED_OVER: (
        "payment_provider_verification", "production_build_passed",
        "security_checks_passed", "client_acceptance_checks_passed",
        "deployment_verified", "admin_access_verified", "handover_record"
    ),
}


def evaluate_delivery_transition(
    target: DeliveryStage, evidence: Mapping[str, Any], *, owner_approved: bool = False
) -> GateResult:
    """Evaluate a client delivery stage from trusted evidence flags/records.

    AI-generated text is not proof. Callers should populate evidence only from
    authenticated client, payment, CI, hosting, and handover integrations.
    """
    required = _STAGE_REQUIREMENTS[target]
    missing = tuple(key for key in required if not _is_verified(evidence.get(key)))
    if missing:
        return GateResult(False, "Required verified evidence is missing.", missing)
    if target in {DeliveryStage.DEMO_APPROVED, DeliveryStage.PRODUCTION_QA,
                  DeliveryStage.HANDED_OVER} and not owner_approved:
        return GateResult(False, "Owner approval is required.", ("owner_approval",))
    return GateResult(True, "Evidence and approval gates passed.", ())


def _is_verified(value: Any) -> bool:
    """Accept explicit verified records; reject plain strings and truthy AI claims."""
    if not isinstance(value, Mapping):
        return False
    return value.get("verified") is True and bool(str(value.get("source", "")).strip()) and bool(
        str(value.get("reference", "")).strip()
    )


@dataclass
class AgentRunRecord:
    """Minimal per-agent accountability record suitable for dashboard serialization."""
    agent_id: str
    task_id: str
    status: str = "queued"
    attempt: int = 0
    heartbeat_at: str | None = None
    evidence: list[dict[str, str]] = field(default_factory=list)
    output: dict[str, Any] = field(default_factory=dict)
    failure_category: str | None = None

    VALID_STATUSES = frozenset({
        "queued", "running", "retrying", "blocked", "needs_review", "completed", "failed"
    })

    def transition(self, status: str, *, output: Mapping[str, Any] | None = None,
                   evidence: list[dict[str, str]] | None = None,
                   failure_category: str | None = None) -> None:
        if status not in self.VALID_STATUSES:
            raise GateError("Unknown agent task status.")
        if status == "completed":
            if not output or not evidence:
                raise GateError("Completion requires a non-empty output and evidence.")
            for item in evidence:
                if not isinstance(item, dict) or not item.get("source") or not item.get("reference"):
                    raise GateError("Each evidence item requires a source and reference.")
        self.status = status
        if output is not None:
            self.output = dict(output)
        if evidence is not None:
            self.evidence = list(evidence)
        self.failure_category = failure_category


def can_perform_external_action(
    action: str, *, connector_verified: bool, owner_approved: bool,
    platform_permission_verified: bool = False, budget_approved: bool = False
) -> GateResult:
    """Default-deny gate for actions that affect clients or public platforms."""
    if not connector_verified:
        return GateResult(False, "A verified production connector is required.",
                          ("connector_verification",))
    if not owner_approved:
        return GateResult(False, "Explicit owner approval is required.", ("owner_approval",))
    if action in {"publish_content", "send_public_reply", "send_direct_message"}:
        if not platform_permission_verified:
            return GateResult(False, "Platform permission must be verified.",
                              ("platform_permission_verification",))
    if action in {"paid_promotion", "make_purchase"} and not budget_approved:
        return GateResult(False, "An explicit budget approval is required.", ("budget_approval",))
    return GateResult(True, "External-action gates passed.", ())


def validate_video_delivery(manifest: Mapping[str, Any]) -> GateResult:
    """Reject script-only 'video complete' claims; require a rendered artifact and QA."""
    required = (
        "rendered_asset_uri", "duration_seconds", "aspect_ratio", "voiceover_qa",
        "audio_mix_qa", "caption_safe_area_qa", "pacing_qa", "claims_qa"
    )
    missing = tuple(key for key in required if not _is_usable(manifest.get(key)))
    if missing:
        return GateResult(False, "A rendered video and all required QA checks are needed.", missing)
    return GateResult(True, "Rendered video manifest passed required QA fields.", ())


def _is_usable(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value > 0
    return isinstance(value, str) and bool(value.strip())
