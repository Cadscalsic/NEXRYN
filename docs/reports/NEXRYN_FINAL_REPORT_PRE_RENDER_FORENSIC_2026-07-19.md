# NEXRYN Final Report Pre-Render Hang Forensic Report

## 1. Exact Last Successful Runtime Marker

Observed last task boundary:

- `EVALUATION METRICS: {...}`
- Diagnostic boundary: `LAST_TASK_EVALUATION_COMPLETE_SNAPSHOT`
- Run: `python main.py --tasks_dir data/training --mode fast --report-level minimal --training-batch-size 3 --post-success-mode fast --reset-training-assistant`
- Artifact: `runtime/artifacts/pre_final_report_diagnostics.json`

## 2. Exact First Missing Runtime Marker

The first report marker is constructed by `runtime/reporting/final_report_renderer.py` as `REPORT_BEGIN_MARKER = "<<< NEXRYN_REPORT_BEGIN >>>"`.

It is not printed until `DeterministicFinalReportRenderer.emit()` receives a fully rendered string. The marker is therefore missing while `render()` is still computing.

## 3. Complete Call Path Between Boundaries

Fast/minimal path:

1. `main.py:1699` enters `minimal_terminal_closure`.
2. `main.py:1701` calls `TrainingAssistant.complete_cycle`.
3. `main.py:1711` calls `build_training_report`.
4. `main.py:1783` calls `final_report_renderer.render`.
5. `final_report_renderer.py:95` applies `_minimal_report_projection`.
6. `final_report_renderer.py:107` calls `canonical_report_binding_engine.bind`.
7. `canonical_report_binding_engine.py:181` calls `discover_sources`.
8. `canonical_report_binding_engine.py:342-368` unconditionally builds cognitive domain report sources.
9. `final_report_renderer.py:132` calls `compact_report_compression_engine.compress`.
10. `compact_report_compression_engine.py:158` compresses the bound state.
11. `compact_report_compression_engine.py:763` serializes state for `_actual_size`.
12. `final_report_renderer.py:146` builds canonical render state.
13. `final_report_renderer.py:153` calls `_render_full_report`.
14. `final_report_renderer.py:185` emits the finished string.

## 4. Confirmed Blocking File And Function

Primary pre-first-byte compute site:

- `runtime/reporting/canonical_report_binding_engine.py:257`
- `CanonicalReportBindingEngine.discover_sources`

Hottest nested functions:

- `canonical_report_binding_engine.py:1351` `_build_cognitive_domain_lifecycle_visibility`
- `canonical_report_binding_engine.py:1310` `_build_cognitive_domain_intelligence_visibility`
- `canonical_report_binding_engine.py:1429` `_build_cognitive_domain_governance_visibility`
- `canonical_report_binding_engine.py:1474` `_build_cognitive_domain_ecosystem_visibility`
- `canonical_report_binding_engine.py:1529` `_build_cognitive_domain_constitution_visibility`

## 5. Confirmed Blocking Line

The observability defect starts at `main.py:1783`: `render()` is called before any `<<< NEXRYN_REPORT_BEGIN >>>` byte is emitted.

Inside that call, the confirmed expensive line family is `canonical_report_binding_engine.py:342-368`, where `discover_sources()` constructs all cognitive domain canonical sources before the marker can print.

## 6. Wall Time In Pre-Render Interval

3-task fast/minimal run:

- `LAST_TASK_EVALUATION_COMPLETE` to `FINAL_REPORT_FIRST_BYTE_WRITTEN`: `1.891325s`
- `TRAINING_BATCH_FINALIZATION`: `0.003086s`
- `TRAINING_REPORT_GENERATION`: `0.012740s`
- `REPORT_PROJECTION`: `0.000347s`
- `CANONICAL_BIND`: `1.326911s`
- `REPORT_SOURCE_COLLECTION` inside bind: `1.223809s`
- `REPORT_COMPRESSION`: `0.254832s`
- `REPORT_FULL_STRING_CONSTRUCTED`: at `1.878278s`
- first to last byte: `0.000187s`

## 7. Top Slow Functions

Top cumulative:

- `final_report_renderer.py:73 render`: `1.645639s`
- `canonical_report_binding_engine.py:169 bind`: `1.325841s`
- `canonical_report_binding_engine.py:257 discover_sources`: `1.223509s`
- `canonical_report_binding_engine.py:1351 _build_cognitive_domain_lifecycle_visibility`: `0.776723s`, 16 calls
- `dataclasses.py:1254 asdict`: `0.645379s`, 1089 calls
- `canonical_report_binding_engine.py:1310 _build_cognitive_domain_intelligence_visibility`: `0.596966s`, 17 calls
- `canonical_report_binding_engine.py:1429 _build_cognitive_domain_governance_visibility`: `0.590646s`, 4 calls
- `canonical_report_binding_engine.py:1529 _build_cognitive_domain_constitution_visibility`: `0.570564s`
- `canonical_report_binding_engine.py:1474 _build_cognitive_domain_ecosystem_visibility`: `0.556255s`
- `copy.py:128 deepcopy`: `0.304817s`, 28,395 calls
- `compact_report_compression_engine.py:143 compress`: `0.255003s`

Top self:

- `dataclasses.py:1278 _asdict_inner`: `0.307806s`
- diagnostic `_shape.visit`: `0.240809s` from the temporary profiler
- `copy.py:128 deepcopy`: `0.183451s`
- `json/encoder.py:205 iterencode`: `0.071212s`
- `cognitive_knowledge_domains.py:2346 _dedupe`: `0.055617s`

## 8. Stack-Dump Evidence

No 10-second stack dump fired in the 1-task or 3-task repro because first byte arrived before 10 seconds. The process was computing on `MainThread`, not deadlocked or waiting.

## 9. Collection Sizes

3-task run:

- boundary snapshot: 692 sampled nodes, largest dict 38, largest list 9
- report source snapshot before renderer: 7,461 sampled nodes, largest list 382
- canonical discover input: 127 sampled nodes
- compression input: 3,174 sampled nodes, largest dict 101
- canonical render state: 3,230 sampled nodes, largest dict 101
- compressed state: 36 sampled nodes

## 10. Report Size Estimate

- full rendered report: 4,400 chars / 4,400 UTF-8 bytes
- compressed canonical JSON size before compression: 135,284 chars
- compressed canonical JSON size after compression: 766 chars
- renderer console budget: 34,000 chars
- compression budgets: minimal 8,000, normal 20,000, diagnostic summary 50,000, full diagnostic unbounded

No enforced max report nodes, max concepts, max relationships, max history entries, or render duration is applied by `final_report_renderer.render()` before binding.

## 11. History Aggregation Findings

`TrainingAssistant.complete_cycle` at `runtime/learning/training_assistant.py:632-643` retains only the last 31 prior batch history entries plus current cycle. In the profiled interval it took `0.003086s`, so it is not the blocking function.

The `history_size = 3` growth is real training assistant state, but this path does not traverse all task history during the observed delay.

## 12. Context Explosion Findings

`task_spatial_signal` is not present as a symbol in this checkout. The profiled pre-render path did not spend time in context string flatteners.

There are unrelated evidence string builders, for example `runtime/concepts/concept_formation_engine.py:727`, but they were not active in the pre-render profile.

## 13. Projection Findings

Minimal projection is applied first in `final_report_renderer.py:95`.

However, canonical binding then rebuilds non-minimal canonical sources anyway. The system therefore behaves as:

- selects minimal report state first
- then reconstructs full cognitive domain source families inside binding
- then hides many bound fields by policy

This is the core projection bug.

## 14. Training Finalization Findings

Training finalization is not the cause in the repro:

- `TrainingAssistant.complete_cycle`: `0.003086s`
- `build_training_report`: `0.012740s`
- report keys: 44
- task results: 3

It persists training assistant state via JSON, but the profile shows this is negligible compared to canonical binding.

## 15. Governor Bypass Findings

The profiled final-report path is bypassing the Adaptive Execution Governor.

`runtime/resource_governance/reporting_governor.py` defines projection contracts and report-size budgets, but `main.py:1783`, `final_report_renderer.py:107`, and `canonical_report_binding_engine.py:181` call renderer and binding directly. No `AdaptiveExecutionGovernor.select_report_projection`, serialization governor, or post-processing budget enforcement appears in the call path.

Classification:

- training finalization: `BYPASSING_GOVERNOR`
- training report generation: `BYPASSING_GOVERNOR`
- final renderer: `BYPASSING_GOVERNOR`
- canonical binding: `BYPASSING_GOVERNOR`
- compression serialization: `BYPASSING_GOVERNOR`
- stdout emit: `BYPASSING_GOVERNOR`

## 16. Lock Or Wait Findings

No `Lock`, `RLock`, `Event.wait`, `Queue.get`, `Future.result`, `join`, executor shutdown, subprocess wait, or file-lock wait appears in the profiled call stack.

The process is computing, not waiting or deadlocked.

## 17. Root Cause

After the last task, `main.py:1783` calls `DeterministicFinalReportRenderer.render()` before printing `<<< NEXRYN_REPORT_BEGIN >>>`. In minimal mode, `render()` projects the report, but then `CanonicalReportBindingEngine.discover_sources()` reconstructs full cognitive domain canonical sources at `canonical_report_binding_engine.py:342-368`. Those fallbacks recursively rebuild domain knowledge, intelligence, lifecycle, interaction, governance, ecosystem, and constitution reports, causing repeated `dataclasses.asdict` and `deepcopy` work before the first report byte can reach stdout.

## 18. Secondary Causes

- `CanonicalReportBindingEngine._merge_dicts` deep-copied 627 dicts.
- `deepcopy` ran 28,395 calls.
- compression serialized the bound report to JSON before rendering: 135,284 chars.
- report renderer builds the full report string in memory before emitting.
- observability marker is printed only after expensive binding and compression unless temporary diagnostics are enabled.

## 19. Recommended Repair Plan

1. `FIX_REPORT_PROJECTION`: make canonical source discovery projection-aware; in minimal mode do not build cognitive domain/fabric/lifecycle fallback sources unless a visible minimal field requires them.
2. `OPTIMIZE_CANONICAL_BINDING`: memoize internal fallback visibility builders within a single `bind()` call; `_build_cognitive_domain_lifecycle_visibility` was called 16 times and intelligence 17 times.
3. `STREAM_RENDERING`: emit `<<< NEXRYN_REPORT_BEGIN >>>` before binding/compression, or split rendering into first-byte header emission plus deferred sections.
4. `GOVERNOR_GATING_FIX`: route final renderer, canonical binding, compression, and serialization through `ReportingGovernor` and `SerializationGovernor`.
5. `BOUND_REPORT_DATA`: add explicit max nodes, max list length, max relationship count, max history entries, and max render duration before binding.
6. `REMOVE_DUPLICATE_CONTEXT`: avoid binding full diagnostics into hidden/minimal fields; hidden fields should carry metadata, not deep-copied values.
7. `LIMIT_HISTORY_SCOPE`: keep the current 31-cycle training cap and ensure canonical report context only receives the current execution summary in minimal mode.

## 20. Default Adaptive/Normal Reproduction Addendum

After the fast/minimal run completed successfully, the same diagnostic markers were exercised on the default CLI path:

- Command: `python main.py`
- Artifact: `runtime/artifacts/pre_final_report_run_default.log`
- Result: process exited with Windows access violation `-1073741819`
- The process printed `<<< FINAL_REPORT_PIPELINE_ENTER >>>`
- The process printed `<<< FINAL_REPORT_RENDERER_ENTER >>>`
- The process did not print `FINAL_REPORT_FIRST_BYTE_WRITTEN`
- The process did not print `<<< NEXRYN_REPORT_BEGIN >>>`
- The process did not print `REPORT_SOURCE_COLLECTION_EXIT`
- The process did not print `CANONICAL_BIND_EXIT`

This proves the default path blocks after renderer entry and before the first report byte.

## 21. Corrected Missing Marker For Default Path

Exact last successful runtime markers:

- final task `EVALUATION METRICS`
- `PRE_FINALIZATION_ENTER`
- `LAST_TASK_EVALUATION_COMPLETE_SNAPSHOT`
- `<<< FINAL_REPORT_PIPELINE_ENTER >>>`
- `REPORT_SOURCE_COLLECTION_SNAPSHOT`
- `<<< FINAL_REPORT_RENDERER_ENTER >>>`
- `COGNITIVE_REPORT_BUILD_ENTER`
- `CANONICAL_BIND_ENTER`
- `REPORT_SOURCE_COLLECTION_ENTER`
- `CANONICAL_DISCOVER_INPUT_SNAPSHOT`

Exact first missing marker:

- `REPORT_SOURCE_COLLECTION_EXIT`

First missing final-report byte marker:

- `FINAL_REPORT_FIRST_BYTE_WRITTEN`
- `<<< NEXRYN_REPORT_BEGIN >>>`

## 22. Default Path Confirmed Blocking Call Path

Default path call stack at repeated samples:

1. `main.py:4934` calls `final_report_renderer.render`.
2. `runtime/reporting/final_report_renderer.py:111` calls `canonical_report_binding_engine.bind`.
3. `runtime/reporting/canonical_report_binding_engine.py:187` calls `discover_sources`.
4. `runtime/reporting/canonical_report_binding_engine.py:354` constructs `unified_concept_lifecycle_report`.
5. `runtime/reporting/canonical_report_binding_engine.py:1109` calls `unified_concept_lifecycle_builder.build(report_state, performance)`.
6. `core/concept_lifecycle/unified_concept_lifecycle.py:115` calls `_collect_concepts(context)`.
7. `core/concept_lifecycle/unified_concept_lifecycle.py:116` builds lifecycle rows for every collected concept.
8. `core/concept_lifecycle/unified_concept_lifecycle.py:138` calls `_discovery_source(concept, context)`.
9. `core/concept_lifecycle/unified_concept_lifecycle.py:262` calls `_collect_concepts(value)` again for each discovery source candidate.
10. `core/concept_lifecycle/unified_concept_lifecycle.py:241-248` recursively visits nested mappings/lists.
11. `core/concept_lifecycle/unified_concept_lifecycle.py:270-287` recursively visits truth-state structures.

The confirmed report-path blocker is `CanonicalReportBindingEngine.discover_sources`, specifically the unconditional source creation at `canonical_report_binding_engine.py:354`, which invokes `_build_unified_concept_lifecycle_visibility`.

The confirmed active compute site is `core/concept_lifecycle/unified_concept_lifecycle.py:241-248`, the recursive `visit()` inside `_collect_concepts`.

## 23. Default Path Stack-Dump Evidence

`faulthandler.dump_traceback_later(10, repeat=True)` captured 23 timeout stack dumps before the process crashed. Repeated locations:

- `core/concept_lifecycle/unified_concept_lifecycle.py:242 in visit`: 72 samples
- `core/concept_lifecycle/unified_concept_lifecycle.py:246 in visit`: 21 samples
- `runtime/reporting/canonical_report_binding_engine.py:1109 in _build_unified_concept_lifecycle_visibility`: 15 samples
- `runtime/reporting/canonical_report_binding_engine.py:354 in discover_sources`: 15 samples
- `core/concept_lifecycle/unified_concept_lifecycle.py:248 in _collect_concepts`: 11 samples
- `core/concept_lifecycle/unified_concept_lifecycle.py:241 in visit`: 9 samples

Classification:

- computing, not waiting
- not deadlocked
- progress is partial but pathological: repeated deep copies and recursive traversals continue while memory rises
- final stdout is blocked because `emit()` has not been called

## 24. Default Path Collection And Memory Evidence

Boundary snapshot after final task:

- `total_nodes`: 65,578
- `total_dicts`: 4,391
- `total_lists`: 1,342
- `largest_list`: 1,290
- `largest_dict`: 175
- `estimated_scalar_chars`: 870,158

Renderer source snapshot before binding:

- `total_nodes`: 34,492
- `total_dicts`: 1,788
- `total_lists`: 793
- `largest_list`: 500
- `largest_dict`: 177
- `estimated_scalar_chars`: 467,214

Canonical discovery input:

- `total_nodes`: 108,656
- `total_dicts`: 8,918
- `total_lists`: 4,881
- `largest_list`: 1,290
- `largest_dict`: 177
- `estimated_scalar_chars`: 1,466,154

Memory progression during `REPORT_SOURCE_COLLECTION`:

- 4.927656s: current 5,885,594 bytes, peak 7,349,180 bytes
- 21.412492s: current 30,520,987 bytes, peak 40,716,141 bytes
- 39.387997s: current 56,847,747 bytes, peak 67,044,427 bytes
- 56.176709s: current 82,094,238 bytes, peak 92,291,054 bytes
- 74.321025s: current 108,119,047 bytes, peak 118,315,727 bytes

The process later terminated with `Windows fatal exception: access violation` while still inside the same pre-render binding/lifecycle stack.

## 25. Projection And CLI Findings After Default Run

The requested command `python main.py --policy balanced` is not supported by the current CLI:

```text
main.py: error: unrecognized arguments: --policy balanced
```

The codebase has an internal balanced policy alias in `runtime/resource_governance/execution_contract.py`, and legacy mode `adaptive` maps to `BALANCED`, but `main.py` only exposes:

```text
--mode {fast,adaptive,deep,full}
--report-level {minimal,normal,full,debug,audit}
```

Therefore the next runnable policy-equivalent diagnostic is `python main.py --mode adaptive`, not `python main.py --policy balanced`, unless the CLI is extended.

## 26. Updated Root Cause

Fast/minimal is healthy because projection shrinks the source enough for binding to complete.

Default/adaptive normal reporting is not healthy. After the final task, `main.py:4934` calls `DeterministicFinalReportRenderer.render()` before the first report byte is emitted. During `render()`, `CanonicalReportBindingEngine.bind()` enters `discover_sources()`. `discover_sources()` unconditionally builds `unified_concept_lifecycle_report` at `canonical_report_binding_engine.py:354`. That calls `unified_concept_lifecycle_builder.build()` at `canonical_report_binding_engine.py:1109`, which recursively scans the combined `report_state + performance` context in `core/concept_lifecycle/unified_concept_lifecycle.py:241-248` and re-scans concept discovery sources per concept at line 262.

The exact line preventing the first report byte is therefore the pre-render call to build unified concept lifecycle visibility from canonical source discovery:

```text
runtime/reporting/canonical_report_binding_engine.py:354
```

The exact active repeated compute loop is:

```text
core/concept_lifecycle/unified_concept_lifecycle.py:241-248
```

The marker has not printed because `<<< NEXRYN_REPORT_BEGIN >>>` is only written by `final_report_renderer.emit()`, and `emit()` is called after `render()` returns. In the failing default path, `render()` never returns.

## 27. Updated Repair Plan

1. `FIX_REPORT_PROJECTION`: make `discover_sources()` projection-aware and skip `unified_concept_lifecycle_report` unless the selected report policy needs it.
2. `BOUND_REPORT_DATA`: impose report-source budgets before `unified_concept_lifecycle_builder.build()`, especially max nodes, max list length, max concepts, and max lifecycle rows.
3. `OPTIMIZE_CANONICAL_BINDING`: memoize `_collect_concepts(context)` and avoid calling it again inside `_discovery_source()` once per concept and once per source key.
4. `STREAM_RENDERING`: print `<<< NEXRYN_REPORT_BEGIN >>>` before expensive binding, or split report rendering into a flushed header plus deferred sections.
5. `GOVERNOR_GATING_FIX`: route final report source construction through the reporting governor/post-processing budget; current default path is still effectively bypassing budget enforcement.
6. `LIMIT_HISTORY_SCOPE`: pass only current-execution lifecycle inputs into final report binding unless a full/debug/audit policy explicitly requests historical lifecycle reconstruction.
7. `REMOVE_DUPLICATE_CONTEXT`: prevent full `report_state` and `performance_report` copies from being merged into lifecycle builders when only a small set of concept fields is needed.

## 28. Fix Verification Addendum

Implemented repairs:

- `FIX_REPORT_PROJECTION`: canonical source collection is now report-level aware. Expensive derived lifecycle/domain/program sources are skipped for large non-diagnostic report states unless explicitly present.
- `BOUND_REPORT_DATA`: unified concept lifecycle collection, truth-state traversal, canonical binding copies, and JSON normalization now have bounded depth/node/list budgets and recursive-reference protection.
- `OPTIMIZE_CANONICAL_BINDING`: lifecycle visibility is cached per bind call, program generation reuses the cached lifecycle, and large normal/adaptive source discovery no longer performs a full recursive named-source scan.
- `STREAM_RENDERING`: first-byte markers are flushed directly around final report pipeline, renderer entry, first byte, and last byte.
- `REMOVE_DUPLICATE_CONTEXT`: canonical binding uses bounded visible report-state projections rather than copying full runtime state into every canonical source.

Final verification command:

```text
NEXRYN_FINAL_REPORT_DIAG=1 python main.py
```

Final result:

- Process exit code: `0`
- `<<< FINAL_REPORT_PIPELINE_ENTER >>>`: printed
- `<<< FINAL_REPORT_RENDERER_ENTER >>>`: printed
- `<<< NEXRYN_REPORT_BEGIN >>>`: printed
- `<<< NEXRYN_REPORT_END >>>`: printed
- `Binding Validation Status`: `VALID`
- Renderer validation errors: `0`
- Final report characters/bytes: `19,267`

Final measured pre-render timeline:

- `PRE_FINALIZATION_ENTER`: 0.004050s
- `REPORT_SOURCE_COLLECTION_EXIT`: 16.321689s, 23 sources, 1,128 source keys
- `CANONICAL_BIND_EXIT`: 16.588630s, 101 fields
- `REPORT_RENDER_PREP_EXIT`: 19.482790s, 19,267 rendered chars
- `FINAL_REPORT_FIRST_BYTE_WRITTEN`: 19.499885s
- `FINAL_REPORT_LAST_BYTE_WRITTEN`: 19.500727s

Final profile after repair:

- `final_report_renderer.render`: 17.668s cumulative
- `CanonicalReportBindingEngine.bind`: 14.732s cumulative
- `discover_sources`: 14.491s cumulative
- `_diag_deepcopy` / `_bounded_copy`: 10.749s / 10.663s cumulative under diagnostics
- diagnostic `collection_snapshot`: 8.325s cumulative

The previous confirmed blocker, unconditional lifecycle/domain source construction plus full recursive named-source discovery before the first report byte, no longer prevents report output. Remaining pre-render cost in diagnostic mode is mostly bounded copy/shape instrumentation and is finite with visible progress.
