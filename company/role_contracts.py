"""Canonical, testable role contracts for every Nexora registered agent.

Contracts define responsibilities and acceptance criteria. They do not grant a role
tools or permissions that are not actually configured in the runtime.
"""
from __future__ import annotations

from typing import Any

from company.nexora_growth_runtime import AGENT_DIRECTORY


# Order matters: narrow specialist matches precede broad department defaults.
_RULES = [
    (("harvey", "prospect researcher", "lead researcher", "lead discovery", "account research",
      "public prospect", "lead enrichment"), "research"),
    (("website builder", "frontend", "backend", "full-stack", "website making",
      "integration engineer", "devops", "automation developer", "agent developer",
      "release & development"), "engineering"),
    (("video", "creative", "graphic designer", "presentation designer", "voice producer",
      "motion"), "creative"),
    (("quality", "qa", "tester", "security", "red-team", "accessibility auditor",
      "website auditor", "compliance", "privacy", "policy", "process auditor"), "quality"),
    (("comment", "community", "customer support", "client support", "customer success",
      "retention", "feedback", "response escalation"), "community"),
    (("sales", "proposal", "qualification", "qualifier", "client onboarding",
      "partnership", "objection handling", "contact agent", "follow-up"), "sales"),
    (("marketing", "social", "instagram", "seo", "campaign", "content", "brand",
      "keyword", "distribution", "copywriter", "short-form"), "marketing"),
    (("finance", "bookkeeper", "cash-flow", "invoicing", "collections", "pricing",
      "procurement"), "finance"),
    (("research", "analyst", "intelligence", "data analyst", "experiment",
      "user researcher", "product researcher", "scout"), "analysis"),
    (("project", "operations", "orchestrator", "coordinator", "scheduler",
      "resource planner", "delivery", "release manager", "chief of staff"), "operations"),
    (("ceo", "strategy", "director", "executive", "decision", "memory", "knowledge",
      "performance auditor", "manager", "lead"), "coordination"),
]

_CONTRACTS: dict[str, dict[str, Any]] = {
    "research": {
        "mission": "Find and assess relevant public information with source-level evidence.",
        "deliverables": ["findings", "source_urls", "observed_facts", "uncertainties", "opportunity_score"],
        "quality_checks": ["Every material claim has a source and access date.",
                           "Separate observed facts from hypotheses.", "Deduplicate and flag stale or unavailable sources."],
        "tools": ["configured_public_research"],
    },
    "engineering": {
        "mission": "Create maintainable software deliverables from an approved scope and prove they build and work.",
        "deliverables": ["implementation_summary", "changed_files", "build_report", "test_report", "known_limitations"],
        "quality_checks": ["Build and relevant tests pass.", "Secrets are not committed or logged.",
                           "Security, accessibility, and responsive checks match the approved scope."],
        "tools": ["repository_access_if_configured", "sandboxed_code_execution_if_configured"],
    },
    "creative": {
        "mission": "Produce brand-consistent visual, audio, or video assets matching the approved creative brief.",
        "deliverables": ["creative_brief", "asset_manifest", "rendered_asset_uri", "quality_report"],
        "quality_checks": ["A real exported asset exists; a script alone is not a video.",
                           "Check pacing, voice clarity, audio mix, captions, safe margins, rights, and factual claims."],
        "tools": ["configured_media_generation", "render_pipeline_if_configured"],
    },
    "quality": {
        "mission": "Independently verify work against acceptance criteria and report reproducible defects.",
        "deliverables": ["acceptance_matrix", "test_results", "defects", "release_recommendation"],
        "quality_checks": ["Test evidence identifies the run and environment.",
                           "Failures block release until fixed or explicitly risk-accepted.",
                           "Mocked tests are labelled and never presented as production proof."],
        "tools": ["configured_test_runner", "configured_security_scanner"],
    },
    "community": {
        "mission": "Classify customer feedback and prepare accurate, helpful responses within approved policy.",
        "deliverables": ["intent_label", "priority", "evidence", "response_draft", "escalation_reason"],
        "quality_checks": ["Do not invent promises or customer facts.", "Protect personal data.",
                           "External replies require a verified connector, platform permission, and approval."],
        "tools": ["configured_public_comment_reader_if_authorized"],
    },
    "sales": {
        "mission": "Qualify a legitimate opportunity and prepare a scoped, truthful commercial next step.",
        "deliverables": ["qualification", "client_requirements", "scope_draft", "proposal_draft", "open_questions"],
        "quality_checks": ["No invented price, guarantee, credential, testimonial, or deadline.",
                           "Owner approves terms and external contact.", "Payment is recognized only from trusted provider evidence."],
        "tools": ["configured_public_research"],
    },
    "marketing": {
        "mission": "Plan and evaluate brand-consistent organic marketing based on audience and performance evidence.",
        "deliverables": ["content_calendar", "creative_brief", "caption_or_script", "campaign_metrics_plan"],
        "quality_checks": ["Claims are substantiated and content fits brand voice.",
                           "Distinguish organic reach from paid ads.", "Publishing and paid promotion require verified integration and approval."],
        "tools": ["configured_public_research", "configured_media_generation"],
    },
    "finance": {
        "mission": "Prepare auditable financial and pricing analysis from verified inputs.",
        "deliverables": ["assumptions", "calculation", "source_records", "risk_flags"],
        "quality_checks": ["Reconcile calculations and source records.", "Mark estimates clearly.",
                           "No purchase, price change, or payment action without authorization."],
        "tools": ["approved_financial_records_if_configured"],
    },
    "analysis": {
        "mission": "Turn verified evidence into a reasoned analysis, score, or experiment recommendation.",
        "deliverables": ["question", "method", "findings", "evidence", "confidence", "next_experiment"],
        "quality_checks": ["Explain assumptions and sample limits.", "Do not imply causation from correlation.",
                           "Reproduce calculations and distinguish facts from recommendations."],
        "tools": ["configured_public_research", "configured_analytics_if_available"],
    },
    "operations": {
        "mission": "Coordinate dependencies, ownership, task state, and delivery milestones.",
        "deliverables": ["task_plan", "owners", "dependencies", "status", "blockers", "handoff"],
        "quality_checks": ["No task is complete without required output and evidence.",
                           "Retries are bounded and idempotent.", "Escalate blocked work instead of claiming success."],
        "tools": ["internal_task_registry"],
    },
    "coordination": {
        "mission": "Align specialist work to company goals, preserve decision context, and enforce quality and policy.",
        "deliverables": ["decision_brief", "delegation_plan", "risk_register", "review_summary"],
        "quality_checks": ["Delegate only to registered roles.", "Recall relevant shared context and record useful outcomes when available.",
                           "New agents require an approved contract, least privilege, and tests before activation."],
        "tools": ["internal_task_registry", "shared_brain_if_configured"],
    },
}

_COMMON_PROHIBITIONS = [
    "Never claim a tool ran, file was created, site deployed, video rendered, payment received, or message sent without verifiable evidence.",
    "Never expose secrets, bypass platform rules, or access data outside the authorized scope.",
    "Never perform external contact, publication, purchases, price changes, or production handover without the required connector and approval.",
]


def _category(agent: dict[str, Any]) -> str:
    name = str(agent.get("name", "")).casefold()
    department = str(agent.get("department", "")).casefold()
    combined = f"{name} {department}"
    for needles, category in _RULES:
        if any(needle in combined for needle in needles):
            return category
    return "coordination"


def role_contract(agent_id: str) -> dict[str, Any]:
    """Return a stable contract for one registered agent or raise KeyError."""
    agent = AGENT_DIRECTORY.get(agent_id)
    if agent is None:
        raise KeyError(f"Unknown registered agent: {agent_id}")
    category = _category(agent)
    base = _CONTRACTS[category]
    return {
        "agent_id": agent["agent_id"],
        "name": agent["name"],
        "department": agent["department"],
        "category": category,
        "mission": base["mission"],
        "inputs_required": ["approved_task_brief", "relevant_context", "constraints"],
        "deliverables": list(base["deliverables"]),
        "quality_checks": list(base["quality_checks"]),
        "permitted_tools": list(base["tools"]),
        "prohibited_actions": list(_COMMON_PROHIBITIONS),
        "completion_policy": "needs_review",
        "external_actions_enabled": False,
        "subagent_policy": "propose_only_until_owner_approval_and_acceptance_tests",
    }


def all_role_contracts() -> list[dict[str, Any]]:
    """Return contracts for all registered company and growth roles."""
    return [role_contract(agent_id) for agent_id in sorted(AGENT_DIRECTORY)]


def validate_role_contract(contract: dict[str, Any]) -> list[str]:
    """Return validation errors; an empty list means the contract is structurally valid."""
    errors: list[str] = []
    for field in ("agent_id", "name", "department", "category", "mission"):
        if not isinstance(contract.get(field), str) or not contract[field].strip():
            errors.append(f"missing_{field}")
    for field in ("inputs_required", "deliverables", "quality_checks", "permitted_tools", "prohibited_actions"):
        value = contract.get(field)
        if not isinstance(value, list) or not value or any(not isinstance(x, str) or not x.strip() for x in value):
            errors.append(f"invalid_{field}")
    if contract.get("completion_policy") not in {"needs_review", "verified"}:
        errors.append("invalid_completion_policy")
    if contract.get("external_actions_enabled") is not False:
        errors.append("external_actions_must_default_deny")
    return errors
