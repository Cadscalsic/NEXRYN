"""NEXRYN semantic runtime exports.

Exports are loaded lazily so lightweight semantic execution modules do not pull
older boundary-governance dependencies into import cycles during test discovery.
"""

from __future__ import annotations

from importlib import import_module


_EXPORTS = {
    "SemanticActivationGraph": ("runtime.semantic.activation_graph", "SemanticActivationGraph"),
    "semantic_activation_graph": ("runtime.semantic.activation_graph", "semantic_activation_graph"),
    "SemanticBoundaryEngine": ("runtime.semantic.semantic_boundary_engine", "SemanticBoundaryEngine"),
    "semantic_boundary_engine": ("runtime.semantic.semantic_boundary_engine", "semantic_boundary_engine"),
    "InvariantBoundaryEngine": ("runtime.semantic.invariant_boundary_engine", "InvariantBoundaryEngine"),
    "invariant_boundary_engine": ("runtime.semantic.invariant_boundary_engine", "invariant_boundary_engine"),
    "ExecutableSemanticIntelligence": ("runtime.semantic.executable_semantics", "ExecutableSemanticIntelligence"),
    "executable_semantics": ("runtime.semantic.executable_semantics", "executable_semantics"),
    "SemanticOperationMapper": ("runtime.semantic.semantic_operation_mapper", "SemanticOperationMapper"),
    "semantic_operation_mapper": ("runtime.semantic.semantic_operation_mapper", "semantic_operation_mapper"),
    "ExecutableCoverageTracker": ("runtime.semantic.executable_coverage", "ExecutableCoverageTracker"),
    "executable_coverage": ("runtime.semantic.executable_coverage", "executable_coverage"),
    "SemanticIntentRouter": ("runtime.semantic.semantic_intent_router", "SemanticIntentRouter"),
    "semantic_intent_router": ("runtime.semantic.semantic_intent_router", "semantic_intent_router"),
}


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attribute = _EXPORTS[name]
    value = getattr(import_module(module_name), attribute)
    globals()[name] = value
    return value


__all__ = list(_EXPORTS)
