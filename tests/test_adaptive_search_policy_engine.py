from dataclasses import dataclass, field
from pathlib import Path

from runtime.search.adaptive_search_policy import (
    AdaptiveSearchPolicyEngine,
    AdaptiveSearchPolicyMemory,
)
from runtime.search.cognitive_search_manager import SearchRoute


def _engine(tmp_path):
    return AdaptiveSearchPolicyEngine(
        memory=AdaptiveSearchPolicyMemory(
            Path(tmp_path) / "adaptive_search_policy_memory.json"
        ),
        persist_memory=False,
    )


def test_complexity_deterministically_changes_search_budget(tmp_path):
    engine = _engine(tmp_path)
    easy = engine.plan({
        "object_count": 1,
        "transformation_count": 1,
        "spatial_complexity": 0.05,
        "historical_similarity": 0.9,
        "estimated_cost": 0.1,
    })
    hard = engine.plan({
        "object_count": 12,
        "object_diversity": 1.0,
        "color_diversity": 0.8,
        "transformation_count": 6,
        "spatial_complexity": 0.9,
        "process_complexity": 0.9,
        "historical_similarity": 0.0,
        "estimated_cost": 0.95,
    })

    assert easy["ADAPTIVE_SEARCH_POLICY_REPORT"] is True
    assert (
        hard["search_budget"]["maximum_search_routes"]
        > easy["search_budget"]["maximum_search_routes"]
    )
    assert hard["task_complexity"]["complexity_score"] > easy["task_complexity"]["complexity_score"]
    assert easy["strategy_selection_reason"]
    assert hard["search_budget_reason"]


def test_online_policy_decisions_explain_adaptation(tmp_path):
    routes = [
        SearchRoute(
            route_id="r1",
            current_confidence=0.5,
            evidence_score=0.1,
            expected_information_gain=0.2,
            estimated_computational_cost=0.1,
            scores={"information_gain": 0.2},
        ),
        SearchRoute(
            route_id="r2",
            current_confidence=0.4,
            evidence_score=0.1,
            expected_information_gain=0.5,
            estimated_computational_cost=0.2,
            scores={"information_gain": 0.5},
        ),
    ]

    report = _engine(tmp_path).plan({}, routes=routes)

    assert len(report["policy_decisions"]) == 2
    assert report["policy_decisions"][1]["decision"] == "Increase Exploration"
    assert report["policy_decisions"][1]["reason"]
    assert report["search_adaptation_timeline"]
    assert report["route_allocation"]["reason"]


@dataclass
class _ReasoningBudget:
    max_active_routes: int = 3
    max_reasoning_depth: int = 4
    max_hypotheses: int = 4
    notes: list[str] = field(default_factory=list)


def test_policy_applies_to_existing_reasoning_budget(tmp_path):
    engine = _engine(tmp_path)
    report = engine.plan({
        "object_count": 8,
        "transformation_count": 5,
        "spatial_complexity": 0.7,
        "estimated_cost": 0.8,
    })
    budget = _ReasoningBudget()

    engine.apply_budget(budget, report)

    assert budget.max_active_routes == report["search_budget"]["maximum_search_routes"]
    assert budget.max_reasoning_depth <= report["search_budget"]["maximum_branch_depth"]
    assert "adaptive_search_policy_applied" in budget.notes
