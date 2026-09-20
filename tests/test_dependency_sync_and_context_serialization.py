import json

from core.truth.truth_candidate_engine import TruthCandidatePromotionEngine
from runtime.context.context_serializer import (
    deserialize_context,
    normalize_context,
    safe_context_accessor,
    serialize_context,
)
from runtime.context import context_serialization_engine
from runtime.dependency.dependency_injection_audit import (
    DependencyInjectionAudit,
)


def test_preservation_dependency_sync_ignores_zero_placeholder():
    promotion = TruthCandidatePromotionEngine()._dependency_promotion(
        "shape_preservation",
        {
            "process_dependency_memory": {
                "dependency_confidence": 0.0,
                "dependency_chain_depth": 0,
                "dependency_chain_coverage": 0.0,
            },
            "causal_validation": {
                "dependency_promotion_evidence": {
                    "dependency_confidence": 0.91,
                    "dependency_chain_depth": 4,
                    "dependency_chain_coverage": 0.92,
                    "missing_dependencies": [],
                },
            },
        },
    )

    assert promotion["dependency_confidence"] == 0.91
    assert promotion["dependency_chain_depth"] == 4
    assert promotion["dependency_chain_coverage"] == 0.92
    assert promotion["dependency_chain_complete_for_promotion"] is True
    assert promotion["dependency_aware_promotion_applicable"] is True


def test_dependency_injection_audit_reports_block_reason():
    report = DependencyInjectionAudit().audit([
        {
            "concept": "color_preservation",
            "dependency_confidence": 0.0,
            "dependency_chain_depth": 0,
            "dependency_chain_coverage": 0.0,
        }
    ])

    audit = report["dependency_injection_audit"][0]
    assert audit["dependency_discovered"] is False
    assert audit["dependency_block_reason"] == "dependency_not_discovered"


def test_context_serializer_accepts_json_and_string_identifiers():
    serialized = serialize_context({"context_id": "shape_context", "properties": ["shape"]})
    assert deserialize_context(serialized)["context_id"] == "shape_context"

    payload = json.dumps({"context_id": "color_context", "capabilities": ["color"]})
    assert safe_context_accessor(payload, "context_id") == "color_context"

    identifier = deserialize_context("topology_context")
    assert identifier["context_id"] == "topology_context"


def test_context_serializer_treats_empty_string_as_text_context():
    normalized = normalize_context("")

    assert normalized == {
        "context_id": "",
        "context_text": "",
        "context_type": "TEXT_CONTEXT",
    }


def test_context_serializer_decoder_exception_falls_back_to_text(monkeypatch):
    def broken_json_loads(_value):
        raise AssertionError("plain text must not enter JSON decoder")

    monkeypatch.setattr(context_serialization_engine.json, "loads", broken_json_loads)

    normalized = normalize_context("NOT_DEFINED")

    assert normalized == {
        "context_id": "NOT_DEFINED",
        "context_text": "NOT_DEFINED",
        "context_type": "TEXT_CONTEXT",
    }


def test_context_serializer_nested_decoder_exception_preserves_string(monkeypatch):
    def broken_json_loads(_value):
        raise AssertionError("plain text must not enter JSON decoder")

    monkeypatch.setattr(context_serialization_engine.json, "loads", broken_json_loads)

    normalized = normalize_context({"context": "NOT_DEFINED"})

    assert normalized["context"] == "NOT_DEFINED"


def test_context_serializer_object_shaped_decoder_exception_falls_back(monkeypatch):
    def broken_json_loads(_value):
        raise StopIteration(0)

    monkeypatch.setattr(context_serialization_engine.json, "loads", broken_json_loads)

    normalized = normalize_context("{not valid json")

    assert normalized == {
        "context_id": "{not valid json",
        "context_text": "{not valid json",
        "context_type": "TEXT_CONTEXT",
    }
