from core.perception import ObjectRuntime


def test_object_runtime_represents_object_temporal_transition():
    report = ObjectRuntime().run(
        [[1, 0, 0]],
        [[1, 0, 1]],
    )

    timeline = report["object_timeline"]

    assert report["system"] == "object_runtime"
    assert report["phase"] == "PHASE_6_OBJECT_CENTRIC_COGNITION"
    assert report["runtime_state"] in {
        "OBJECT_RUNTIME_READY",
        "OBJECT_RUNTIME_PROVISIONAL",
    }
    assert report["operation"] == "duplication"
    assert timeline
    assert any(item["object_t0"] == "obj_1" for item in timeline)
    assert any(
        item["identity_transition"] == "IdentitySplit"
        for item in timeline
    )
    assert report["dependency_report"]["chain_complete"] is True
    assert report["identity_continuity_report"]["identity_split"] is True


def test_object_runtime_tracks_identity_preserved_change():
    report = ObjectRuntime().run(
        [[1, 0, 0]],
        [[2, 0, 0]],
        operation="color_remap",
    )

    timeline = report["object_timeline"][0]

    assert timeline["object_t0"] == "obj_1"
    assert timeline["object_t1"] == "obj_1"
    assert timeline["identity_transition"] == "IdentityPreserved"
    assert timeline["transition_type"] == "color_changed"
    assert report["identity_continuity_report"]["identity_preserved"] is True
