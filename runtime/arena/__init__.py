"""Governed cognitive candidate arena."""

from runtime.arena.arena_memory import ArenaMemory, arena_memory
from runtime.arena.candidate_diversity_analyzer import (
    CandidateDiversityAnalyzer,
    candidate_diversity_analyzer,
)
from runtime.arena.candidate_normalizer import CandidateNormalizer, candidate_normalizer
from runtime.arena.candidate_proposal_gateway import (
    CandidateProposalGateway,
    candidate_proposal_gateway,
)
from runtime.arena.candidate_scorer import CandidateScorer, candidate_scorer
from runtime.arena.candidate_simulator import CandidateSimulator, candidate_simulator
from runtime.arena.cognitive_candidate_arena import (
    CognitiveCandidateArena,
    cognitive_candidate_arena,
)
from runtime.arena.source_dominance_guard import (
    SourceDominanceGuard,
    source_dominance_guard,
)
from runtime.arena.winner_selection_policy import (
    WinnerSelectionPolicy,
    winner_selection_policy,
)

__all__ = [
    "ArenaMemory",
    "arena_memory",
    "CandidateDiversityAnalyzer",
    "candidate_diversity_analyzer",
    "CandidateNormalizer",
    "candidate_normalizer",
    "CandidateProposalGateway",
    "candidate_proposal_gateway",
    "CandidateScorer",
    "candidate_scorer",
    "CandidateSimulator",
    "candidate_simulator",
    "CognitiveCandidateArena",
    "cognitive_candidate_arena",
    "SourceDominanceGuard",
    "source_dominance_guard",
    "WinnerSelectionPolicy",
    "winner_selection_policy",
]
