"""Professional customer-conversation helpers; no telephony calls are made here."""
from dataclasses import dataclass

@dataclass(frozen=True)
class CallAuthorization:
    contact_is_approved: bool
    purpose_is_approved: bool
    consent_or_lawful_basis_checked: bool
    time_window_approved: bool
    operator_authorized: bool

def may_place_call(a: CallAuthorization) -> bool:
    return all((a.contact_is_approved, a.purpose_is_approved,
                a.consent_or_lawful_basis_checked, a.time_window_approved,
                a.operator_authorized))

def greeting(company_name: str = "TradingLab03") -> str:
    return (f"Hello, you've reached {company_name}'s AI client assistant. "
            "I'm an AI assistant, and I can help understand your project and arrange the next step. "
            "Is now a convenient time to talk?")

def discovery_questions() -> list[str]:
    return [
        "What business outcome would you like the website or project to achieve?",
        "Who is your target audience?",
        "Which pages and features do you need?",
        "Do you have examples of designs you like?",
        "What is your target launch date and budget range?",
        "Would you like me to prepare a written scope for our team to review?"
    ]

def safe_response(question: str, approved_facts: dict[str, str]) -> str:
    q = question.casefold()
    if any(term in q for term in ("price", "quote", "discount", "contract", "deadline", "guarantee")):
        return "I can record your request and ask our project lead to confirm the quote or commitment in writing."
    for key, value in approved_facts.items():
        if key.casefold() in q:
            return value
    return "I don't want to guess. I'll record this question for a human project lead to confirm."
