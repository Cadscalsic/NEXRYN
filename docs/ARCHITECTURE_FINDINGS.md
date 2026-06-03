# NEXRYN Architecture Findings

## Current Active Path

The active runtime path is:

1. `main.py`
2. `runtime/pipeline.py`
3. `runtime/stages/__init__.py`
4. `runtime/stages/*`
5. `runtime/transforms/primitive_executor.py`
6. `runtime/world/world_model.py`
7. `runtime/governance/cognitive_governance_engine.py`

Any new ARC execution logic should enter through the active path first.

## Fixed In This Pass

- Consolidated `runtime/stage_registry.py` into a compatibility wrapper over
  `runtime/stages/registry.py`.
- Removed duplicated `__all__` definitions from `runtime/memory/__init__.py`.
- Added `tools/architecture_audit.py` for repeatable architecture checks.
- Confirmed `runtime/stages/__init__.py` exposes 8 active stages.
- Confirmed the runtime still reaches `NEXRYN :: EXECUTION COMPLETE`.

## High-Risk Findings

### Generated Cache Pollution

The audit found Python source files under `__pycache__/.venv`.

This is generated noise from a broad compile command and should not be considered part of
the architecture. It should be removed in a deliberate cleanup pass only.

### Duplicate Architectural Surfaces

These areas still have overlapping implementations:

- Program synthesis:
  - `core/synthesis.py`
  - `runtime/engines/program_synthesis.py`
  - `runtime/synthesis/program_synthesis_engine.py`
- Execution:
  - `runtime/transforms/primitive_executor.py`
  - `runtime/execution/execution_engine.py`
  - `runtime/synthesis/adaptive_execution_engine.py`
  - `runtime/engines/transformation_engine.py`
- Kernel:
  - `runtime/kernel/cognitive_kernel.py`
  - `runtime/cognitive_kernel/cognitive_kernel.py`

The active system should prefer:

- `runtime/engines/program_synthesis.py` for current inference synthesis.
- `runtime/transforms/primitive_executor.py` for grounded primitive execution.
- `runtime/kernel/runtime_kernel.py` for pipeline runtime state.

## Recommended Next Moves

1. Split `runtime/pipeline.py` into a lean active pipeline plus optional subsystem
   initializers.
2. Move legacy `core/*` into an explicit compatibility namespace only after import
   references are mapped.
3. Create a single execution graph runtime and route both world simulation and primitive
   execution through it.
4. Add tests for:
   - active stage order
   - stage registry compatibility
   - architecture audit invariants
   - winner anchored synthesis
   - dynamic attention allocation

## Audit Command

```powershell
python tools\architecture_audit.py
```
