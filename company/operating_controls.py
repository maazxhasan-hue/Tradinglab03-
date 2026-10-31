"""Small governance helpers for the company operating system."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Approval:
    requester: str
    action: str
    resource: str
    approver: str | None = None
    approved: bool = False
    reason: str = ""

SENSITIVE_ACTIONS = {
    "send_customer_message", "place_phone_call", "submit_bid", "sign_contract",
    "change_price", "issue_refund", "make_purchase", "start_paid_subscription",
    "publish_content", "deploy_customer_site", "access_customer_data", "change_permissions",
}

def may_execute(approval: Approval) -> tuple[bool, str]:
    if not approval.requester.strip() or not approval.action.strip() or not approval.resource.strip():
        return False, "Requester, action, and resource must be specified."
    if approval.action in SENSITIVE_ACTIONS and not approval.approved:
        return False, "Explicit human approval is required for this sensitive action."
    if approval.action in SENSITIVE_ACTIONS and (not approval.approver or approval.approver == approval.requester):
        return False, "A separate authorized approver is required."
    return True, "Allowed by this local approval check; system-level permissions and legal checks still apply."

def can_promote(*, completed_tasks: int, quality: float, reliability: float,
                safety_incidents: int, customer_rating: float) -> tuple[bool, str]:
    if safety_incidents:
        return False, "Promotion blocked: safety incident requires review."
    if completed_tasks < 30:
        return False, "Need at least 30 completed tasks for promotion review."
    if quality < 95 or reliability < 95 or customer_rating < 4.7:
        return False, "Performance thresholds not met."
    return True, "Eligible for human promotion review; this is not an automatic promotion."

def can_recommend_bonus(*, completed_tasks: int, quality: float, reliability: float,
                        safety_incidents: int) -> tuple[bool, str]:
    if safety_incidents:
        return False, "Bonus review blocked pending safety review."
    if completed_tasks < 10 or quality < 90 or reliability < 90:
        return False, "Minimum completed-task, quality, or reliability evidence not met."
    return True, "Eligible for human bonus review; no payment is made automatically."
