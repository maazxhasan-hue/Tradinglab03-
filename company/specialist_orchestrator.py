"""Sequential specialist passes for autonomous client delivery.

Each pass is a bounded model-agent run with a role-specific objective and a
separate evidence artifact. The passes share the approved local workspace;
they cannot send messages, access the network through tools, spend money, or
deploy production.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .autonomous_delivery import SERVICE_ROLES
from .tool_agent import run_tool_agent

ROLE_OBJECTIVES = {
    "Project Manager": "Turn the approved brief into a prioritized execution checklist, flag dependencies, and map acceptance criteria.",
    "Website Builder": "Improve the static website draft and identify pages that exist versus features needing real implementation.",
    "UX/UI Designer": "Improve layout, readability, responsive behavior, accessibility cues, and consistency using supplied facts only.",
    "QA Tester": "Inspect existing artifacts and quality reports, identify testable defects, and write reproducible acceptance tests/checklists. Never claim browser tests ran unless they did.",
    "Delivery Coordinator": "Prepare clear handover notes, scope boundaries, client review steps, and a list of remaining blockers.",
    "Copywriter": "Improve clear, audience-appropriate copy without inventing testimonials, credentials, performance claims, or client facts.",
    "Frontend Developer": "Implement feasible static front-end behavior in the allowed website workspace and document features that need backend support.",
    "Website Auditor": "Prepare evidence-oriented audit findings only from supplied artifacts; distinguish unverified hypotheses from observed results.",
    "SEO Specialist": "Improve page structure and SEO drafts using provided facts; do not fabricate search volumes, rankings, or external research.",
    "Accessibility Auditor": "Review available HTML/CSS for common accessibility issues and document concrete evidence and follow-up checks.",
    "Content Marketing Agent": "Improve content structure, audience fit, and reusable content ideas while keeping claims verifiable.",
    "Creative Director": "Create a coherent creative direction and concise concept brief aligned to the supplied audience and goals.",
    "Video Editor": "Prepare a practical edit plan, shot list, captions, and production checklist; do not claim a rendered video exists.",
    "Social Media Manager": "Prepare platform-ready draft copy and a posting checklist; do not publish or message anyone.",
    "Automation Developer": "Design a testable automation workflow and identify implementation steps, retries, and failure handling; do not connect external systems.",
    "Integration Engineer": "Document integration contracts, required permissions, test cases, and safe fallback behavior without using credentials.",
    "Security Reviewer": "Review artifacts for obvious secret exposure, unsafe assumptions, and least-privilege gaps; do not claim a full security audit.",
}

def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-") or "specialist"

def run_specialist_team(*, brief: dict[str, Any], workspace: str | Path,
                        api_key: str | None = None, max_rounds_per_role: int = 2) -> dict:
    """Run one bounded tool-agent pass per service role and preserve partial results."""
    if not isinstance(brief, dict):
        raise ValueError("brief must be an object")
    if max_rounds_per_role < 1 or max_rounds_per_role > 3:
        raise ValueError("max_rounds_per_role must be between 1 and 3")
    service = str(brief.get("service", "business_website")).strip()
    if service not in SERVICE_ROLES:
        raise ValueError("Unsupported service: " + service)
    root = Path(workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)
    key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")
    roles = SERVICE_ROLES[service]
    started = datetime.now(timezone.utc).isoformat()
    results: list[dict] = []

    if not key:
        results = [{
            "role": role, "status": "skipped_no_api_key", "tool_calls": 0,
            "artifact": f"agent_workspace/specialists/{_slug(role)}.md",
            "message": "No model API key configured; deterministic delivery remains available.",
        } for role in roles]
    else:
        for role in roles:
            artifact = f"agent_workspace/specialists/{_slug(role)}.md"
            role_brief = dict(brief)
            role_brief["specialist_execution"] = {
                "role": role,
                "objective": ROLE_OBJECTIVES.get(role, "Complete the role's in-scope task and document evidence."),
                "required_artifact": artifact,
                "instructions": [
                    "Work only from the supplied brief and existing local workspace artifacts.",
                    "Write your role-specific notes, concrete actions, evidence, unresolved blockers, and next acceptance checks to the required artifact.",
                    "Use the provided local tools; do not claim work that was not performed.",
                    "Do not contact clients, access external services, use credentials, spend money, publish, or deploy.",
                    "Do not overwrite reports or manifests protected by the tool layer.",
                ],
            }
            try:
                result = run_tool_agent(
                    brief=role_brief, workspace=root, api_key=key,
                    max_rounds=max_rounds_per_role,
                )
                results.append({
                    "role": role,
                    "status": result.get("status", "unknown"),
                    "tool_calls": int(result.get("tool_calls", 0) or 0),
                    "artifact": artifact if (root / artifact).is_file() else None,
                    "message": str(result.get("final_message") or result.get("message") or result.get("error") or "")[:700],
                })
                # An unavailable provider is unlikely to recover within the same run;
                # preserve the report and continue deterministic evidence handling.
                if result.get("status") in {"unavailable", "skipped_no_api_key"}:
                    break
            except Exception as exc:
                results.append({
                    "role": role, "status": "unavailable", "tool_calls": 0,
                    "artifact": None,
                    "message": f"Specialist pass unavailable: {type(exc).__name__}. Check model quota/access.",
                })
                break

    completed = sum(bool(x["status"] == "completed" and x["artifact"]) for x in results)
    report = {
        "status": "completed_with_limitations" if results and all(x["status"] == "completed" for x in results) and completed == len(roles) else
                  "skipped_no_api_key" if results and all(x["status"] == "skipped_no_api_key" for x in results) else
                  "partial_or_unavailable",
        "service": service,
        "started_at": started,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "roles_requested": roles,
        "roles_attempted": len(results),
        "roles_with_artifact": completed,
        "specialists": results,
        "tool_rounds_per_role_max": max_rounds_per_role,
        "external_actions_performed": [],
        "production_deployment_enabled": False,
        "limitations": [
            "Specialists run sequentially through a shared bounded tool layer; they are not independent background services.",
            "Model output and artifact presence do not prove a feature works; acceptance and functional tests remain required.",
            "No external messages, browsing, purchases, payments, or production deployments are available in this workflow.",
        ],
    }
    report_path = root / "specialist_execution_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report

def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="Run bounded role-specific specialist passes")
    parser.add_argument("--brief", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--rounds-per-role", type=int, default=2)
    args = parser.parse_args(argv)
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    report = run_specialist_team(brief=brief, workspace=args.workspace, max_rounds_per_role=args.rounds_per_role)
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
