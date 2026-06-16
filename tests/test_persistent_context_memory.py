from runtime.context.context_governance_registry import ContextGovernanceRegistry
from runtime.context.persistent_context_memory import PersistentContextMemory


def validated_context(context_id, concept):
    return {
        "context_name": context_id,
        "concept": concept,
        "semantic_validation": True,
        "identity_compatible": True,
        "context_confidence": 0.94,
        "status": "SEMANTICALLY_VALIDATED",
    }


def test_persistent_context_memory_retains_validated_contexts_between_cycles(
    tmp_path,
):
    storage_path = tmp_path / "context_memory.json"

    first_memory = PersistentContextMemory(storage_path=storage_path)
    first_report = ContextGovernanceRegistry(
        persistent_context_memory=first_memory,
    ).register_runtime_contexts(
        contexts=[validated_context("symmetry_context", "symmetry_reasoning")],
    )

    assert "symmetry_context" in first_report["visible_context_ids"]
    assert first_report["context_loss_events"] == 0

    second_memory = PersistentContextMemory(storage_path=storage_path)
    second_report = ContextGovernanceRegistry(
        persistent_context_memory=second_memory,
    ).register_runtime_contexts(
        contexts=[validated_context("color_context", "color_preservation")],
    )

    assert "color_context" in second_report["visible_context_ids"]
    assert "symmetry_context" in second_report["visible_context_ids"]
    assert second_report["persistent_context_count"] == 2
    assert second_report["governance_context_count"] == 2
    assert second_report["context_loss_events"] == 0
    assert second_report["persistent_context_report"]["missing_contexts"] == [
        "symmetry_context"
    ]


def test_persistent_context_memory_revocation_hides_context(tmp_path):
    storage_path = tmp_path / "context_memory.json"
    memory = PersistentContextMemory(storage_path=storage_path)
    registry = ContextGovernanceRegistry(persistent_context_memory=memory)

    registry.register_runtime_contexts(
        contexts=[validated_context("symmetry_context", "symmetry_reasoning")],
    )
    memory.revoke_context("symmetry_context")

    reloaded = PersistentContextMemory(storage_path=storage_path)
    report = ContextGovernanceRegistry(
        persistent_context_memory=reloaded,
    ).register_runtime_contexts()

    assert "symmetry_context" not in report["visible_context_ids"]
    assert report["persistent_context_count"] == 0
    assert report["context_loss_events"] == 0
