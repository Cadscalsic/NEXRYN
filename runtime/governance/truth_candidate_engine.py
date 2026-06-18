"""Runtime compatibility export for truth candidate governance."""

from core.truth.truth_candidate_engine import TruthCandidatePromotionEngine


truth_candidate_engine = TruthCandidatePromotionEngine()


__all__ = [
    "TruthCandidatePromotionEngine",
    "truth_candidate_engine",
]
