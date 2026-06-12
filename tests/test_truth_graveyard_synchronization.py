from core.truth_graveyard_synchronization import (
    LIFECYCLE_TRACE,
    TruthGraveyardSynchronizer,
)


def _conflicted_context():
    return {
        "truth_registry_report": {
            "active_truths": [
                {
                    "concept": "size_preservation",
                    "status": "ACTIVE",
                    "reusable": True,
                    "reviewed_at": "Cycle 170",
                },
                {
                    "concept": "symmetry_preservation",
                    "status": "ACTIVE",
                    "reusable": True,
                    "reviewed_at": "Cycle 170",
                },
            ],
        },
        "extinction_engine_report": {
            "extinct_traits": [
                {
                    "trait_id": "size_preservation",
                    "trait_state": "extinct",
                    "timestamp": "Cycle 142",
                },
                {
                    "trait_id": "low_fitness_abstraction",
                    "trait_state": "extinct",
                    "timestamp": "Cycle 141",
                },
            ],
            "extinction_archive": [
                {
                    "trait_id": "symmetry_preservation",
                    "reason": "archived_extinction",
                    "timestamp": "Cycle 148",
                },
            ],
        },
        "trait_recovery_report": {
            "resurrection_candidates": [
                {
                    "trait_id": "symmetry_preservation",
                    "rehearsal_state": "resurrection_candidate",
                },
            ],
            "recovered_traits": [
                {
                    "trait_id": "symmetry_preservation",
                    "recovery_status": "probationary_resurrection",
                },
            ],
        },
        "evolutionary_graveyard_report": {
            "recent_entries": [
                {
                    "id": "size_preservation",
                    "category": "strategy",
                    "reason": "extinct_trait",
                    "timestamp": "Cycle 142",
                },
                {
                    "id": "unsafe_merge",
                    "category": "merge",
                    "reason": "identity_conflict",
                    "timestamp": "Cycle 144",
                },
            ],
        },
    }


def test_truth_graveyard_audit_detects_stable_truth_extinction_conflicts():
    synchronizer = TruthGraveyardSynchronizer()

    report = synchronizer.run_cycle(_conflicted_context())

    assert report["lifecycle_trace"] == LIFECYCLE_TRACE
    assert report["truth_graveyard_conflicts"] == 2
    assert report["stale_graveyard_entries"] == 2
    assert report["resurrection_conflicts"] == 1
    assert report["auto_resurrection_performed"] is False
    assert report["governance_modified"] is False
    assert "size_preservation" in report["stale_graveyard_concepts"]
    assert "symmetry_preservation" in report["stale_graveyard_concepts"]

    size_row = next(
        row
        for row in report["audit_report"]
        if row["concept"] == "size_preservation"
    )

    assert size_row["truth_state"] == "STABLE_TRUTH"
    assert size_row["graveyard_state"] == "EXTINCT"
    assert size_row["source_of_truth"] == "truth_registry"
    assert size_row["last_update_cycle"] == "Cycle 170"


def test_synchronization_filters_public_graveyard_reports_but_keeps_raw_audit():
    synchronizer = TruthGraveyardSynchronizer()

    synchronized = synchronizer.synchronize_context_reports(
        _conflicted_context()
    )

    extinction = synchronized["extinction_engine_report"]
    graveyard = synchronized["evolutionary_graveyard_report"]
    recovery = synchronized["trait_recovery_report"]
    consistency = synchronized["truth_graveyard_consistency_report"]

    assert [
        item["trait_id"]
        for item in extinction["extinct_traits"]
    ] == ["low_fitness_abstraction"]
    assert extinction["raw_extinct_traits"]
    assert extinction["stale_extinct_traits"][0]["trait_id"] == "size_preservation"
    assert graveyard["recent_entries"][0]["id"] == "unsafe_merge"
    assert graveyard["raw_recent_entries"]
    assert recovery["recovered_traits"] == []
    assert recovery["raw_recovered_traits"]
    assert consistency["truth_graveyard_conflicts"] == 2
