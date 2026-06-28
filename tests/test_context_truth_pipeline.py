from runtime.context import (
    ContextHierarchyEngine,
    ContextRegistry,
    SemanticContextBuilder,
    validate_context_collection,
)
from runtime.truth import (
    PromotionEngine,
    TruthCandidateEngine,
    TruthCommitEngine,
    TruthEligibilityEngine,
)


DEPENDENCY_CHAIN = {
    "concept": "growth",
    "chain": ["object_core", "identity_persistence", "size_increase"],
    "resolved_dependency_chain": [
        "object_core",
        "identity_persistence",
        "size_increase",
    ],
    "dependency_chain_depth": 3,
    "dependency_chain_coverage": 0.9,
    "dependency_coherence": 0.88,
}


def test_context_is_registered_after_discovery():
    builder = SemanticContextBuilder()
    registry = ContextRegistry()

    discovery = builder.build_batch({"growth": DEPENDENCY_CHAIN})
    registered = registry.register_batch(discovery["semantic_contexts"])

    assert discovery["contexts_discovered"] == 1
    assert registered["contexts_registered"] == 1
    assert registry.report()["active_contexts"] == 1


def test_semantic_context_generated_from_dependency_chain():
    context = SemanticContextBuilder().build("growth", DEPENDENCY_CHAIN)

    assert context["context_type"] == "SEMANTIC_CONTEXT"
    assert context["dependency_score"] > 0
    assert context["confidence"] > 0


def test_context_hierarchy_created():
    context = SemanticContextBuilder().build("growth", DEPENDENCY_CHAIN)
    hierarchy = ContextHierarchyEngine().build([context])

    assert hierarchy["report_state"] == "final"
    assert hierarchy["hierarchy_depth"] >= 3
    assert hierarchy["context_hierarchy_size"] > 0


def test_promotion_values_never_return_none():
    context = SemanticContextBuilder().build("growth", DEPENDENCY_CHAIN)
    promotion = PromotionEngine().evaluate(
        "growth",
        dependency_report=DEPENDENCY_CHAIN,
        contexts=[context],
    )
    eligibility = TruthEligibilityEngine().evaluate_eligibility(
        "growth",
        promotion_report=promotion,
        contexts=[context],
    )

    assert promotion["promotion_score"] is not None
    assert promotion["candidate_ready"] is not None
    assert eligibility["eligible_for_truth_candidate"] is not None


def test_truth_candidate_generated_when_evidence_sufficient():
    context = {
        **SemanticContextBuilder().build("growth", DEPENDENCY_CHAIN),
        "confidence": 0.9,
        "causal_score": 0.9,
        "identity_score": 0.9,
        "stability_score": 0.9,
    }
    promotion = PromotionEngine().evaluate(
        "growth",
        dependency_report=DEPENDENCY_CHAIN,
        contexts=[context],
    )
    eligibility = TruthEligibilityEngine().evaluate_eligibility(
        "growth",
        promotion_report=promotion,
        contexts=[context],
    )
    candidate = TruthCandidateEngine().generate(
        "growth",
        promotion_report=promotion,
        eligibility_report=eligibility,
        contexts=[context],
    )

    assert candidate["report_state"] == "final"
    assert candidate["candidate_generated"] is True
    assert candidate["truth_candidates"]


def test_truth_commit_generated_when_candidate_valid():
    candidate = {
        "concept": "growth",
        "candidate_confidence": 0.94,
        "dependency_support": 0.94,
        "context_support": 0.92,
        "causal_support": 0.9,
        "identity_support": 0.9,
        "contradiction_score": 0.0,
        "promotion_score": 0.93,
        "candidate_state": "TRUTH_CANDIDATE",
    }

    report = TruthCommitEngine().commit([candidate])

    assert report["report_state"] == "final"
    assert report["committed_truths"]
    assert report["truth_committed"] is True


def test_empty_reports_always_include_explanation():
    discovery = SemanticContextBuilder().build_batch({})
    hierarchy = ContextHierarchyEngine().build([])
    candidate = TruthCandidateEngine().generate(
        "growth",
        promotion_report={"candidate_ready": False},
        eligibility_report={"eligible_for_truth_candidate": False},
    )
    commit = TruthCommitEngine().commit([])

    for report in (discovery, hierarchy, candidate, commit):
        assert report["report_state"] == "final"
        assert report["reason"]


def test_context_loss_telemetry_can_be_computed():
    builder = SemanticContextBuilder()
    registry = ContextRegistry()
    discovery = builder.build_batch({"growth": DEPENDENCY_CHAIN})
    registered = registry.register_batch([
        {**discovery["semantic_contexts"][0], "confidence": 0.0}
    ])

    context_lost = (
        discovery["contexts_discovered"]
        - registered["contexts_registered"]
    )

    assert registered["contexts_rejected"] == 1
    assert context_lost == 1


def test_malformed_contexts_are_rejected_without_crashing_hierarchy():
    context = SemanticContextBuilder().build("growth", DEPENDENCY_CHAIN)
    hierarchy = ContextHierarchyEngine().build([
        17,
        None,
        "bad_context",
        context,
    ])

    assert hierarchy["report_state"] == "final"
    assert hierarchy["contexts_received"] == 4
    assert hierarchy["contexts_valid"] == 1
    assert hierarchy["contexts_rejected"] == 3
    assert hierarchy["result_count"] == 1
    assert hierarchy["context_hierarchy_size"] > 0
    assert hierarchy["context_rejection_reasons"][0]["received_type"] == "int"


def test_truth_pipeline_ignores_malformed_contexts():
    context = {
        **SemanticContextBuilder().build("growth", DEPENDENCY_CHAIN),
        "confidence": 0.9,
        "causal_score": 0.9,
        "identity_score": 0.9,
        "stability_score": 0.9,
    }
    contexts = [1, False, context]
    promotion = PromotionEngine().evaluate(
        "growth",
        dependency_report=DEPENDENCY_CHAIN,
        contexts=contexts,
    )
    eligibility = TruthEligibilityEngine().evaluate_eligibility(
        "growth",
        promotion_report=promotion,
        contexts=contexts,
    )
    candidate = TruthCandidateEngine().generate(
        "growth",
        promotion_report=promotion,
        eligibility_report=eligibility,
        contexts=contexts,
    )

    assert promotion["contexts_valid"] == 1
    assert promotion["contexts_rejected"] == 2
    assert eligibility["contexts_valid"] == 1
    assert candidate["contexts_valid"] == 1
    assert candidate["candidate_generated"] is True


def test_context_validator_rejects_scalars():
    contexts, telemetry = validate_context_collection([
        1,
        2.0,
        True,
        "context",
        None,
        {"context_id": "valid_context"},
    ])

    assert contexts == [{"context_id": "valid_context"}]
    assert telemetry["contexts_received"] == 6
    assert telemetry["contexts_valid"] == 1
    assert telemetry["contexts_rejected"] == 5


def test_context_registry_rejects_scalar_batch_entries():
    registry = ContextRegistry()
    report = registry.register_batch([
        4,
        {"context_id": "valid", "confidence": 0.8},
    ])

    assert report["contexts_received"] == 2
    assert report["contexts_valid"] == 1
    assert report["contexts_registered"] == 1
    assert report["contexts_rejected"] == 1
    assert report["context_rejection_reasons"][0]["received_type"] == "int"
