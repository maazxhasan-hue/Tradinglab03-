"""Business needs analyst: turn approved company observations into ethical service leads."""
from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class BusinessObservation:
    business_name: str
    website_url: str
    observed_needs: tuple[str, ...]
    evidence: tuple[str, ...]
    source_checked_by_human: bool = False

@dataclass(frozen=True)
class BusinessOpportunity:
    business_name: str
    website_url: str
    services: tuple[str, ...]
    rationale: tuple[str, ...]
    confidence: str
    outreach_draft: str
    needs_human_verification: bool = True

SERVICE_MAP = {
    "no website": ("business website", "landing page"),
    "outdated website": ("website redesign", "accessibility audit"),
    "slow website": ("performance optimization",),
    "not mobile friendly": ("responsive redesign",),
    "no booking": ("booking/contact workflow",),
    "no online store": ("e-commerce website",),
    "poor search visibility": ("SEO audit", "content plan"),
    "no video": ("short-form video package",),
    "manual repetitive process": ("business automation",),
    "unclear services": ("website copy refresh",),
}

def analyze_business(o: BusinessObservation) -> BusinessOpportunity:
    needs = tuple(n.strip().casefold() for n in o.observed_needs if n.strip())
    mapped, evidence = [], []
    for need in needs:
        for trigger, services in SERVICE_MAP.items():
            if trigger in need:
                mapped.extend(services)
                evidence.append(f"Observed need: {need}")
    unique_services = tuple(dict.fromkeys(mapped))
    if not unique_services:
        confidence = "low"
        rationale = ("No specific service need matched; do not invent a problem.",)
        draft = (f"Hello {o.business_name}, I am an AI assistant for TradingLab03. "
                 "We help businesses with websites, content, and automation. "
                 "Would a short, no-obligation discussion be useful? Please ignore this if not relevant.")
    else:
        confidence = "medium" if o.source_checked_by_human else "low"
        rationale = tuple(evidence)
        service_text = ", ".join(unique_services)
        draft = (f"Hello {o.business_name}, I am an AI assistant for TradingLab03. "
                 f"We may be able to help with {service_text}, based on these observed needs: "
                 f"{'; '.join(evidence)}. If this is relevant, would you like a short discussion? "
                 "I can send a scope for your review. No assumptions about your budget or timeline.")
    return BusinessOpportunity(o.business_name, o.website_url, unique_services, rationale,
                               confidence, draft)

def can_contact(opportunity: BusinessOpportunity, *, consent_or_lawful_basis_checked: bool,
                channel_approved: bool, human_approved_message: bool) -> bool:
    return all((consent_or_lawful_basis_checked, channel_approved, human_approved_message))

def to_dict(opportunity: BusinessOpportunity) -> dict:
    return asdict(opportunity)
