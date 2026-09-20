import pytest

from runtime.learning.training_report import (
    build_training_report,
    first_positive_numeric,
    first_valid_numeric,
    optional_numeric_average,
    safe_optional_float,
    safe_required_count,
)


def test_optional_float_preserves_absence_zero_invalid_and_nonfinite():
    assert safe_optional_float(None).to_dict() == {
        "value": None,
        "available": False,
        "valid": False,
        "finite": False,
        "status": "UNAVAILABLE",
    }
    assert safe_optional_float(0.0).to_dict() == {
        "value": 0.0,
        "available": True,
        "valid": True,
        "finite": True,
        "status": "AVAILABLE",
    }
    assert safe_optional_float("abc").status == "INVALID"
    assert safe_optional_float(True).status == "INVALID_BOOL"
    assert safe_optional_float(float("nan")).status == "NONFINITE"
    assert safe_optional_float(float("inf")).status == "NONFINITE"


@pytest.mark.parametrize(
    ("value", "expected_status", "expected_value"),
    [
        (0, "AVAILABLE", 0),
        (1, "AVAILABLE", 1),
        ("3", "AVAILABLE", 3),
        (None, "UNAVAILABLE", None),
        (True, "INVALID_BOOL", None),
        (False, "INVALID_BOOL", None),
        (float("nan"), "NONFINITE", None),
        (float("inf"), "NONFINITE", None),
        ("0.5", "INVALID", None),
    ],
)
def test_required_count_contract(value, expected_status, expected_value):
    normalized = safe_required_count(value)

    assert normalized.status == expected_status
    assert normalized.value == expected_value


def test_first_valid_and_first_positive_numeric_contracts():
    assert first_valid_numeric(None, "bad", 0.0).to_dict() == {
        "value": 0.0,
        "available": True,
        "valid": True,
        "finite": True,
        "status": "AVAILABLE",
    }
    positive = first_positive_numeric(None, 0.0, float("nan"), 0.7)
    assert positive.value == 0.7

    zero_only = first_positive_numeric(0.0)
    assert zero_only.available is True
    assert zero_only.status == "NO_POSITIVE_VALUE"


def test_optional_numeric_average_excludes_unavailable_and_nonfinite():
    mixed = optional_numeric_average([0.8, None, 0.6, "bad", float("nan")])
    assert mixed.value == 0.7

    missing = optional_numeric_average([None, "bad", float("inf")])
    assert missing.value is None
    assert missing.status == "UNAVAILABLE"

    zero = optional_numeric_average([0.0])
    assert zero.value == 0.0
    assert zero.status == "AVAILABLE"


def test_training_report_context_synthesis_ignores_missing_existing_strength():
    report = build_training_report(
        multi_task_results=[
            {
                "task": "context_strength_none_task",
                "status": "completed",
                "result": {
                    "truth_candidate_report": {
                        "evaluations": [
                            {
                                "concept": "shape_growth",
                                "candidate_ready": True,
                                "promotion_score": None,
                                "context_strength": None,
                                "context_discovery": {
                                    "system": "process_context_discovery_engine",
                                    "concept": "shape_growth",
                                    "context_name": "shape_growth_context",
                                    "transition_family": [
                                        {
                                            "from": "CANDIDATE",
                                            "to": "TRUTH_CANDIDATE",
                                        }
                                    ],
                                    "preconditions": [
                                        {
                                            "metric": "candidate_ready",
                                            "satisfied": True,
                                        }
                                    ],
                                    "expected_outcomes": [
                                        {
                                            "stage": "TRUTH_CANDIDATE",
                                            "eligible_for_truth_candidate": True,
                                        }
                                    ],
                                },
                            }
                        ]
                    }
                },
            }
        ],
    )

    synthesized = report["context_discovery_reports"]["shape_growth"]
    assert synthesized["context_confidence"] > 0.0
    assert (
        report["semantic_context_reports"]["shape_growth"]["semantic_context_score"]
        > 0.0
    )
    availability = synthesized["numeric_availability"]
    assert availability["context_strength"]["status"] == "UNAVAILABLE"
    assert availability["promotion_score"]["status"] == "UNAVAILABLE"


def test_training_report_truth_commit_reuse_ignores_missing_positive_scores():
    report = build_training_report(
        include_truth_evaluations=True,
        multi_task_results=[
            {
                "task": "truth_commit_none_scores_task",
                "status": "completed",
                "result": {
                    "truth_candidate_report": {
                        "evaluations": [
                            {
                                "concept": "stable_shape_growth",
                                "candidate_ready": True,
                                "promotion_score": None,
                                "dependency_confidence": None,
                                "dependency_chain_coverage": None,
                                "promotion_dependency_score": None,
                                "semantic_context": {
                                    "semantic_context_score": 0.92,
                                },
                                "context_hierarchy": {
                                    "context_hierarchy_score": 0.93,
                                },
                                "contextual_truth": {
                                    "contextual_truth_score": 0.94,
                                },
                            }
                        ]
                    },
                    "cognition_report": {
                        "evaluations": [
                            {
                                "concept": "stable_shape_growth",
                                "truth_commit": {
                                    "decision": "READY_FOR_TRUTH_COMMIT",
                                    "metadata": {
                                        "contextual_truth": {
                                            "when_valid": ["shape_growth_context"],
                                        }
                                    },
                                },
                            }
                        ]
                    },
                },
            }
        ],
    )

    assert "stable_shape_growth" in report["truth_commit_evaluations"]
    assert report["truth_commit_engine_report"]["truth_committed"] is True
    committed = report["truth_commit_engine_report"]["committed_truths"][0]
    assert committed["dependency_confidence"] == 0.94
    availability = committed["numeric_availability"]
    assert availability["dependency_confidence"]["status"] == "UNAVAILABLE"
    assert availability["dependency_chain_coverage"]["status"] == "UNAVAILABLE"
    assert availability["promotion_dependency_score"]["status"] == "UNAVAILABLE"


@pytest.mark.parametrize(
    "bad_count",
    [
        None,
        "",
        "NOT_DEFINED",
        "N/A",
        "unknown",
        "none",
        "null",
        "abc",
        "0.5x",
        True,
        False,
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_training_report_knowledge_reuse_counts_reject_unavailable_values(
    bad_count,
):
    report = build_training_report(
        include_truth_evaluations=True,
        concept_lifecycle_report={"context_hits": bad_count},
        multi_task_results=[
            {
                "task": "truth_commit_bad_count_task",
                "status": "completed",
                "result": {
                    "truth_candidate_report": {
                        "evaluations": [
                            {
                                "concept": "stable_context_reuse",
                                "candidate_ready": True,
                                "semantic_context": {
                                    "semantic_context_score": 0.92,
                                },
                                "context_hierarchy": {
                                    "context_hierarchy_score": 0.93,
                                },
                                "contextual_truth": {
                                    "contextual_truth_score": 0.94,
                                },
                            }
                        ]
                    },
                    "cognition_report": {
                        "evaluations": [
                            {
                                "concept": "stable_context_reuse",
                                "truth_commit": {
                                    "decision": "READY_FOR_TRUTH_COMMIT",
                                    "metadata": {},
                                },
                            }
                        ]
                    },
                },
            }
        ],
    )

    assert report["knowledge_reuse_report"]["context_hits"] == 0
