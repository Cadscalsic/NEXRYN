from core.identity import IdentityContinuityEngine
from core.identity.identity_governance_policy import evaluate_identity_governance
from core.belief_engine import EpistemicCognitionLayer


def evidence_targets(report):
    return {
        evidence["target"]
        for evidence in report["dependency_evidence"]
    }


def test_object_identity_continuity_preserves_recolored_object():
    report = IdentityContinuityEngine().evaluate_objects(
        [[1]],
        [[2]],
    )

    mapping = report["object_temporal_mappings"][0]

    assert report["continuity_state"] == "OBJECT_IDENTITY_CONTINUOUS"
    assert report["identity_preserved"] is True
    assert mapping["object_t0"] == "obj_1"
    assert mapping["object_t1"] == "obj_1"
    assert mapping["identity_transition"] == "IdentityPreserved"
    assert "identity_transition:IdentityPreserved" in evidence_targets(report)


def test_object_identity_continuity_detects_split_lineage():
    report = IdentityContinuityEngine().evaluate_objects(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )

    assert report["continuity_state"] == "OBJECT_IDENTITY_SPLIT"
    assert report["identity_split"] is True
    assert report["transition_counts"]["IdentitySplit"] == 2
    assert {
        mapping["object_t1"]
        for mapping in report["object_temporal_mappings"]
        if mapping["identity_transition"] == "IdentitySplit"
    } == {"obj_1", "obj_2"}


def test_object_identity_continuity_detects_created_object():
    report = IdentityContinuityEngine().evaluate_objects(
        [],
        [[1]],
    )

    assert report["continuity_state"] == "OBJECT_IDENTITY_CREATED"
    assert report["identity_created"] is True
    assert report["object_temporal_mappings"][0]["object_t1"] == "obj_1"
    assert report["object_temporal_mappings"][0]["identity_transition"] == (
        "IdentityCreated"
    )


def test_object_identity_continuity_detects_destroyed_object():
    report = IdentityContinuityEngine().evaluate_objects(
        [[1]],
        [],
    )

    assert report["continuity_state"] == "OBJECT_IDENTITY_INTERRUPTED"
    assert report["identity_destroyed"] is True
    assert report["object_temporal_mappings"][0]["object_t0"] == "obj_1"
    assert report["object_temporal_mappings"][0]["object_t1"] is None


def test_object_identity_continuity_detects_merge_lineage():
    report = IdentityContinuityEngine().evaluate_objects(
        [[1, 0, 1]],
        [[1]],
    )

    assert report["continuity_state"] == "OBJECT_IDENTITY_MERGED"
    assert report["identity_merged"] is True
    assert "IdentityMerged" in report["transition_counts"]
    assert "identity_transition:IdentityMerged" in evidence_targets(report)


def test_identity_continuity_sequence_preserves_recolored_object_lineage():
    report = IdentityContinuityEngine().evaluate_sequence(
        [
            [[1]],
            [[2]],
            [[3]],
        ],
    )

    assert report["continuity_state"] == "IDENTITY_SEQUENCE_PRESERVED"
    assert report["identity_continuity_preserved"] is True
    assert report["identity_preserved"] is True
    assert report["identity_split"] is False
    assert report["identity_merged"] is False
    assert report["identity_governance_gates"]["identity_stable"] is True
    assert report["identity_chains"][0]["chain"] == [
        "t0:obj_1",
        "t1:obj_1",
        "t2:obj_1",
    ]
    assert (
        "temporal_identity_transition:IdentityPreserved"
        in evidence_targets(report)
    )


def test_identity_continuity_sequence_detects_temporal_split():
    report = IdentityContinuityEngine().evaluate_sequence(
        [
            [[1, 0, 0]],
            [[1, 0, 1]],
            [[1, 0, 1]],
        ],
    )

    assert report["continuity_state"] == "IDENTITY_SEQUENCE_SPLIT"
    assert report["identity_continuity_preserved"] is True
    assert report["identity_split"] is True
    assert report["identity_governance_gates"]["identity_stable"] is False
    assert report["transition_counts"]["IdentitySplit"] == 2


def test_identity_continuity_sequence_detects_temporal_merge():
    report = IdentityContinuityEngine().evaluate_sequence(
        [
            [[1, 0, 1]],
            [[1]],
            [[2]],
        ],
    )

    assert report["continuity_state"] == "IDENTITY_SEQUENCE_MERGED"
    assert report["identity_continuity_preserved"] is True
    assert report["identity_merged"] is True
    assert report["identity_governance_gates"]["identity_stable"] is False
    assert report["transition_counts"]["IdentityMerged"] >= 1


def test_identity_runtime_exports_truth_commit_context_for_preserved_lineage():
    runtime = IdentityContinuityEngine().run_identity_runtime(
        [
            [[1]],
            [[2]],
            [[3]],
        ],
    )
    context_patch = runtime["truth_commit_context_patch"]
    governance = evaluate_identity_governance(context_patch)

    assert runtime["runtime_state"] == "IDENTITY_RUNTIME_STABLE"
    assert runtime["runtime_ready"] is True
    assert context_patch["identity_continuity"] >= 0.82
    assert context_patch["semantic_drift"] < 0.58
    assert governance["identity_stable"] is True
    assert governance["semantic_spine_stable"] is True
    assert governance["identity_runtime_supported"] is True


def test_identity_runtime_tracks_split_without_marking_identity_stable():
    runtime = IdentityContinuityEngine().run_identity_runtime(
        [
            [[1, 0, 0]],
            [[1, 0, 1]],
            [[1, 0, 1]],
        ],
    )
    context_patch = runtime["truth_commit_context_patch"]
    governance = evaluate_identity_governance(context_patch)

    assert runtime["runtime_state"] == "IDENTITY_RUNTIME_TRANSFORMED"
    assert runtime["identity_split"] is True
    assert context_patch["identity_stability_report"][
        "identity_stability_state"
    ] == "identity_branching_tracked"
    assert governance["identity_stable"] is False
    assert governance["semantic_spine_stable"] is True


def test_identity_runtime_promotes_continuous_runtime_above_truth_threshold():
    class ModerateContinuityEngine(IdentityContinuityEngine):
        def evaluate_objects(self, input_grid, output_grid, source="test"):
            return {
                "continuity_score": 0.5917,
                "object_temporal_mappings": [
                    {
                        "object_t0": "obj_1",
                        "object_t1": "obj_1",
                        "identity_transition": "IdentityPreserved",
                        "continuity": 0.5917,
                        "evidence": {},
                    }
                ],
                "transition_counts": {
                    "IdentityPreserved": 1,
                },
                "tracking": {
                    "identity_runtime": {
                        "identity_spine_continuity": 0.706,
                    },
                },
                "dependency_evidence": [],
            }

    runtime = ModerateContinuityEngine().run_identity_runtime([
        [[1]],
        [[2]],
    ])
    context_patch = runtime["truth_commit_context_patch"]
    governance = evaluate_identity_governance(context_patch)

    assert runtime["runtime_state"] == "IDENTITY_RUNTIME_STABLE"
    assert runtime["runtime_ready"] is True
    assert round(runtime["identity_continuity"], 3) == 0.706
    assert runtime["semantic_drift"] < runtime["maximum_semantic_drift"]
    assert runtime["identity_split"] is False
    assert runtime["identity_merged"] is False
    assert runtime["identity_governance_gates"][
        "identity_continuity_above_limit"
    ] is True
    assert runtime["identity_governance_gates"][
        "semantic_drift_below_limit"
    ] is True
    assert governance["identity_stable"] is True
    assert governance["semantic_spine_stable"] is True
    assert governance["identity_runtime_supported"] is True


def test_identity_runtime_uses_preserved_lineage_to_bound_semantic_drift():
    class LowRawSpineEngine(IdentityContinuityEngine):
        def evaluate_objects(self, input_grid, output_grid, source="test"):
            return {
                "continuity_score": 0.5917,
                "object_temporal_mappings": [
                    {
                        "object_t0": "obj_1",
                        "object_t1": "obj_1",
                        "identity_transition": "IdentityPreserved",
                        "continuity": 0.5917,
                        "evidence": {},
                    }
                ],
                "transition_counts": {
                    "IdentityPreserved": 1,
                },
                "tracking": {
                    "identity_runtime": {
                        "identity_spine_continuity": 0.294,
                    },
                },
                "dependency_evidence": [],
            }

    runtime = LowRawSpineEngine().run_identity_runtime([
        [[1]],
        [[2]],
    ])
    sequence = runtime["sequence"]

    assert round(runtime["identity_continuity"], 3) == 0.706
    assert sequence["raw_semantic_spine_score"] == 0.294
    assert round(sequence["semantic_spine_score"], 3) == 0.706
    assert runtime["semantic_drift"] < runtime["maximum_semantic_drift"]
    assert runtime["runtime_ready"] is True
    assert runtime["runtime_state"] == "IDENTITY_RUNTIME_STABLE"


def test_belief_engine_builds_identity_runtime_context_for_identity_concept():
    layer = EpistemicCognitionLayer()
    patch = layer._identity_runtime_context(
        {
            "input_grid": [[1]],
            "output_grid": [[2]],
        },
        "object_identity_preservation",
        {
            "transformation_family": "identity_preservation",
        },
    )

    assert patch["identity_continuity"] >= 0.82
    assert patch["semantic_drift"] < 0.58
    assert patch["identity_runtime_report"]["runtime_ready"] is True
    assert patch["identity_stability_report"][
        "identity_stability_state"
    ] == "stable"
    assert patch["semantic_spine_report"][
        "semantic_spine_state"
    ] == "stable_semantic_spine"


def test_belief_engine_runs_identity_runtime_for_growth_context():
    layer = EpistemicCognitionLayer()
    patch = layer._identity_runtime_context(
        {
            "input_grid": [[1, 0]],
            "output_grid": [[1, 1]],
        },
        "growth",
        {
            "transformation_family": "growth",
            "identity_behavior": "identity_split",
        },
    )

    assert patch["identity_runtime_report"]["runtime_state"] is not None
    assert patch["identity_runtime_report"]["identity_continuity"] is not None
    assert "identity_continuity_engine_report" in patch


def test_belief_engine_runs_identity_runtime_for_replication_family():
    layer = EpistemicCognitionLayer()
    patch = layer._identity_runtime_context(
        {
            "input_grid": [[1, 0, 0]],
            "output_grid": [[1, 0, 1]],
        },
        "replication",
        {
            "transformation_family": "replication",
            "identity_behavior": "identity_split",
        },
    )

    assert patch["identity_runtime_report"]["runtime_state"] is not None
    assert patch["identity_runtime_report"]["identity_split"] is True


def test_belief_engine_identity_runtime_context_reads_task_path():
    layer = EpistemicCognitionLayer()
    patch = layer._identity_runtime_context(
        {
            "task_path": "data/training/task_001.json",
        },
        "object_identity_preservation",
        {
            "transformation_family": "identity_preservation",
        },
    )

    assert patch["identity_runtime_report"]["runtime_state"] in {
        "IDENTITY_RUNTIME_STABLE",
        "IDENTITY_RUNTIME_TRANSFORMED",
        "IDENTITY_RUNTIME_REVIEW_REQUIRED",
    }
    assert "identity_continuity_engine_report" in patch
