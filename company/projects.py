"""Project intake and proposal workflow with explicit approval boundaries."""
from dataclasses import dataclass

@dataclass
class ProjectBrief:
    client_name: str
    project_type: str
    business_goal: str
    required_pages: list[str]
    features: list[str]
    deadline: str
    budget_inr: float | None = None
    state: str = "lead"
    approved_quote_inr: float | None = None
    human_approved: bool = False

def qualify_project(p: ProjectBrief) -> tuple[bool, list[str]]:
    missing = []
    for key, value in (("client name", p.client_name), ("project type", p.project_type),
                       ("business goal", p.business_goal), ("deadline", p.deadline)):
        if not value or not value.strip():
            missing.append(f"Missing {key}")
    if not p.required_pages:
        missing.append("Confirm required pages")
    return not missing, missing

def estimate_range(project_type: str, page_count: int, feature_count: int) -> dict:
    base = {"landing_page": 5000, "business_website": 15000, "ecommerce": 30000, "redesign": 10000}
    if project_type not in base:
        raise ValueError("Unknown project type; request manual scoping")
    low = base[project_type] + max(0, page_count-3)*1500 + feature_count*1000
    return {"currency":"INR", "low":low, "high":round(low*1.8), "illustrative_only":True,
            "approval_required":True, "note":"Not a binding quote. Confirm scope, taxes, timeline, hosting, and revisions."}

def may_send_proposal(p: ProjectBrief) -> bool:
    return p.state == "proposal_pending_approval" and p.human_approved and p.approved_quote_inr is not None and p.approved_quote_inr >= 0
