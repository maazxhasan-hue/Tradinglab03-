"""Role registry for a bounded software delivery team; external agents are not connected."""
from dataclasses import dataclass

@dataclass(frozen=True)
class AgentRole:
    name: str
    mission: str
    outputs: tuple[str, ...]
    must_escalate: tuple[str, ...]

DEV_TEAM = (
    AgentRole("Product Lead","Turn goals into testable requirements.",("PRD","acceptance criteria"),("unclear scope","new paid commitment")),
    AgentRole("Architect","Design isolated modules, interfaces, and failure handling.",("architecture note","API contracts"),("cross-project access","credential boundary change")),
    AgentRole("Research Engineer","Create source-attributed research and label uncertainty.",("research brief","source list"),("unverified claims","restricted data")),
    AgentRole("Backend Engineer","Implement tested business logic and opt-in adapters.",("code","API contract"),("payments","external side effects")),
    AgentRole("Frontend Engineer","Build accessible dashboard and operator controls.",("UI components","accessibility checks"),("new data collection","account permissions")),
    AgentRole("AI/Agent Engineer","Route bounded tasks and maintain scoped memory/tool access.",("agent workflow","evaluation suite"),("tool escalation","prompt injection")),
    AgentRole("QA Engineer","Run unit, integration, regression, and failure tests.",("test report","repro steps"),("failed safety tests","unverified release")),
    AgentRole("Security Engineer","Review permissions, secrets, dependencies, and audit logs.",("threat model","security checklist"),("secret exposure","unauthorized access")),
    AgentRole("Content & Media Producer","Draft educational scripts and media QA checklists.",("scripts","captions","shot list"),("fake testimonials","unlicensed media")),
    AgentRole("SEO & Growth Analyst","Propose ethical discovery experiments using verified metrics.",("SEO plan","experiment brief"),("spam","paid spend")),
    AgentRole("Customer Support Analyst","Answer only from approved facts and escalate unknowns.",("FAQ drafts","escalation queue"),("payment dispute","personal data")),
    AgentRole("Finance & Revenue Analyst","Track verified receipts, refunds, costs, and revenue gates.",("revenue ledger","unit economics"),("unverified revenue","refund/price changes")),
    AgentRole("Release Manager","Require passing tests, security review, owner approval, and rollback.",("release checklist","release notes"),("failed gates","production change")),
    AgentRole("Independent Red-Team Reviewer","Challenge safety boundaries and claims before release.",("risk findings","block/allow recommendation"),("unresolved critical finding",)),
)

def get_team():
    return [{"name": r.name, "mission": r.mission, "outputs": list(r.outputs),
             "must_escalate": list(r.must_escalate)} for r in DEV_TEAM]

def release_gate(*, tests_pass: bool, security_approved: bool, owner_approved: bool,
                 rollback_ready: bool, critical_findings: int):
    blockers = []
    if not tests_pass: blockers.append("Tests have not passed")
    if not security_approved: blockers.append("Security review is not approved")
    if not owner_approved: blockers.append("Owner approval is missing")
    if not rollback_ready: blockers.append("Rollback plan is missing")
    if critical_findings > 0: blockers.append("Critical red-team findings remain")
    return not blockers, blockers
