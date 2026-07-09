from runtime.search import (
    AdaptiveSearchIntelligenceEngine,
    AdaptiveSearchIntelligenceMemory,
)


def _concept_report(count=8):
    concepts = [
        {
            "concept_id": f"concept:{index}",
            "concept_name": f"concept_{index}",
            "confidence": 0.7,
            "utility": 0.65,
        }
        for index in range(count)
    ]
    return {
        "CONCEPT_FORMATION_REPORT": True,
        "concept_count": count,
        "confidence": 0.72,
        "top_concepts": concepts,
        "concept_graph": {"nodes": concepts, "edges": []},
    }


def _program_report(count=8, validated=5):
    programs = [
        {
            "program_id": f"program:{index}",
            "program_name": f"program_{index}",
            "confidence": 0.75,
        }
        for index in range(validated)
    ]
    return {
        "PROGRAM_SYNTHESIS_REPORT": True,
        "generated_programs": count,
        "program_candidates": count,
        "programs_validated": validated,
        "winning_programs": programs,
    }


def test_adaptive_search_intelligence_generates_strategy_budget_graph(tmp_path):
    engine = AdaptiveSearchIntelligenceEngine(
        memory=AdaptiveSearchIntelligenceMemory(tmp_path / "search_memory.json"),
    )

    report = engine.build_report(
        cognitive_search_report={
            "route_ranking": [
                {"route_id": "route:a", "confidence": 0.72},
                {"route_id": "route:b", "confidence": 0.24},
            ]
        },
        concept_formation_report=_concept_report(),
        program_synthesis_report=_program_report(),
        all_results=[
            {
                "input": [[1, 2], [2, 1]],
                "output": [[2, 1], [1, 2]],
                "success": False,
            }
        ],
    )

    assert report["ADAPTIVE_SEARCH_INTELLIGENCE_REPORT"] is True
    assert report["chosen_strategy"]["strategy"]
    assert report["search_budget"]["maximum_routes"] > 0
    assert report["search_graph"]["nodes"]
    assert report["search_graph"]["edges"]
    assert report["route_decisions"]
    assert report["multi_hypothesis_management"]
    assert any(item["decision"] == "Expand" for item in report["route_decisions"])
    assert any(
        item["decision"] in {"Terminate", "Archive", "Suspend"}
        for item in report["route_decisions"]
    )
    assert any(
        item["question"] == "Why this strategy?"
        for item in report["policy_decisions"]
    )
    assert any(
        item["question"] == "Why hypotheses survived?"
        for item in report["policy_decisions"]
    )


def test_search_behaviour_differs_between_easy_and_difficult_tasks(tmp_path):
    easy_engine = AdaptiveSearchIntelligenceEngine(
        memory=AdaptiveSearchIntelligenceMemory(tmp_path / "easy_memory.json"),
    )
    hard_engine = AdaptiveSearchIntelligenceEngine(
        memory=AdaptiveSearchIntelligenceMemory(tmp_path / "hard_memory.json"),
    )

    easy = easy_engine.build_report(
        cognitive_search_report={
            "route_ranking": [{"route_id": "easy_route", "confidence": 0.8}]
        },
        concept_formation_report=_concept_report(count=1),
        program_synthesis_report=_program_report(count=1, validated=1),
        all_results=[{"input": [[1]], "output": [[1]], "success": True}],
    )
    difficult = hard_engine.build_report(
        cognitive_search_report={
            "route_ranking": [
                {"route_id": f"hard_route_{index}", "confidence": 0.35 + index * 0.02}
                for index in range(12)
            ]
        },
        concept_formation_report=_concept_report(count=18),
        program_synthesis_report=_program_report(count=14, validated=7),
        dependency_report={"chains": list(range(12))},
        causal_report={"contexts": list(range(8))},
        all_results=[
            {
                "input": [[(row + col) % 9 for col in range(9)] for row in range(9)],
                "output": [[(row * col) % 9 for col in range(9)] for row in range(9)],
                "success": False,
            }
        ],
    )

    assert easy["task_complexity"]["difficulty"] != difficult["task_complexity"]["difficulty"]
    assert (
        easy["chosen_strategy"]["strategy"]
        != difficult["chosen_strategy"]["strategy"]
    )
    assert (
        easy["search_budget"]["maximum_routes"]
        < difficult["search_budget"]["maximum_routes"]
    )
