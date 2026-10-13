"""Evidence-based agent hiring and promotion recommendations."""
from dataclasses import dataclass

@dataclass(frozen=True)
class CandidateEvidence:
    name: str
    role: str
    task_accuracy: float
    quality_score: float
    safety_score: float
    reliability_score: float
    sample_count: int
    failed_safety_checks: int = 0

@dataclass(frozen=True)
class HiringDecision:
    status: str
    score: float
    reasons: tuple[str, ...]

def evaluate_candidate(e: CandidateEvidence) -> HiringDecision:
    scores = (e.task_accuracy, e.quality_score, e.safety_score, e.reliability_score)
    if any(s < 0 or s > 100 for s in scores):
        raise ValueError("Scores must be between 0 and 100")
    if e.sample_count < 5:
        return HiringDecision("TRIAL", sum(scores)/4, ("Insufficient evidence: complete at least 5 role-specific test tasks",))
    if e.failed_safety_checks > 0 or e.safety_score < 95:
        return HiringDecision("REJECTED", sum(scores)/4, ("Safety gate failed; retrain and retest before reconsideration",))
    score = round(e.task_accuracy*.30 + e.quality_score*.30 + e.safety_score*.25 + e.reliability_score*.15, 2)
    if score >= 90 and e.task_accuracy >= 85 and e.quality_score >= 85:
        return HiringDecision("HIRED", score, ("Passed sample-size, quality, reliability, and safety gates",))
    if score >= 75:
        return HiringDecision("RETRAIN", score, ("Promising results; improve weak areas and retest",))
    return HiringDecision("REJECTED", score, ("Below hiring threshold",))

def promotion_recommendation(*, current_level: int, quality: float, reliability: float,
                             client_rating: float, completed_tasks: int, safety_incidents: int) -> str:
    if safety_incidents:
        return "HOLD_AND_REVIEW"
    if completed_tasks >= 30 and quality >= 95 and reliability >= 95 and client_rating >= 4.7:
        return f"PROMOTION_RECOMMENDED_TO_LEVEL_{current_level + 1}"
    if completed_tasks >= 10 and quality >= 90 and reliability >= 90:
        return "BONUS_RECOMMENDATION"
    return "NO_CHANGE"
