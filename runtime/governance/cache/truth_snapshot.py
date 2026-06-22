from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass
class TruthSnapshot:

    concept_name: str
    truth_hash: str
    dependency_hash: str
    context_hash: str
    identity_hash: str
    final_commit_state: str
    identity_runtime_continuity: float
    contextual_truth_score: float
    last_validation_timestamp: str

    @classmethod
    def create(
        cls,
        concept_name,
        truth_hash,
        dependency_hash,
        context_hash,
        identity_hash,
        final_commit_state,
        identity_runtime_continuity,
        contextual_truth_score,
    ):

        return cls(
            concept_name=str(concept_name),
            truth_hash=str(truth_hash),
            dependency_hash=str(dependency_hash),
            context_hash=str(context_hash),
            identity_hash=str(identity_hash),
            final_commit_state=str(final_commit_state),
            identity_runtime_continuity=float(
                identity_runtime_continuity or 0.0
            ),
            contextual_truth_score=float(
                contextual_truth_score or 0.0
            ),
            last_validation_timestamp=datetime.utcnow().isoformat(),
        )

    def as_dict(self):

        return asdict(self)


__all__ = [
    "TruthSnapshot",
]
