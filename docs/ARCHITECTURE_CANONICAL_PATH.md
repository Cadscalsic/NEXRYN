# NEXRYN Canonical Architecture Path

This document records the active runtime path after the architecture audit.

## Active Entry Point

`main.py` is the only runtime entry point for normal execution.

Execution flow:

1. `main.py`
2. `runtime.pipeline.pipeline`
3. `runtime.stages.NEXRYN_STAGE_SEQUENCE`
4. `runtime/stages/task_loading.py`
5. `runtime/stages/grid_analysis.py`
6. `runtime/stages/object_detection.py`
7. `runtime/stages/pattern_rule.py`
8. `runtime/stages/inference.py`
9. `runtime/stages/transformation.py`
10. `runtime/stages/evaluation.py`
11. `runtime/stages/self_improvement.py`
12. `runtime.pipeline.AdaptiveCognitivePipeline.run_governance_cycle`

## Canonical Runtime Surfaces

Use these as the primary implementation surfaces:

- Stage order: `runtime/stages/__init__.py`
- Runtime state: `runtime/state/runtime_state.py`
- Runtime scheduler: `runtime/scheduler/runtime_scheduler.py`
- Primitive execution: `runtime/transforms/primitive_executor.py`
- Current inference synthesis: `runtime/engines/program_synthesis.py`
- Current transformation engine: `runtime/engines/transformation_engine.py`
- Runtime governance: `runtime/governance/cognitive_governance_engine.py`
- Executive arbitration: `runtime/executive/executive_arbitration_runtime.py`
- Attention kernel: `runtime/attention/attention_kernel.py`
- Semantic activation: `runtime/semantic/activation_graph.py`
- Ontology semantics: `runtime/semantics/semantic_ontology.py`

## Legacy Or Compatibility Surfaces

These files are retained for compatibility or older experiments:

- selected `core/*` modules are shared foundational dependencies imported by the
  active runtime; the remaining modules should be treated as experimental until
  their imports are mapped
- `runtime/runtime_state.py`
- `runtime/stage_registry.py`
- `runtime/legacy/scheduler_legacy.py`
- `runtime/cognitive_kernel/cognitive_kernel.py`
- `runtime/synthesis/program_synthesis_engine.py`
- `runtime/synthesis/adaptive_execution_engine.py`
- `runtime/execution/execution_engine.py`

New runtime behavior should not be added to legacy surfaces unless there is a specific compatibility reason.

## Audit Outcome

Resolved in this pass:

- Removed project Python source files from `__pycache__` by quarantining them as `.txt`.
- Added missing package initializers.
- Removed the `runtime/scheduler.py` naming collision by moving it to `runtime/legacy/scheduler_legacy.py`.
- Converted `runtime/runtime_state.py` into a compatibility wrapper over `runtime/state/runtime_state.py`.
- Extended `tools/architecture_audit.py` to detect:
  - project Python files inside `__pycache__`
  - copied virtualenv sources inside `__pycache__/.venv`
  - root module/package name collisions
  - missing `__init__.py` files
  - known duplicate architecture surfaces

Remaining known issue:

- `__pycache__/.venv` contains copied virtualenv Python sources. This is not part of the active runtime path, but it should be deleted manually or with explicit cleanup approval because it is a large generated artifact.
