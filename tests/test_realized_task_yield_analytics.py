from copy import deepcopy

from runtime.analytics.realized_task_yield import (
    RealizedTaskYieldAnalyticsEngine,
)


def _raw(execution_id="task_execution_1", raw_id="raw_1"):
    return {
        "raw_result_id": raw_id,
        "canonical_raw_result_id": raw_id,
        "origin_task_execution_id": execution_id,
        "origin_run_id": "run_1",
        "origin_task_id": "task_1",
    }


def _accepted(
    evidence_id="accepted_1",
    execution_id="task_execution_1",
    *,
    status="ACTIVE",
    source="source_a",
    causal=False,
):
    return {
        "accepted_evidence_id": evidence_id,
        "evidence_acceptance_state": "ACCEPTED",
        "evidence_decision_id": f"decision_{evidence_id}",
        "producer_operation_id": source,
        "canonical_source_identity": source,
        "accepted_evidence_origin_state": "TASK_ORIGIN_PRESERVED",
        "accepted_evidence_origin": {
            "accepted_evidence_origin_state": "TASK_ORIGIN_PRESERVED",
            "raw_evidence_id": f"raw_{evidence_id}",
            "raw_result_id": f"raw_{evidence_id}",
            "origin_task_execution_id": execution_id,
            "origin_run_id": "run_1",
            "origin_task_id": "task_1",
            "origin_lineage_fingerprint": f"origin_fp_{evidence_id}",
            "authority": "NONE",
        },
        "accepted_evidence_current_state": {
            "accepted_evidence_id": evidence_id,
            "current_status": status,
            "is_currently_accepted": status == "ACTIVE",
            "superseded_by": "accepted_replacement"
            if status == "SUPERSEDED"
            else None,
        },
        "capability_causal_support_state": (
            "CAUSALLY_SUPPORTED" if causal else "OBSERVED_ONLY"
        ),
    }


def _assessment(*evidence):
    return {
        "capability_evidence_assessment_id": "assessment_1",
        "supporting_accepted_evidence_refs": [
            {
                "accepted_evidence_id": item["accepted_evidence_id"],
                "raw_evidence_id": item["accepted_evidence_origin"]["raw_evidence_id"],
                "origin_task_execution_id": item["accepted_evidence_origin"][
                    "origin_task_execution_id"
                ],
                "accepted_evidence_origin_state": "TASK_ORIGIN_PRESERVED",
            }
            for item in evidence
        ],
    }


def _decision(*evidence, state="PROMOTION_GRANTED", current="NOT_QUALIFIED", granted="OPERATIONALLY_OBSERVED"):
    return {
        "qualification_decision_id": "qualification_1",
        "decision_state": state,
        "current_level": current,
        "granted_level": granted,
        "reproducibility_state": "REPRODUCIBLY_SUPPORTED",
        "capability_evidence_support_lineage": [
            {
                "accepted_evidence_id": item["accepted_evidence_id"],
                "raw_evidence_id": item["accepted_evidence_origin"]["raw_evidence_id"],
                "origin_task_execution_id": item["accepted_evidence_origin"][
                    "origin_task_execution_id"
                ],
                "accepted_evidence_origin_state": "TASK_ORIGIN_PRESERVED",
            }
            for item in evidence
        ],
    }


def _report(**overrides):
    engine = RealizedTaskYieldAnalyticsEngine()
    accepted = overrides.pop("accepted_evidence", [_accepted()])
    capability_assessments = overrides.pop("capability_assessments", None)
    if capability_assessments is None:
        capability_assessments = [_assessment(*accepted)]
    qualification_decisions = overrides.pop("qualification_decisions", None)
    if qualification_decisions is None:
        qualification_decisions = [_decision(*accepted)]
    return engine.analyze_task_execution(
        task_execution_id=overrides.pop("task_execution_id", "task_execution_1"),
        run_id="run_1",
        task_id="task_1",
        raw_evidence=overrides.pop("raw_evidence", [_raw()]),
        accepted_evidence=accepted,
        capability_assessments=capability_assessments,
        qualification_decisions=qualification_decisions,
        task_outcome=overrides.pop("task_outcome", {"success": True}),
        diagnostics=overrides.pop("diagnostics", []),
        predicted_selection=overrides.pop(
            "predicted_selection",
            {"expected_information_gain_bonus": 10, "novelty_bonus": 5},
        ),
        **overrides,
    )


def test_positive_case_measures_multidimensional_current_yield():
    report = _report(accepted_evidence=[_accepted(causal=True)])
    vector = report["value_vector"]

    assert vector["raw_evidence_count"] == 1
    assert vector["accepted_evidence_count"] == 1
    assert vector["current_active_evidence_count"] == 1
    assert vector["capability_support_count"] == 1
    assert vector["qualification_support_count"] == 1
    assert vector["causal_support_count"] == 1
    assert vector["reproducibility_support_count"] == 1
    assert report["yield_class"] == "HIGH_REALIZED_YIELD"
    assert report["authority"]["selector"] == "NONE"
    assert report["selector_feedback_consumed"] is False


def test_redundant_success_is_not_high_yield():
    report = _report(
        raw_evidence=[],
        accepted_evidence=[],
        capability_assessments=[],
        qualification_decisions=[],
        task_outcome={"success": True},
    )

    assert report["yield_class"] == "ZERO_REALIZED_YIELD"
    assert report["success_failure_value_class"] == "SUCCESS_YIELD_UNKNOWN"


def test_useful_failure_receives_nonzero_diagnostic_value():
    report = _report(
        raw_evidence=[],
        accepted_evidence=[],
        capability_assessments=[],
        qualification_decisions=[],
        task_outcome={"success": False},
        diagnostics=[{"diagnostic_class": "NEW_FAILURE_CLASS"}],
    )

    assert report["yield_class"] == "LOW_REALIZED_YIELD"
    assert report["success_failure_value_class"] == (
        "FAILURE_WITH_NEW_DIAGNOSTIC_VALUE"
    )


def test_revoked_evidence_is_historical_not_current():
    revoked = _accepted(status="REVOKED")
    report = _report(accepted_evidence=[revoked])
    vector = report["value_vector"]

    assert vector["accepted_evidence_count"] == 1
    assert vector["current_active_evidence_count"] == 0
    assert vector["historical_only_evidence_count"] == 1
    assert vector["invalidated_yield_count"] == 1


def test_shared_support_is_represented_without_exclusive_causal_credit():
    first = _accepted("accepted_a", "task_execution_1")
    second = _accepted("accepted_b", "task_execution_2", source="source_b")
    report = _report(
        accepted_evidence=[first],
        capability_assessments=[_assessment(first, second)],
        qualification_decisions=[_decision(first, second)],
    )

    assert report["value_vector"]["shared_support_count"] == 1
    assert report["value_vector"]["attribution_confidence"] == (
        "STRONG_SUPPORT_LINEAGE"
    )
    assert report["qualification_advancement_support_class"] == (
        "SHARED_TASK_SUPPORT_IN_ADVANCEMENT"
    )


def test_duplicate_artifacts_do_not_inflate_evidence_yield():
    first = _accepted("accepted_a")
    duplicate = deepcopy(first)
    report = _report(accepted_evidence=[first, duplicate])

    assert report["value_vector"]["accepted_evidence_count"] == 1
    assert report["value_vector"]["current_active_evidence_count"] == 1


def test_legacy_unknown_attribution_is_unknown_not_zero():
    report = _report(
        task_execution_id="task_execution_missing",
        raw_evidence=[{"raw_result_id": "legacy_raw"}],
        accepted_evidence=[{"accepted_evidence_id": "legacy_accepted"}],
        capability_assessments=[],
        qualification_decisions=[],
    )

    assert report["yield_class"] == "UNKNOWN_REALIZED_YIELD"
    assert report["value_vector"]["attribution_confidence"] == "ATTRIBUTION_UNKNOWN"


def test_predicted_vs_realized_is_analysis_only():
    report = _report(
        predicted_selection={
            "expected_information_gain_bonus": 10,
            "novelty_bonus": 3,
            "exposure_penalty": 1,
            "recency_penalty": 1,
        }
    )

    comparison = report["predicted_vs_realized"]
    assert comparison["predicted_vs_realized_result"] == "DIRECTIONALLY_ALIGNED"
    assert comparison["novelty_vs_realized_result"] == "DIRECTIONALLY_ALIGNED"
    assert comparison["selector_feedback_consumed"] is False


def test_feedback_readiness_requires_natural_observations():
    engine = RealizedTaskYieldAnalyticsEngine()
    report = _report()
    readiness = engine.feedback_readiness([report], natural_observation_count=0)

    assert readiness["feedback_readiness"] == "PARTIALLY_READY"
    assert "INSUFFICIENT_NATURAL_OBSERVATIONS" in readiness["blockers"]
    assert readiness["authority"]["selector"] == "NONE"
