"""FAQ helper grounded only in approved course facts."""
from .workflow import load_facts

def answer_faq(question: str) -> str:
    q = question.casefold()
    facts = load_facts()
    if any(w in q for w in ("price", "cost", "fee", "₹", "rupee")):
        return f"The listed course price is ₹{facts['price_inr']}. See {facts['course_url']} for details."
    if any(w in q for w in ("module", "curriculum", "syllabus", "include", "includes")):
        includes = ", ".join(facts["includes"])
        topics = ", ".join(facts["topics"])
        return f"The course has {facts['modules']} modules and includes {includes}. Topics include {topics}. Details: {facts['course_url']}"
    if any(w in q for w in ("profit", "return", "earn", "guarantee", "signal")):
        return f"The course is educational and does not guarantee profits or returns; it is not a signal service. Details: {facts['course_url']}"
    if any(w in q for w in ("link", "website", "course", "enrol", "enroll", "buy")):
        return f"Course details are available at {facts['course_url']}."
    return "I don't have a verified answer in the approved knowledge base. Please escalate to a human rather than guessing."
