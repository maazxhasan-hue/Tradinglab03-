"""Safety and claim checks for local draft assets."""
FORBIDDEN_CLAIMS = (
    "guaranteed profit", "guaranteed profits", "guaranteed return",
    "guaranteed returns", "risk-free income", "100% win rate",
    "verified trading results", "secret trading bot access",
)

def review_content(text: str) -> list[str]:
    lowered = text.casefold()
    return [claim for claim in FORBIDDEN_CLAIMS if claim in lowered]

def require_approval(state: str) -> bool:
    return state == "approved"
