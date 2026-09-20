# NEXRYN Performance Diagnosis - 2026-07-17

## 1. Confirmed primary bottleneck

Single-task fast/minimal execution does not hang in task solving. It spends most visible time after task execution, in reporting/finalization and post-execution cognitive memory construction.

Measured command profile:

`main.py --mode fast --report-level minimal --training-batch-size 1 --selection-mode random --random-seed 1 --disable-telemetry --cache-dependencies --post-success-mode fast`

Evidence artifacts:

- `runtime/artifacts/diagnostics/nexryn_profile_summary_fast_single_120s.json`
- `runtime/artifacts/diagnostics/nexryn_profile_summary_fast_single_180s.json`
- `runtime/artifacts/diagnostics/nexryn_stack_samples_fast_single_180s.txt`

The first normal diagnostic run exceeded 300 seconds and was externally killed. A self-dumping 120s run was still inside post-execution cognitive memory. A self-dumping 180s run reached final report rendering but was still not complete at cutoff.

Top-level 180s attribution:

| Stage/function | Measured duration | Runtime share | Evidence |
|---|---:|---:|---|
| `main.py:<module>` | 180.339s | 99.4% | cProfile |
| `pipeline.run` task execution path | 56.518s | 31.2% | `runtime/pipeline/legacy_pipeline.py:13061` |
| `cognitive_runtime_execution_engine.build_report` | 92.281s | 50.9% | `runtime/cognitive_runtime/execution_engine.py:825` |
| remaining main finalization/rendering after cognitive report | at least 31.5s | at least 17.4% | derived from 180.339 - 56.518 - 92.281 |

This accounts for approximately 99.5% of observed runtime in the 180s cutoff run.

## 2. Exact file and function

Primary hot function:

- `runtime/knowledge/knowledge_fabric_engine.py:143` `KnowledgeFabricRegistry.add_relationship`
- Inner hot line: `runtime/knowledge/knowledge_fabric_engine.py:191` set comprehension rebuilding `existing` from all prior relationships on every insert.

Root loop:

- `runtime/knowledge/knowledge_fabric_engine.py:373` `KnowledgeFabricEngine._discover_cross_domain_links`
- Loop condition: `for index, left in enumerate(entities): for right in entities[index + 1:]:`
- Termination: finite pairwise traversal over all semantic entities.
- Necessity: cross-domain discovery may be necessary, but the duplicate check is unnecessarily O(current_relationships) per insertion.

## 3. Measured duration

In the 180s cutoff run:

- `KnowledgeFabricEngine.integrate`: 76.014s cumulative.
- `KnowledgeFabricRegistry.add_relationship`: 45.442s cumulative across 11,329 calls.
- `KnowledgeFabricRegistry.add_relationship` inner set comprehension: 44.057s self time across 11,329 calls.
- `KnowledgeFabricEngine._discover_cross_domain_links`: 42.489s cumulative.
- `KnowledgeFabricEngine.build_report`: 25.342s cumulative after relationship generation.
- `KnowledgeFabricEngine._fabric_topology_intelligence`: 20.973s cumulative.
- `KnowledgeFabricEngine._reasoning_corridors`: 18.364s cumulative.

In the 120s cutoff run, the same function dominated while still in progress:

- `KnowledgeFabricEngine.integrate`: 56.632s cumulative.
- `KnowledgeFabricRegistry.add_relationship`: 51.502s cumulative across 9,047 calls.
- Inner set comprehension: 49.796s self time.

## 4. Call count

Top repeated calls in the 180s profile:

| Function | Calls | Cumulative | Self |
|---|---:|---:|---:|
| `builtins.isinstance` | 17,578,875 | 13.009s | 6.099s |
| `dict.get` | 14,199,238 | 4.054s | 4.054s |
| `json.encoder._iterencode_dict` | 13,978,033 | 16.230s | 11.145s |
| `copy.deepcopy` | 3,698,433 | 21.023s | 12.445s |
| `runtime/cognitive_runtime/execution_engine.py:1494 _deep_size` | 1,382,685 | 8.202s | 2.845s |
| `KnowledgeFabricRegistry.add_relationship` | 11,329 | 45.442s | 0.568s |
| `SemanticMemoryRegistry.add_relationship` set comprehension | 4,601 | 6.778s | 6.778s |

## 5. Root cause

The primary root cause is repeated full-registry reconstruction during relationship insertion.

`KnowledgeFabricRegistry.add_relationship` rebuilds this set on every call:

```python
existing = {
    (rel["source_entity_id"], rel["target_entity_id"], rel["relation_type"])
    for rel in self.fabric_relationships
}
```

Because `_discover_cross_domain_links` performs a pairwise concept/domain traversal and calls `add_relationship` repeatedly, total duplicate-check cost grows roughly with relationship_count squared. The execution is finite, but it appears hung because each later insertion scans a larger list.

The same pattern exists in `runtime/memory/semantic_memory_engine.py:153`, where `SemanticMemoryRegistry.add_relationship` rebuilds an `existing` set for every semantic relationship insertion.

## 6. Secondary bottlenecks

Top 20 by cumulative time, 180s run:

| # | Function | Cumulative | Self | Calls |
|---:|---|---:|---:|---:|
| 1 | `main.py:<module>` | 180.339s | 0.005s | 1 |
| 2 | `CognitiveRuntimeExecutionEngine.build_report` | 92.281s | 0.020s | 1 |
| 3 | `_produce_post_execution_cognitive_memory` | 92.211s | 0.015s | 1 |
| 4 | `KnowledgeFabricEngine.integrate` | 76.014s | 0.000s | 1 |
| 5 | `pipeline.run` proxy | 59.656s | 0.000s | 1 |
| 6 | `AdaptiveCognitivePipeline.run` | 56.518s | 0.019s | 1 |
| 7 | `KnowledgeFabricRegistry.add_relationship` | 45.442s | 0.568s | 11,329 |
| 8 | `KnowledgeFabricRegistry.add_relationship.<setcomp>` | 44.057s | 44.057s | 11,329 |
| 9 | `_discover_cross_domain_links` | 42.489s | 3.577s | 1 |
| 10 | `KnowledgeFabricEngine.build_report` | 25.342s | 0.001s | 1 |
| 11 | `copy.deepcopy` | 21.023s | 12.445s | 3,698,433 |
| 12 | `_fabric_topology_intelligence` | 20.973s | 0.088s | 1 |
| 13 | `_reasoning_corridors` | 18.364s | 3.177s | 1 |
| 14 | `_compact_final_context` | 18.117s | 0.017s | 1 |
| 15 | `copy._deepcopy_dict` | 18.116s | 2.770s | 196,744 |
| 16 | `json.encoder._iterencode` | 18.014s | 1.783s | 2,590,566 |
| 17 | `CompactReportBuilder.compact_context` | 17.875s | 0.000s | 2 |
| 18 | `CompactReportCompressionEngine.compress` | 17.754s | 0.000s | 2 |
| 19 | `copy._deepcopy_list` | 16.951s | 0.638s | 96,537 |
| 20 | `json.dump` wrapper | 16.603s | 0.000s | 5 |

Top 20 by self time, 180s run:

| # | Function | Self | Calls |
|---:|---|---:|---:|
| 1 | `knowledge_fabric_engine.py:191 <setcomp>` | 44.057s | 11,329 |
| 2 | `copy.deepcopy` | 12.445s | 3,698,433 |
| 3 | `json.encoder._iterencode_dict` | 11.145s | 13,978,033 |
| 4 | `semantic_memory_engine.py:153 <setcomp>` | 6.778s | 4,601 |
| 5 | `builtins.isinstance` | 6.099s | 17,578,875 |
| 6 | `dict.get` | 4.054s | 14,199,238 |
| 7 | `builtins.round` | 4.034s | 3,475,659 |
| 8 | `compact_report_compression_engine.py:643 visit` | 4.026s | 904,470 |
| 9 | `_discover_cross_domain_links` | 3.577s | 1 |
| 10 | `json.encoder._iterencode_list` | 3.536s | 4,703,285 |
| 11 | `dataclasses._asdict_inner` | 3.472s | 794,077 |
| 12 | `_reasoning_corridors` | 3.177s | 1 |
| 13 | `_deep_size` | 2.845s | 1,382,685 |
| 14 | `_number` | 2.819s | 1,370,516 |
| 15 | `clamp` | 2.800s | 1,441,906 |
| 16 | `copy._deepcopy_dict` | 2.770s | 196,744 |
| 17 | `typing.__subclasscheck__` | 2.496s | 1,316,086 |
| 18 | `CompactReportBuilder._purge_value` | 2.448s | 693,263 |
| 19 | `knowledge_fabric_engine.py:1148 <listcomp>` | 2.233s | 563,260 |
| 20 | `knowledge_reuse_engine.py:257 <setcomp>` | 2.040s | 900 |

## 7. Work continuing after success

Post-success work is substantial.

The stack samples show:

- 30s: still inside `pipeline.run`, compacting final task context via `CompactReportCompressionEngine._collect_anomalies`.
- 60s: still inside `pipeline.run`, deep-copying large appendix data in `CompactReportCompressionEngine._compress_dict`.
- 120s: after task pipeline, `main.py:4331` calls `cognitive_runtime_execution_engine.build_report`, which invokes `_produce_post_execution_cognitive_memory`, `SemanticMemoryEngine.integrate`, then `KnowledgeFabricEngine.integrate`.
- 170s: `main.py:4343` persists `shared_cognitive_state.save()` and spends time in `json.dumps`.
- 180s cutoff: `main.py:4643` enters `final_report_renderer.render`; `canonical_report_binding_engine.discover_sources` deep-copies large performance structures.

This occurs despite the configured fast/minimal run:

- `mode=fast`
- `report_level=minimal`
- `telemetry_enabled=False`
- `post_success_mode=fast`
- `shutdown_mode=fast`

Mode-policy violation: `CognitiveRuntimeExecutionEngine.build_report` has no observed fast-mode gate before `_produce_post_execution_cognitive_memory`.

## 8. Duplicate computations

Confirmed duplicate or repeated expensive computations:

- `KnowledgeFabricRegistry.add_relationship` rebuilds the full relationship marker set 11,329 times.
- `SemanticMemoryRegistry.add_relationship` rebuilds the full relationship marker set 4,601 times.
- `CompactReportCompressionEngine._collect_anomalies` recursively traverses large reports and lists up to 100 entries per list.
- `CompactReportCompressionEngine._compress_dict` deep-copies large appendix payloads during minimal reporting.
- `CanonicalReportBindingEngine._first_dict` deep-copies large report sources during final rendering.
- `shared_cognitive_state.save` serializes large nested state after the expensive cognitive execution report.

## 9. Mode-policy violations

Fast profile declares:

- `max_reasoning_depth=2`
- `max_hypotheses=2`
- `max_active_routes=3`
- `telemetry_enabled=False`
- `explanation_enabled=False`
- `process_semantics_enabled=False`
- `report_level=minimal`
- `finalization_mode=fast`

Observed violations or mismatches:

- Post-execution cognitive memory conversion runs in `main.py:4331` through `CognitiveRuntimeExecutionEngine.build_report` even in fast/minimal mode.
- Knowledge fabric cross-domain discovery and topology intelligence run during finalization, not task solving.
- Minimal report compaction still performs recursive anomaly scans and deep copies of large appendix sections.
- Final report rendering still performs canonical source discovery and deep copies after shutdown-mode fast.
- Shared cognitive state serialization runs synchronously after terminal success.

No evidence that blocked disk I/O is the primary cause. Disk read/write timings were small; CPU serialization and repeated aggregation dominate.

## 10. Loop and recursion audit

| File/function | Loop/recursion | Count/time | Termination | Necessary? |
|---|---|---:|---|---|
| `runtime/knowledge/knowledge_fabric_engine.py:373 _discover_cross_domain_links` | nested `entities x entities[index+1:]` | 42.489s | finite entity pair list | conceptually necessary, but too broad for fast finalization |
| `runtime/knowledge/knowledge_fabric_engine.py:143 add_relationship` | rebuild existing marker set from `self.fabric_relationships` per insert | 11,329 calls, 44.057s self in setcomp | finite insert attempts | duplicate check necessary; repeated rebuild is not |
| `runtime/memory/semantic_memory_engine.py:343 _relationships_from_entities` | nested all-pairs over semantic entities | 4,601 duplicate-check setcomp calls, 6.778s self | finite entity pair list | relationship generation may be necessary; per-insert full scan is not |
| `runtime/reporting/compact_report_compression_engine.py:643 visit` | recursive dict/list traversal | 904,470 calls, 5.084s cumulative | finite tree, list capped at 100 | too expensive for minimal fast output |
| `runtime/reporting/compact_report_compression_engine.py:270 _compress_dict` | deep-copy appendix data | visible in 60s stack, 21.023s total deepcopy | finite report tree | not appropriate for minimal console path |
| `runtime/reporting/canonical_report_binding_engine.py:739 _first_dict` | deep-copy source report during binding | active at 180s cutoff | finite source list | should not copy whole structures in fast/minimal |
| `runtime/meta/supervisor/task_signature_engine.py:129 _collect_values` | recursive full-context scan | 5.346s cumulative in 120s run | finite context tree | suspicious in fast mode; should be bounded |

## Blocking I/O operations

Measured blocking file operations were not the main bottleneck.

Largest direct file reads/writes in the 180s profile:

- `Path.read_text:C:\Users\SERVICE INFO\AMIS\runtime\memory\context_memory.json`: 5 calls, 0.185s total.
- `Path.read_text:runtime\memory\context_memory.json`: 2 calls, 0.073s total.
- `Path.read_text:runtime\artifacts\runtime_data\route_intelligence_memory.json`: 4 calls, 0.043s total.
- `Path.write_text:runtime\artifacts\runtime_data\shared_cognitive_state\latest.json`: 2 calls, 0.032s total.

Serialization CPU was significant:

- `json.dump`: 5 calls, 16.603s total, max 15.698s.
- `json.dumps`: 4,553 calls, 6.533s total.
- `json.loads`: 1,001 calls, 1.504s total.
- `json.load`: 403 calls, 1.005s total.

Conclusion: persistence overhead is mostly JSON serialization of large structures, not disk latency.

## Reporting overhead

Reporting/finalization overhead is confirmed:

- `_compact_final_context`: 18.117s.
- `CompactReportBuilder.compact_context`: 17.875s across 2 calls.
- `CompactReportCompressionEngine.compress`: 17.754s across 2 calls.
- `CompactReportCompressionEngine.visit`: 4.026s self over 904,470 calls.
- `copy.deepcopy`: 21.023s cumulative.
- `json.dump/json.dumps`: 23.135s total serialization CPU.
- Final renderer was still running at 180s cutoff in `final_report_renderer.render -> canonical_report_binding_engine.bind -> discover_sources -> _first_dict -> deepcopy`.

## Registry rebuilds

Confirmed registry rebuilds:

- Knowledge fabric relationship marker registry is rebuilt per relationship insertion.
- Semantic memory relationship marker registry is rebuilt per relationship insertion.
- Canonical report binding deep-copies source registries/reports rather than binding by reference or summary in minimal mode.

## Finalization overhead

Finalization is the long-running region:

- `CognitiveRuntimeExecutionEngine.build_report`: 92.281s.
- `_produce_post_execution_cognitive_memory`: 92.211s.
- `KnowledgeFabricEngine.integrate`: 76.014s.
- Shared state JSON save was active at 170s.
- Final report renderer and canonical binding were active at 180s cutoff.

## Recommendations

1. `REMOVE_DUPLICATION` / `SAFE_PATCH`: maintain an incremental relationship marker set in `KnowledgeFabricRegistry` instead of rebuilding `existing` on every `add_relationship`.
2. `REMOVE_DUPLICATION` / `SAFE_PATCH`: apply the same marker-set fix to `SemanticMemoryRegistry`.
3. `MODE_GATING_FIX`: in fast mode or `post_success_mode=fast`, skip or summarize `_produce_post_execution_cognitive_memory`; do not run knowledge fabric cross-domain discovery after terminal success.
4. `MODE_GATING_FIX`: make minimal report compaction avoid recursive anomaly scans and appendix deep copies unless diagnostic/full report level is requested.
5. `CACHE_CANDIDATE`: cache knowledge fabric topology intelligence and reasoning corridors by semantic-memory report signature.
6. `CACHE_CANDIDATE`: cache canonical report source binding by object id/signature during a single finalization pass.
7. `ASYNC_CANDIDATE`: defer shared cognitive state persistence and full report artifact JSON writing after fast terminal success.
8. `ARCHITECTURAL_FIX`: separate task-solving result finalization from cognitive ecosystem expansion. Fast/adaptive task success should return before ecosystem introspection unless explicitly requested.
9. `SAFE_PATCH`: add diagnostic counters for relationship insert attempts, unique relationships, entity-pair comparisons, report tree nodes visited, deep-copy bytes/objects, and serialized JSON bytes.
10. `MODE_GATING_FIX`: enforce `explanation_enabled=False` and `process_semantics_enabled=False` through post-success and report layers, not only reasoning-budget setup.

## Conclusion

The apparent hang is caused by post-success observability/finalization work, not ARC task solving. The exact primary bottleneck is repeated relationship-registry reconstruction in `KnowledgeFabricRegistry.add_relationship`, triggered by post-execution cognitive memory generation from `CognitiveRuntimeExecutionEngine.build_report`. Secondary costs come from semantic memory using the same duplicate-check pattern, report compression deep copies, JSON serialization, shared-state persistence, and final report canonical binding.

