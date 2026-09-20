from runtime.artifacts import (
    ArtifactEconomyEngine,
    ArtifactLifecycleEngine,
    ArtifactPersistenceLayer,
    ArtifactPromotionEngine,
    CANONICAL_LIFECYCLE,
    PROMOTION_STAGES,
    ConceptArtifact,
    CognitiveArtifact,
    EvidenceArtifact,
    ProgramArtifact,
    TruthArtifact,
)
from runtime.state.shared_cognitive_state import CognitiveKnowledgeBus, SharedCognitiveState


def test_artifact_model_exposes_common_interface():
    registry = {}
    events = []
    engine = ArtifactLifecycleEngine(registry, events)

    artifact = engine.create_published(
        store_name="concept_store",
        artifact={"id": "concept:a", "confidence": 0.8},
        owner_runtime="concept_formation_runtime",
        origin_runtime="concept_formation_runtime",
        artifact_id="concept:a",
    )

    assert issubclass(ConceptArtifact, CognitiveArtifact)
    assert issubclass(ProgramArtifact, CognitiveArtifact)
    assert issubclass(EvidenceArtifact, CognitiveArtifact)
    assert issubclass(TruthArtifact, CognitiveArtifact)
    assert artifact["artifact_id"] == "concept:a"
    assert artifact["artifact_type"] == "CONCEPT"
    assert artifact["owner_runtime"] == "concept_formation_runtime"
    assert artifact["lifecycle_state"] == "PUBLISHED"
    assert artifact["validation_status"] == "VALIDATED"
    assert artifact["publication_status"] == "PUBLISHED"
    assert artifact["immutable"] is True
    assert [event["lifecycle_state"] for event in events] == [
        "CREATED",
        "NORMALIZED",
        "VALIDATED",
        "PUBLISHED",
    ]


def test_lifecycle_engine_rejects_skipped_stages_and_wrong_ownership():
    registry = {}
    failures = []
    engine = ArtifactLifecycleEngine(registry, validation_failures=failures)
    engine.create_published(
        store_name="program_store",
        artifact={"id": "program:a", "confidence": 0.7},
        owner_runtime="program_synthesis_runtime",
        origin_runtime="program_synthesis_runtime",
        artifact_id="program:a",
    )

    engine.transition("program:a", "COMMITTED", runtime_id="truth_runtime")
    engine.create_published(
        store_name="program_store",
        artifact={"id": "program:a", "confidence": 0.9},
        owner_runtime="truth_runtime",
        origin_runtime="truth_runtime",
        artifact_id="program:a",
    )

    assert any(item["failure"] == "illegal_transition" for item in failures)
    assert any(item["failure"] == "invalid_ownership" for item in failures)
    assert registry["program:a"]["owner_runtime"] == "program_synthesis_runtime"


def test_shared_state_registers_every_runtime_output_as_canonical_artifact():
    state = SharedCognitiveState.create(mode="adaptive")
    bus = CognitiveKnowledgeBus(state)

    bus.publish(
        "concept_formation_runtime",
        {"discovered_concepts": [{"id": "concept:a", "confidence": 0.8}]},
        owner="concept_formation_runtime",
    )
    bus.publish(
        "program_synthesis_runtime",
        {
            "generated_program_objects": [
                {
                    "id": "program:a",
                    "supporting_concepts": ["concept:a"],
                    "confidence": 0.7,
                }
            ]
        },
        owner="program_synthesis_runtime",
    )
    bus.publish(
        "evidence_builder_runtime",
        {
            "evidence_objects": [
                {
                    "id": "evidence:a",
                    "supporting_concepts": ["concept:a"],
                    "supporting_programs": ["program:a"],
                    "confidence": 0.75,
                }
            ]
        },
        owner="evidence_builder_runtime",
    )

    bus.consume(
        "truth_runtime",
        ("evidence_store",),
        required=("evidence_store",),
    )
    report = state.build_artifact_lifecycle_report()

    assert report["COGNITIVE_ARTIFACT_LIFECYCLE_REPORT"] is True
    assert report["canonical_lifecycle"] == list(CANONICAL_LIFECYCLE)
    assert report["artifact_types"]["CONCEPT"] == 1
    assert report["artifact_types"]["PROGRAM"] == 1
    assert report["artifact_types"]["EVIDENCE"] == 1
    assert state.concept_store["concept:a"]["artifact_type"] == "CONCEPT"
    assert state.evidence_store["evidence:a"]["lifecycle_state"] == "CONSUMED"
    assert state.artifact_registry["concept:a"]["owner_runtime"] == "concept_formation_runtime"
    assert state.artifact_registry["program:a"]["owner_runtime"] == "program_synthesis_runtime"
    assert state.artifact_registry["evidence:a"]["owner_runtime"] == "evidence_builder_runtime"
    assert report["lineage_graph"]["nodes"]


def test_artifact_promotion_progresses_and_persistence_records_history(tmp_path):
    registry = {}
    events = []
    promotion_events = []
    promotion_failures = []
    lifecycle = ArtifactLifecycleEngine(registry, events)
    lifecycle.create_published(
        store_name="truth_candidates",
        artifact={
            "id": "truth:a",
            "confidence": 0.96,
            "reliability": 0.94,
            "supporting_evidence": [
                "evidence:1",
                "evidence:2",
                "evidence:3",
                "evidence:4",
                "evidence:5",
                "evidence:6",
            ],
                "lineage": ["evidence:1", "knowledge:a"],
                "context_references": ["context:stable", "context:task", "context:domain"],
                "dependency_references": ["dependency:a", "dependency:b", "dependency:c"],
                "validated": True,
        },
        owner_runtime="truth_runtime",
        origin_runtime="truth_runtime",
        artifact_id="truth:a",
    )

    promotion = ArtifactPromotionEngine(
        lifecycle,
        promotion_events,
        promotion_failures,
    ).evaluate("truth:a")
    persistence = ArtifactPersistenceLayer(
        registry,
        path=tmp_path / "artifacts.json",
    ).persist_eligible()

    assert promotion["promoted"] is True
    assert registry["truth:a"]["promotion_stage"] in PROMOTION_STAGES
    assert registry["truth:a"]["promotion_stage"] == "LONG_TERM_MEMORY"
    assert registry["truth:a"]["lifecycle_state"] == "COMMITTED"
    assert registry["truth:a"]["promotion_history"]
    assert persistence["persisted_artifacts"] == ["truth:a"]
    assert registry["truth:a"]["persistence_status"] == "LONG_TERM_MEMORY"


def test_promotion_rejects_unsupported_truth_candidate():
    registry = {}
    failures = []
    lifecycle = ArtifactLifecycleEngine(registry)
    lifecycle.create_published(
        store_name="truth_candidates",
        artifact={"id": "truth:weak", "confidence": 0.38, "reliability": 0.4},
        owner_runtime="truth_runtime",
        origin_runtime="truth_runtime",
        artifact_id="truth:weak",
    )

    result = ArtifactPromotionEngine(
        lifecycle,
        promotion_failures=failures,
    ).evaluate("truth:weak")

    assert result["promoted"] is False
    assert result["failure"] in {"promotion_not_eligible", "promotion_without_evidence"}
    assert registry["truth:weak"]["promotion_stage"] == "CANDIDATE"


def test_shared_state_governance_persists_stable_artifacts_and_filters_memory_inputs(tmp_path):
    state = SharedCognitiveState.create(mode="adaptive")
    bus = CognitiveKnowledgeBus(state)

    bus.publish(
        "truth_runtime",
        {
            "truth_candidates": [
                {
                    "id": "truth:a",
                    "confidence": 0.96,
                    "reliability": 0.94,
                    "supporting_evidence": [
                        "evidence:1",
                        "evidence:2",
                        "evidence:3",
                        "evidence:4",
                        "evidence:5",
                        "evidence:6",
                    ],
                    "lineage": ["evidence:1", "knowledge:a"],
                    "context_references": ["context:stable", "context:task", "context:domain"],
                    "dependency_references": ["dependency:a", "dependency:b", "dependency:c"],
                    "validated": True,
                }
            ]
        },
        owner="truth_runtime",
    )
    memory_inputs = bus.consume(
        "memory_runtime",
        (
            "truth_candidates",
            "knowledge_objects",
            "evidence_store",
            "concept_store",
            "program_store",
            "search_routes",
        ),
        required=("truth_candidates",),
    )
    governance = state.run_artifact_governance(
        persistence_path=tmp_path / "artifacts.json",
    )
    flow = state.build_artifact_flow_report()

    assert "concept_store" not in memory_inputs["artifacts"]
    assert "program_store" not in memory_inputs["artifacts"]
    assert "search_routes" not in memory_inputs["artifacts"]
    assert governance["ARTIFACT_GOVERNANCE_REPORT"] is True
    assert flow["ARTIFACT_FLOW_REPORT"] is True
    assert flow["artifacts_promoted"] == 1
    assert flow["artifacts_persisted"] == 1
    assert state.artifact_persistence_store["truth:a"]["promotion_history"]
    assert state.world_model["committed_artifacts"]
    assert state.world_model["temporary_artifacts_excluded"] is True
    assert state.dna_state["stable_artifacts"]
    assert state.dna_state["temporary_hypotheses_excluded"] is True


def test_artifact_economy_updates_value_health_and_experience():
    registry = {}
    lifecycle = ArtifactLifecycleEngine(registry)
    lifecycle.create_published(
        store_name="truth_candidates",
        artifact={
            "id": "truth:economy",
            "confidence": 0.9,
            "reliability": 0.88,
            "supporting_evidence": ["evidence:a", "evidence:b", "evidence:c"],
            "lineage": ["evidence:a", "knowledge:a"],
            "validated": True,
        },
        owner_runtime="truth_runtime",
        origin_runtime="truth_runtime",
        artifact_id="truth:economy",
    )
    economy = ArtifactEconomyEngine(registry)

    economy.record_experience(
        "truth:economy",
        success=True,
        utility=0.92,
        prediction_accuracy=0.95,
        domain="spatial_transform",
    )
    report = economy.update_all()

    artifact = registry["truth:economy"]
    assert report["ARTIFACT_ECONOMY_REPORT"] is True
    assert artifact["reuse_count"] == 1
    assert artifact["times_successful"] == 1
    assert artifact["prediction_accuracy"] == 0.95
    assert artifact["cognitive_value"] > 0.0
    assert artifact["health_state"] in {"HEALTHY", "STABLE"}
    assert artifact["artifact_experience"]["execution_domains"] == ["spatial_transform"]


def test_artifact_reuse_engine_recommends_high_value_artifacts():
    state = SharedCognitiveState.create(mode="adaptive")
    bus = CognitiveKnowledgeBus(state)

    bus.publish(
        "truth_runtime",
        {
            "truth_candidates": [
                {
                    "id": "truth:reuse",
                    "confidence": 0.97,
                    "reliability": 0.95,
                    "supporting_evidence": ["evidence:a", "evidence:b", "evidence:c"],
                    "lineage": ["evidence:a", "knowledge:a"],
                    "validated": True,
                }
            ]
        },
        owner="truth_runtime",
    )
    state.record_artifact_experience(
        "truth:reuse",
        success=True,
        utility=0.94,
        prediction_accuracy=0.93,
        domain="object_replication",
    )
    reuse = state.discover_reusable_artifacts(
        {"domain": "object_replication", "artifact_type": "TRUTH"},
        limit=3,
    )

    assert reuse["ARTIFACT_REUSE_REPORT"] is True
    assert reuse["prevents_duplicate_reasoning"] is True
    assert reuse["recommended_artifacts"][0]["artifact_id"] == "truth:reuse"
    assert reuse["explainability"]["artifacts_used"] == ["truth:reuse"]


def test_relationship_graph_competition_and_collaboration_are_observable():
    registry = {}
    economy = ArtifactEconomyEngine(registry)
    lifecycle = ArtifactLifecycleEngine(registry)
    for truth_id, confidence in (("truth:a", 0.92), ("truth:b", 0.42)):
        lifecycle.create_published(
            store_name="truth_candidates",
            artifact={
                "id": truth_id,
                "confidence": confidence,
                "reliability": confidence,
                "supporting_evidence": ["evidence:shared"],
                "lineage": ["evidence:shared"],
            },
            owner_runtime="truth_runtime",
            origin_runtime="truth_runtime",
            artifact_id=truth_id,
        )
    lifecycle.create_published(
        store_name="evidence_store",
        artifact={
            "id": "evidence:joint",
            "confidence": 0.8,
            "supporting_routes": ["route:spatial", "route:color"],
            "supporting_concepts": ["concept:spatial", "concept:color"],
        },
        owner_runtime="evidence_builder_runtime",
        origin_runtime="evidence_builder_runtime",
        artifact_id="evidence:joint",
    )

    report = economy.update_all()
    graph = report["relationship_graph"]
    relations = {edge["relation"] for edge in graph["edges"]}

    assert "contradicts" in relations or "competes" in relations
    assert "collaborates" in relations
    assert registry["truth:a"]["health_state"] in {"CONFLICTING", "STABLE", "HEALTHY"}


def test_shared_state_artifact_economy_report_feeds_meta_world_and_dna():
    state = SharedCognitiveState.create(mode="adaptive")
    bus = CognitiveKnowledgeBus(state)
    bus.publish(
        "truth_runtime",
        {
            "truth_candidates": [
                {
                    "id": "truth:meta",
                    "confidence": 0.96,
                    "reliability": 0.94,
                    "supporting_evidence": ["evidence:a", "evidence:b", "evidence:c"],
                    "lineage": ["evidence:a", "knowledge:a"],
                    "validated": True,
                }
            ]
        },
        owner="truth_runtime",
    )
    state.record_artifact_experience(
        "truth:meta",
        success=True,
        utility=0.9,
        prediction_accuracy=0.91,
        domain="meta_domain",
    )
    state.run_artifact_governance()
    report = state.build_artifact_economy_report()

    assert report["ARTIFACT_ECONOMY_REPORT"] is True
    assert report["artifact_metrics"]["reuse_rate"] > 0.0
    assert report["meta_cognition"]["widest_range_artifacts"]
    assert report["dna"]["learns_from_artifact_populations"] is True
    assert report["world_model"]["temporary_artifacts_excluded"] is True
