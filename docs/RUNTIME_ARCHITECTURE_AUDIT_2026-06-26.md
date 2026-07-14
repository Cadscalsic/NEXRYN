# NEXRYN Runtime Architecture Audit

Audit date: 2026-06-26

Scope: static repository inspection, import/call graph sampling, existing audit tool output, and one constrained runtime execution:

```powershell
python main.py --mode fast --training-batch-size 1 --max-concepts 2 --report-level minimal --disable-telemetry --stats --contexts --truths --candidates
```

Runtime sample log: `runtime/artifacts/runtime_data/architecture_audit_sample.log`.

## Executive Findings

The actual runtime is not the clean modular pipeline described by the canonical architecture doc. The active entry path is:

```text
BOOT
main.py
runtime.pipeline compatibility shim
runtime.pipeline.legacy_pipeline.pipeline
AdaptiveCognitivePipeline.run()
prepare_task_run()
boot_runtime()
adaptive_reuse evaluation
meta supervisor cycle
legacy stage cycle
post-stage conditional reasoning/context/governance/finalization
main.py post-success evaluation/shutdown wrapper
diagnostics
SHUTDOWN
```

The modular pipeline under `runtime/pipeline/*.py` exists and is tested, but normal `main.py` execution still targets `runtime/pipeline/legacy_pipeline.py` through the shim in `runtime/pipeline.py`.

The runtime loads a large number of subsystems eagerly. Many are instantiated or imported by the legacy pipeline but do not necessarily execute in every mode. Fast mode actively executes the stage pipeline but can bypass deep reasoning, process semantics, governance, truth promotion, context discovery, telemetry, and finalization work after episode completion.

The most important dead or weak layers observed in the sample run:

- `context_count = 0`
- `Stable Truths = 0`
- `Truth Candidates = 0`
- `Truth Commit Entries = 0`
- `cache_hits = 0`
- `reuse_rate = 0.0`
- `dependency_chains_executed = 0`
- `dependency_chain_depth = 0`
- `dependency_chain_coverage = 0.0`
- context diagnostics reported: `No context data available.`
- truth candidate diagnostics reported: `No truth candidate data available.`

## Active Runtime Execution Graph

Observed normal `main.py` graph:

```text
BOOT
  print_runtime_banner()
  RuntimeWatchdog initialized
  TrainingAssistant selects task batch
  CacheManager may detect legacy cache but skips migration unless requested

TASK_SELECTION
  training assistant selects ARC task files

TASK_EXECUTION
  pipeline.run(...)

PIPELINE_PREP
  configure_reasoning_budget()
  prepare_task_run()
  seed reusable truth commitments from epistemic decision layer

BOOT_RUNTIME
  world_governance_kernel.build_report()
  cognitive_budget_controller.assign_budget()
  knowledge_strategy_reuse_engine.find_reusable_strategy()
  knowledge_reuse_gate.evaluate()
  incentive_reporter.build_report()
  semantic_memory_retriever.index_memory()
  semantic_cluster_engine.cluster_memory()
  context_delta_engine.detect_changes()

ADAPTIVE_REUSE
  AdaptiveReuseEngine.evaluate_reuse()
  conditionally sets skip_redundant_reasoning and dependency_reasoning_skipped

META_SUPERVISION
  MetaSupervisor.supervise()
  can block reasoning, program synthesis, context discovery, governance, and self improvement

LEGACY_STAGE_CYCLE
  task_loading
  grid_analysis
  object_detection
  pattern_rule
  inference
  transformation
  evaluation
  self_improvement, conditional and skipped after terminal success or meta block

POST_STAGE_BRANCHES
  If cached success or post_success_shutdown: fast shutdown path
  Else if memory-first reuse: reasoning/governance placeholders and finalize
  Else:
    run_reasoning_cycle(), conditional
    run_dependency_reasoning_cycle(), conditional
    run_process_semantic_cycle(), conditional
    run_governance_cycle(), conditional
    run_safe_self_repair_cycle()
    early_exit_controller.evaluate()
    run_health_cycle(), conditional
    finalize_runtime(), conditional

REPORTING
  performance_report()
  cache_metrics_report
  performance intelligence report
  training_report aggregation
  diagnostics bridge

MAIN_POST_SUCCESS
  EvaluationController.evaluate()
  ShutdownController.execute_shutdown(exit_process=False)
  RuntimeDiagnostics read-only commands

SHUTDOWN
  shutdown_controller.exit_enforcer.enforce_exit()
```

## Subsystem Inventory

Representative inventory of the systems that matter to current runtime behavior:

```json
[
  {
    "system": "main runtime",
    "status": "ACTIVE",
    "location": "main.py",
    "entry_points": ["python main.py", "build_runtime_metadata", "safe_print_context"],
    "dependencies": ["runtime.pipeline", "runtime.learning.training_assistant", "runtime.learning.training_report", "runtime.diagnostics", "runtime.evaluation", "runtime.shutdown"],
    "reports_generated": ["runtime_metadata", "performance_report", "performance_intelligence_report", "training_report", "diagnostic output"],
    "execution_frequency": "unconditional for CLI runs"
  },
  {
    "system": "pipeline compatibility shim",
    "status": "ACTIVE / PARTIALLY_CONNECTED",
    "location": "runtime/pipeline.py",
    "entry_points": ["pipeline.run", "AdaptiveCognitivePipeline lazy attribute", "run_pipeline"],
    "dependencies": ["runtime.pipeline.legacy_pipeline", "runtime.pipeline.pipeline_runner"],
    "reports_generated": [],
    "execution_frequency": "unconditional import bridge"
  },
  {
    "system": "legacy adaptive cognitive pipeline",
    "status": "ACTIVE / UNSAFE_TO_DISABLE",
    "location": "runtime/pipeline/legacy_pipeline.py",
    "entry_points": ["AdaptiveCognitivePipeline.run", "pipeline global"],
    "dependencies": ["runtime.stages", "runtime.cache", "runtime.context", "runtime.truth", "runtime.governance", "runtime.memory", "core.*"],
    "reports_generated": ["performance_report", "cache_metrics_report", "governance_report", "process_semantic_report", "dependency_reasoning_report", "adaptive_reuse_report"],
    "execution_frequency": "per task"
  },
  {
    "system": "modular pipeline runner",
    "status": "PARTIALLY_CONNECTED / SAFE_TO_DISABLE for main.py path",
    "location": "runtime/pipeline/pipeline_runner.py",
    "entry_points": ["run_modular_pipeline", "ModularPipelineRunner.run"],
    "dependencies": ["runtime.pipeline.*Stage classes"],
    "reports_generated": ["PipelineContext.execution_metadata.stage_results"],
    "execution_frequency": "tests and explicit use_legacy=False only"
  },
  {
    "system": "legacy stage sequence",
    "status": "ACTIVE / UNSAFE_TO_DISABLE",
    "location": "runtime/stages/__init__.py and runtime/stages/*.py",
    "entry_points": ["NEXRYN_STAGE_SEQUENCE"],
    "dependencies": ["task loading", "grid analysis", "object detection", "pattern/rule", "inference", "transformation", "evaluation", "self improvement"],
    "reports_generated": ["task reports", "inference report", "world model report", "evaluation result", "introspection/failure reports"],
    "execution_frequency": "per task; self improvement conditional"
  },
  {
    "system": "runtime diagnostics",
    "status": "REPORT_ONLY",
    "location": "runtime/diagnostics.py",
    "entry_points": ["RuntimeDiagnostics.stats", "audit", "contexts", "truths", "candidates"],
    "dependencies": ["final results dict"],
    "reports_generated": ["console diagnostics"],
    "execution_frequency": "only when CLI flags are supplied"
  },
  {
    "system": "training report aggregator",
    "status": "REPORT_ONLY / PARTIALLY_CONNECTED",
    "location": "runtime/learning/training_report.py",
    "entry_points": ["build_training_report", "print_training_report"],
    "dependencies": ["multi_task_results", "ledger_report", "concept_lifecycle_report"],
    "reports_generated": ["concept_memory", "truth_candidate_evaluations", "truth_commit_evaluations", "context_*_reports", "architecture_bottleneck_report"],
    "execution_frequency": "once per main.py run"
  },
  {
    "system": "meta supervisor",
    "status": "ACTIVE / EXECUTION_ONLY with limited telemetry",
    "location": "runtime/meta/supervisor/meta_supervisor.py",
    "entry_points": ["supervise", "is_action_allowed", "apply_to_context"],
    "dependencies": ["program_memory", "strategy_memory", "execution_memory", "reuse_decision_engine"],
    "reports_generated": ["META_SUPERVISOR_REPORT", "COGNITIVE_REUSE_REPORT"],
    "execution_frequency": "per task, sometimes multiple times"
  },
  {
    "system": "adaptive reuse engine",
    "status": "ACTIVE / DEAD_RUNTIME_LAYER in sample",
    "location": "runtime/cognition/adaptive_reuse_engine.py",
    "entry_points": ["evaluate_reuse", "reuse_truth", "reuse_strategy", "reuse_context", "reuse_program"],
    "dependencies": ["runtime.cache.CacheManager"],
    "reports_generated": ["ADAPTIVE_REUSE_REPORT", "COGNITIVE_REUSE_REPORT"],
    "execution_frequency": "per task; returned no hits in sample"
  },
  {
    "system": "adaptive cache manager",
    "status": "PARTIALLY_CONNECTED / DEAD_RUNTIME_LAYER in sample",
    "location": "runtime/cache/cache_manager.py",
    "entry_points": ["get", "put", "report", "migrate_legacy_once"],
    "dependencies": ["truth/strategy/program/context/dependency/world/semantic/knowledge cache stores"],
    "reports_generated": ["adaptive_cache_layer", "cache metrics"],
    "execution_frequency": "constructed per pipeline; legacy migration skipped by default"
  },
  {
    "system": "process semantic context",
    "status": "PARTIALLY_CONNECTED",
    "location": "runtime/process and runtime/context",
    "entry_points": ["run_process_semantic_cycle", "ProcessSemanticEngine", "ProcessContextDiscovery"],
    "dependencies": ["process_dependency_chains", "tool selection", "meta supervisor"],
    "reports_generated": ["process_semantic_report", "process_semantic_models", "dependency_completeness_audit"],
    "execution_frequency": "conditional; skipped in fast sample because process_semantics tool was disabled"
  },
  {
    "system": "truth lifecycle",
    "status": "PARTIALLY_CONNECTED / REPORT EMPTY in sample",
    "location": "core/belief_engine.py, core/truth, runtime/truth, runtime/epistemic, runtime/governance",
    "entry_points": ["belief evaluation", "truth candidate engines", "truth commit engines", "truth_lifecycle_synchronizer"],
    "dependencies": ["contextual truth", "identity governance", "evidence", "dependency metrics"],
    "reports_generated": ["truth_candidate_report", "truth_commit_report", "truth_candidate_evaluations", "truth_commit_evaluations"],
    "execution_frequency": "conditional; no candidates/commits observed in sample"
  },
  {
    "system": "world governance",
    "status": "ACTIVE / REPORT_ONLY for normal ARC sample",
    "location": "runtime/world_governance",
    "entry_points": ["world_governance_kernel.build_report"],
    "dependencies": ["world governance submodules"],
    "reports_generated": ["WORLD_GOVERNANCE_REPORT", "world_governance_report"],
    "execution_frequency": "boot and report/finalization"
  },
  {
    "system": "evaluation and shutdown controllers",
    "status": "ACTIVE / UNSAFE_TO_DISABLE",
    "location": "runtime/evaluation, runtime/shutdown",
    "entry_points": ["EvaluationController.evaluate", "ShutdownController.execute_shutdown"],
    "dependencies": ["final results", "task outcome", "learning/reward state"],
    "reports_generated": ["evaluation_report", "SHUTDOWN_REPORT", "post_success_isolation"],
    "execution_frequency": "after completed main.py run"
  }
]
```

## Classification

### ACTIVE

- `main.py`
- `runtime/pipeline.py` shim
- `runtime/pipeline/legacy_pipeline.py`
- `runtime/stages/*` function stages
- `runtime/state/runtime_state.py`
- `runtime/kernel/runtime_kernel.py`
- `runtime/scheduler/runtime_scheduler.py`
- `runtime/learning/training_assistant.py`
- `runtime/learning/training_report.py`
- `runtime/evaluation/evaluation_controller.py`
- `runtime/shutdown/shutdown_controller.py`
- `runtime/meta/supervisor/meta_supervisor.py`
- task loading, grid analysis, object detection, pattern/rule, inference, transformation, evaluation stages

### PARTIALLY_CONNECTED

- `runtime/pipeline/pipeline_runner.py`: callable and tested, but not normal `main.py` path.
- `runtime/process/*` and `runtime/context/*`: available, but process semantics can be disabled by tool selection and meta supervisor.
- `runtime/cache/*`: active object graph, but legacy migration skipped by default; cache hits absent in sample.
- `runtime/cognition/adaptive_reuse_engine.py`: executed, but no reuse in sample.
- `runtime/governance/*`: imported and sometimes executed, but can be skipped by terminal success, meta directives, or budget gates.
- `core/concept_lifecycle/*`: feeds concept lifecycle report, but sample concepts remained `DISCOVERING`.
- `core/truth*`, `runtime/truth*`, `runtime/epistemic/*`: involved in truth surfaces, but final candidate/commit reports were empty in sample.

### REPORT_ONLY

- `runtime/diagnostics.py`
- `runtime/profiling/performance_reporter.py`
- `runtime/reporting/compact_report_builder.py`
- `runtime/learning/training_report.py` as an aggregator
- many `*_reporter.py` modules unless their report is explicitly read by a gate

### EXECUTION_ONLY

- stage functions that mutate `runtime_context` but do not always expose complete telemetry in minimal mode
- `meta_supervisor.is_action_allowed()` gates execution, but final minimal report only exposes partial reuse telemetry
- `early_exit_controller.evaluate()` affects shutdown path, while minimal final context may omit detailed gate trace

### LEGACY

- `runtime/pipeline/legacy_pipeline.py` is legacy by name but active and therefore cannot be disabled.
- `runtime/pipeline.py` exists as a compatibility shim while `runtime/pipeline/` exists as a package.
- `runtime/stage_registry.py` is a compatibility wrapper over `runtime/stages/registry.py`.
- `runtime/runtime_state.py` is a compatibility wrapper over `runtime/state/runtime_state.py`.
- `runtime/legacy/scheduler_legacy.py`.
- `runtime/synthesis/program_synthesis_engine.py` and `runtime/synthesis/adaptive_execution_engine.py` are older/broader surfaces compared with current stage execution.

### DUPLICATED

- Pipeline: `runtime/pipeline.py`, `runtime/pipeline/legacy_pipeline.py`, `runtime/pipeline/pipeline_runner.py`.
- Stage registries: `runtime/stage_registry.py`, `runtime/stages/registry.py`, `runtime/pipeline/stage_registry.py`.
- Runtime state: `runtime/runtime_state.py`, `runtime/state/runtime_state.py`.
- Kernel: `runtime/kernel/cognitive_kernel.py`, `runtime/cognitive_kernel/cognitive_kernel.py`, plus `core/cognitive_kernel`.
- Synthesis: `core/synthesis.py`, `runtime/engines/program_synthesis.py`, `runtime/synthesis/program_synthesis_engine.py`.
- Execution: `runtime/transforms/primitive_executor.py`, `runtime/execution/execution_engine.py`, `runtime/synthesis/adaptive_execution_engine.py`, `runtime/engines/transformation_engine.py`.
- Context: `core/context*`, `core/contextual_truth.py`, `core/context_hierarchy.py`, `core/semantic_context.py`, `runtime/context/*`, `runtime/process/*`.
- Truth: `core/truth/*`, `core/truth_commit_engine.py`, `runtime/truth/*`, `runtime/epistemic/truth_*`, `runtime/governance/truth_candidate_engine.py`, `runtime/truth_candidate_engine.py`.
- Cache/reuse: `runtime/cache/*`, `runtime/planning/cognitive_cache_manager.py`, `runtime/meta/supervisor/*_memory.py`, governance cache.
- Telemetry/performance: `runtime/profiling/*`, `runtime/reporting/*`, `runtime/diagnostics.py`, performance intelligence layer.

### ORPHANED / UNREACHABLE

The audit did not prove all of these are globally unreachable, but they are not part of the sampled `main.py -> legacy_pipeline` execution path:

- Modular pipeline stage classes under `runtime/pipeline/*_stage.py` for default CLI execution.
- Many `core/*` experimental governance, economics, ecology, pharmacy, civilization, and reflective-governance modules are imported by package facades or assigned in the legacy pipeline but require explicit call-site proof before treating them as decision-active.
- `runtime/object_motion/tests` lacks a package initializer per audit tool output.
- `data/curriculum` lacks a package initializer per audit tool output.
- `runtime/diagnostics` directory lacks a package initializer while `runtime/diagnostics.py` exists, creating a future collision risk.

### SAFE_TO_DISABLE Candidates

Safe only after tests confirm no direct call sites:

- Modular pipeline runner for normal CLI path, if preserving only `main.py` behavior.
- Compatibility wrappers once all imports are migrated.
- Report-only diagnostics flags in production execution.
- Optional profiling/reporting layers when not requested.
- Legacy synthesis/execution modules not called by active stages.

### UNSAFE_TO_DISABLE

- `main.py`
- `runtime/pipeline.py` shim while `main.py` imports `pipeline`
- `runtime/pipeline/legacy_pipeline.py`
- `runtime/stages/*`
- `runtime/state/runtime_state.py`
- `runtime/learning/training_assistant.py`
- `runtime/learning/training_report.py`
- `runtime/evaluation/evaluation_controller.py`
- `runtime/shutdown/shutdown_controller.py`

## Dead Runtime Layers

### Context Layer

Flag: `DEAD_RUNTIME_LAYER` for fast sample.

Evidence:

- final `context_count = 0`
- diagnostics printed `No context data available`
- tool selection disabled `process_semantics`
- `run_process_semantic_cycle()` writes an empty `process_semantic_models` dict when disabled by tool selection
- training report can aggregate context reports, but no populated context reports survived into final diagnostics

Breakpoint:

```text
tool selection disables process_semantics
run_process_semantic_cycle short-circuits
training_report receives no process context reports
normalize_context_diagnostics merges empty context maps
RuntimeDiagnostics.contexts prints no context data
```

### Truth Candidate / Commit Layer

Flag: `DEAD_RUNTIME_LAYER` for fast sample.

Evidence:

- `Stable Truths = 0`
- `Truth Candidates = 0`
- `Truth Commit Entries = 0`
- `main.py` has a hard `discovery_only_truth_mode = True` block that clears collected `truth_candidate_report` and `truth_commit_report`
- concepts remained `DISCOVERING`

Breakpoint:

```text
concepts discovered
candidate/commit reports either not generated or not promoted
main.py clears collected truth candidate/commit reports
diagnostics receive empty truth report surfaces
```

### Cache / Reuse Layer

Flag: `DEAD_RUNTIME_LAYER` for fast sample.

Evidence:

- `cache_hits = 0`
- `cache_misses = 2`
- `reuse_rate = 0.0`
- legacy `concept_cache.json` detected but not loaded during boot
- metadata: `cache_boot_loaded = False`, `cache_boot_skipped = True`, `legacy_cache_detected = True`, `legacy_cache_migration_skipped = True`

Breakpoint:

```text
legacy cache exists
adaptive CacheManager constructed with auto_migrate=False
legacy migration skipped
AdaptiveReuseEngine evaluates but finds no reusable assets
performance_report records zero hits
```

### Dependency Reasoning Layer

Flag: `DEAD_RUNTIME_LAYER` for fast sample.

Evidence:

- `dependency_chains_executed = 0`
- `dependency_chain_depth = 0`
- `dependency_chain_coverage = 0.0`
- architecture bottleneck report saw dependency samples but no executed chain depth in final performance report

## Report Flow Audit

| Report | Generated | Consumed | Status |
| --- | --- | --- | --- |
| `CONTEXT DISCOVERY REPORT` / `context_discovery_reports` | training report can collect from cognition and process-context reports | diagnostics via `normalize_context_diagnostics` | empty in sample |
| `CONTEXT HIERARCHY REPORT` / `context_hierarchy_reports` | training report can derive from governance registry or cognition reports | diagnostics via normalized contexts | empty in sample |
| `SEMANTIC CONTEXT REPORT` / `semantic_context_reports` | training report can derive from process semantic reports | diagnostics via normalized contexts | empty in sample |
| `CONTEXTUAL TRUTH REPORT` / `contextual_truth_reports` | training report and causal/truth systems can emit | diagnostics and main report bridge | empty in sample |
| `TRUTH CANDIDATE REPORT` | collected by `main.py` from task results | explicitly cleared by `discovery_only_truth_mode` | ignored/overwritten |
| `TRUTH COMMIT REPORT` | collected by `main.py` from task results | explicitly cleared by `discovery_only_truth_mode` | ignored/overwritten |
| `CACHE REPORT` | cache manager and cognitive cache manager generate metrics | performance report and performance intelligence | generated but hit counts zero in sample |
| `REUSE REPORT` | meta supervisor and adaptive reuse engine generate | performance intelligence, context fields | generated but reuse rate zero in sample |
| `PERFORMANCE REPORT` | pipeline and main aggregate | final output, performance intelligence, runtime metadata | active |
| `PERFORMANCE INTELLIGENCE REPORT` | performance reporter | final output | report-only |
| `RUNTIME METADATA` | `main.py` | final output | active/report-only |

## Context Architecture Audit

### Process Context

- Created by `runtime/process/process_context_discovery.py` and related process semantic engines.
- Registered through process semantic reports and context governance registry when the cycle runs.
- Consumed by training report aggregation and possibly dependency/semantic reasoning.
- Disappears when `process_semantics` is disabled by tool selection.

### Semantic Context

- Created by `core/semantic_context.py`, `runtime/context/semantic_context_graph.py`, and process semantic engines.
- Consumed by contextual truth, dependency knowledge, and causal validation surfaces.
- In sample, semantic abstractions print in inference, but semantic context reports do not survive to final context diagnostics.

### Dependency Context

- Created by dependency chain execution and process dependency memory.
- Consumed by training report architecture bottleneck logic and truth promotion dependency gates.
- In sample, final dependency chain depth/coverage remained zero.

### Causal Context

- Created by causal validation and causal alignment modules.
- Consumed by truth/contextual truth and dependency reports.
- Active in inference as support scores, but not promoted into truth lifecycle output in sample.

### World Context

- Created by world governance boot report and transformation world model report.
- Consumed by performance/world governance reports.
- Active as reporting and transformation evaluation; not shown to influence truth/context promotion in sample.

## Truth Architecture Audit

Observed stages:

- `DISCOVERING`: active. Sample had 18 concepts, all discovering.
- `SUPPORTED`: not observed in final sample output.
- `VALIDATED`: not observed in final sample output.
- `TRUTH_CANDIDATE`: not observed in final sample output.
- `TRUTH_COMMITTED`: not observed in final sample output.
- `LOCKED_TRUTH_PRESERVED`: appears in code and cache snapshots, not observed as final stable truth in sample.

Promotion gates exist for:

- `candidate_ready`
- `promotion_score`
- `eligible_for_truth_candidate`
- `stage_eligible_for_truth_candidate`
- contradiction review
- contextual truth support
- identity governance
- dependency confidence/depth/coverage

Observed failure mode: values remain absent or false because concepts do not leave `DISCOVERING`, process/context reports are empty, dependency metrics are zero, and final truth report surfaces are cleared or empty.

## Cache & Reuse Audit

Cache systems present:

- `runtime/cache/cache_manager.py`
- `truth_cache.py`
- `strategy_cache.py`
- `context_cache.py`
- `program_cache.py`
- `world_model_cache.py`
- `semantic_cache.py`
- `knowledge_cache.py`
- `dependency_snapshot_cache.py`
- `runtime/planning/cognitive_cache_manager.py`
- meta supervisor program/strategy/execution memory
- governance cache

Why hits remain zero in sample:

- legacy cache detected but not loaded
- migration skipped by default
- adaptive reuse eligibility or lookup produced no compatible validated assets
- fast run did not generate reusable validated contexts/truths
- process semantic and deeper reasoning paths were bypassed

## Meta Layer Audit

Active execution influence:

- `MetaSupervisor.is_action_allowed()` gates reasoning, program synthesis, context discovery, governance, self improvement.
- `run_meta_supervisor_cycle()` updates context with directives.
- `early_exit_controller` can change health/finalization path.
- `cognitive_budget_controller` and tool selection influence enabled tools.

Report-only or weak influence:

- performance intelligence optimizes recommendations, not the current run.
- diagnostics read final reports only.
- meta reuse report shows counters but does not guarantee cache reuse.

## Governance Audit

Active:

- identity/truth/contradiction/causal checks are kept in the fast-mode safety floor.
- governance cycle can execute if meta supervisor and meta decision allow it.
- shutdown/evaluation governance is active after successful main runs.

Bypassed/conditional:

- deep governance revalidation can be skipped by meta supervisor, post-success fast shutdown, or meta decision.
- truth candidate/commit reports are cleared from final main output by `discovery_only_truth_mode`.
- context governance cannot receive useful input when process/context discovery is disabled or empty.

## Broken Pipeline Connections

1. `runtime/pipeline.py` and `runtime/pipeline/` coexist, creating a module/package collision. The audit tool flags this.
2. Canonical modular pipeline exists but normal execution still uses `legacy_pipeline`.
3. Process semantic reports are designed for aggregation but can be disabled before they create context inputs.
4. Main report collection gathers truth candidate/commit reports, then clears them with `discovery_only_truth_mode = True`.
5. Legacy cache is detected but not loaded/migrated by default, so cache/reuse systems start from empty adaptive stores.
6. Inference prints semantic abstractions, but context diagnostics see no context data.
7. Performance report can report zero active compute/dependency/governance time despite visible stage execution, indicating timing bridge gaps.
8. Report names vary by case and spacing, increasing collector fragility.
9. Many governance layers are imported eagerly but lack clear final evidence of decision impact.
10. Modular pipeline and legacy stage sequence have separate stage abstractions.

## Architecture Risks

- Active behavior depends on a 280k-line legacy pipeline file.
- “Legacy” cannot mean removable because the legacy pipeline is the active production path.
- Report aggregation can create false confidence: empty reports look like valid reports.
- Truth and context layers have many implementations but weak observed promotion into final runtime diagnostics.
- Cache and reuse surfaces are duplicated and disconnected from legacy cache by default.
- Module/package name collision around `runtime.pipeline` risks import ambiguity.
- Minimal report mode hides details needed to diagnose skipped cycles.
- Many systems are import-active but not execution-proven.

## Top 10 Bottlenecks

1. `runtime/pipeline/legacy_pipeline.py` owns too many responsibilities.
2. Stage cycle dominates sampled runtime.
3. Context discovery is gated off in fast mode, leaving context reports empty.
4. Truth reports are collected then cleared.
5. Cache migration is skipped despite legacy cache detection.
6. Duplicate pipeline systems create uncertainty about canonical behavior.
7. Duplicate truth/context/cache implementations obscure ownership.
8. Performance timing has unattributed runtime and empty module timings in final report.
9. Governance layers are numerous and conditionally bypassed.
10. Diagnostics are post hoc and cannot detect why upstream reports were empty unless skip reports survive compaction.

## Top 10 Refactor Opportunities

1. Decide whether `legacy_pipeline` or `ModularPipelineRunner` is canonical, then make the other a wrapper.
2. Split `legacy_pipeline` into explicit boot, stage, reasoning, context, governance, cache, finalization, and report modules.
3. Remove or rename the `runtime/pipeline.py` vs `runtime/pipeline/` collision.
4. Replace `discovery_only_truth_mode = True` with an explicit CLI/config option and report the suppression reason.
5. Make empty reports carry a `reason` and `upstream_stage` field.
6. Add a runtime execution graph report emitted before compaction.
7. Make context discovery produce at least a disabled/skipped report consumed by diagnostics.
8. Unify cache metrics across adaptive cache, cognitive cache, and meta supervisor memory.
9. Consolidate truth candidate/commit engines behind a single facade.
10. Add tests that run `main.py` and assert non-empty/explicitly-skipped context, truth, cache, and governance report paths.

## Migration Plan

1. Freeze behavior with a golden runtime sample.
   - Store expected stage order, skip reasons, and final counters.
   - Include context/truth/cache/reuse reports even when empty.

2. Establish canonical pipeline ownership.
   - Either migrate `main.py` to `run_modular_pipeline(use_legacy=False)` or rename `legacy_pipeline` to `active_pipeline`.
   - Keep wrappers only after call sites are migrated.

3. Normalize report contracts.
   - Every report must include `system`, `status`, `generated`, `consumed_by`, `affects_execution`, and `empty_reason`.
   - Stop silently replacing reports with `{}`.

4. Reconnect context.
   - Ensure process context, semantic context, dependency context, causal context, and world context each have create/register/consume telemetry.
   - Diagnostics should show skipped reasons, not only missing data.

5. Reconnect truth.
   - Remove hard-coded final truth report suppression or make it visible.
   - Track `candidate_ready`, `promotion_score`, `eligible_for_truth_candidate`, and `stage_eligible_for_truth_candidate` in final diagnostics.

6. Reconnect cache/reuse.
   - Decide whether legacy cache migration should run by default, lazily, or never.
   - Unify cache hit metrics so adaptive cache, cognitive cache, and meta memory agree.

7. Consolidate duplicates.
   - Pipeline first, then truth, context, cache, governance, telemetry.
   - Keep compatibility wrappers with warnings and deprecation dates.

8. Only then remove code.
   - Disable one subsystem at a time behind config flags.
   - Compare golden runtime reports before deleting any implementation.

