# NEXRYN Architecture Audit

## Latest Audit Pass

The latest audit normalized the active runtime path and removed the most confusing source-layout issues.

Current clean signals:

- `project_python_files_inside_pycache_count`: `0`
- `shadowed_root_modules`: `[]`
- `missing_package_initializers`: `[]`
- active stage count: `8`

Actions applied:

- Quarantined Python source files that were incorrectly stored inside `__pycache__`.
- Added package initializers for `core`, `core/state`, `runtime/routing`, `runtime/temporal`, and `tests/models`.
- Moved the shadowing `runtime/scheduler.py` file to `runtime/legacy/scheduler_legacy.py`.
- Replaced `runtime/runtime_state.py` with a compatibility wrapper to the canonical `runtime/state/runtime_state.py`.
- Extended `tools/architecture_audit.py` to detect pycache source leaks, package initializer gaps, and root module/package collisions.

See `docs/ARCHITECTURE_CANONICAL_PATH.md` for the canonical runtime path.

## Active Runtime Path

The active execution path is:

1. `main.py`
2. `runtime.pipeline.AdaptiveCognitivePipeline`
3. `runtime.stages.NEXRYN_STAGE_SEQUENCE`
4. stage modules under `runtime/stages`
5. transform execution through `runtime/transforms/primitive_executor.py`

`runtime/stages/__init__.py` is the canonical source for stage order, stage priority,
stage category, and stage governance metadata.

## Fixed During Audit

- `runtime/pipeline.py` no longer duplicates the stage list manually.
- `runtime/pipeline.py` now builds stages from `NEXRYN_STAGE_SEQUENCE`.
- `runtime/pipeline.py` now exposes `build_pipeline_report()`, which `main.py --verbose`
  already expected.
- `.gitignore` now excludes generated Python cache files, virtual environments, runtime
  output folders, and the local error log.
- `runtime/stage_registry.py` is now a compatibility wrapper over
  `runtime/stages/registry.py`, reducing duplicate registry behavior while keeping old
  method names available.
- `runtime/memory/__init__.py` no longer defines `__all__` twice.
- `tools/architecture_audit.py` now provides a repeatable local audit for duplicate
  architectural surfaces, cache pollution, and active stage path status.

## Duplication Map

These modules overlap architecturally and should not all be treated as equal active
runtime paths:

- Active synthesis for inference:
  `runtime/engines/program_synthesis.py`
- Legacy or broader synthesis subsystem:
  `runtime/synthesis/program_synthesis_engine.py`
- Active primitive execution:
  `runtime/transforms/primitive_executor.py`
- Fallback transformation layer:
  `runtime/engines/transformation_engine.py`
- High-level execution abstraction:
  `runtime/execution/execution_engine.py`
- Adaptive synthesis execution layer:
  `runtime/synthesis/adaptive_execution_engine.py`

Recommended rule: new ARC grid transformations should go through
`runtime/transforms/primitive_executor.py` first, then be grounded by inference rewards.
The other execution modules should be treated as fallback or experimental until they are
explicitly wired into the active stage path.

## Stage Registry Duplication

There are two stage registry implementations:

- `runtime/stage_registry.py`
- `runtime/stages/registry.py`

`runtime/stages/registry.py` is the canonical implementation. `runtime/stage_registry.py`
is now only a compatibility wrapper for older call sites. The active stage ordering still
lives in `runtime/stages/__init__.py`.

## Generated Artifact Risk

Running broad commands such as `python -m compileall .` touches `.venv` and creates cache
noise. Prefer targeted checks:

```powershell
python -m py_compile main.py runtime\pipeline.py runtime\stages\inference.py
```

Run the architecture audit with:

```powershell
python tools\architecture_audit.py
```

Known generated-artifact issue: a prior broad compile produced Python files under
`__pycache__/.venv`. They should be removed manually only when doing an explicit cleanup
pass, not during behavioral refactors.

## Next Refactor Order

1. Consolidate duplicate stage registries into one compatibility wrapper.
2. Mark `runtime/synthesis/program_synthesis_engine.py` as legacy or migrate its useful
   operator library into the active `runtime/engines/program_synthesis.py`.
3. Create a single execution graph runtime and route both `primitive_executor` and
   `world_model_engine` through it.
4. Add tests around the active pipeline order, winner anchored synthesis, and operator
   reward feedback.
5. Split `runtime/pipeline.py` imports into a lean active path and optional subsystem
   initializers to reduce working-memory pressure during normal task execution.
