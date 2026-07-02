# NEXRYN Reporting Architecture Map

## Reporting Hierarchy

| Tier | Mode | Purpose | Runtime posture |
| --- | --- | --- | --- |
| 1 | `minimal` | Fast production execution | Current status, selected tasks, failures, success/resource metrics |
| 2 | `normal` | Daily development | Summaries for tasks, dependencies, contexts, truth, warnings, blockers |
| 3 | `full` | Deep investigation | Expanded subsystem diagnostics and promotion/governance traces |
| 4 | `debug` | Developer debugging | Raw internal structures and full traces where available |
| 5 | `audit` | Architectural inspection | Historical archives and complete lineage/source records |

All terminal-facing reports must pass through `runtime/reporting/output_governor.py`
or through `CompactReportBuilder`, which delegates report-level semantics to the
governor. Normal runtime output is now a present-state dashboard, not an archive
viewer.

## Unified Schema

Required fields:

- `system`
- `report_state`
- `status`
- `timestamp`
- `summary`
- `metrics`
- `warnings`
- `failures`
- `recommendations`

Advanced-only fields:

- `details`
- `archives`
- `traces`
- `history`

`details`, `archives`, `traces`, and `history` are emitted only in `full`,
`debug`, or `audit` mode.

## Historical Structures Audit

| Structure | Primary locations | Why it exists | Consumers | Runtime output decision |
| --- | --- | --- | --- | --- |
| `observed_tasks`, `observed_task_history` | `runtime/reporting/compact_report_builder.py`, training reports, ledger-derived reports | Track cross-task concept observations | Concept maturity, curriculum diversity, audits | Counts only in `minimal`/`normal`; visible in `audit` |
| `task_sources`, `source_tasks`, `training_files`, `source_files` | `core/truth/*`, `runtime/truth_registry/*`, `runtime/reporting/compact_report_builder.py` | Truth provenance and evidence lineage | Truth registry, commit engine, audit tools | Counts only unless `full/debug/audit` |
| `task_history` | `runtime/agents/agent_runtime.py`, compact builder | Agent planning memory | Agent runtime summaries | Count/latest active task only in runtime output |
| `concept_history`, `observation_history` | `runtime/context/semantic_context_builder.py` | Semantic context generation | Context builders | Summarized as counts in normal output |
| `dependency_history`, dependency chains, dependency lineage | Dependency engines, `runtime/learning/training_report.py` | Dependency reasoning and promotion support | Dependency telemetry, architecture bottleneck report | Metrics only in normal output; chains only advanced |
| `semantic_history`, `trace_history`, `lineage_history` | `core/cognition/concept_lineage.py`, governance pruning, genome/pharmacy modules | Long-term lineage and stability inspection | Governance pruning, cognitive genome, pharmacy diagnostics | Hidden from runtime output except advanced modes |
| `knowledge_sources`, `evidence_sources` | Truth commit/registry layers, process context generation | Evidence provenance and truth support | Truth commitment, registry persistence | Counts in normal output; lists only advanced |
| `memory_archives`, `context_archives` | Memory storage and context systems | Persistent memory/context inspection | Audit and recovery tooling | Hidden from runtime output except advanced modes |
| `cache_entries`, cache inventories | `runtime/planning/cognitive_cache_manager.py`, dependency executor cache reports | Cache diagnostics and reuse accounting | Cache managers, performance reports | Cache hit/miss/reuse metrics only; contents advanced only |
| `historical_diagnostics` and equivalent raw reports | Legacy pipeline, compact builder heavy keys, training diagnostics | Deep debugging | Developer/audit workflows | Suppressed or summarized unless advanced |

## Active Runtime Dashboard Owners

| Subsystem | Normal output fields |
| --- | --- |
| Task manager | `selected_tasks`, `active_tasks`, `completed_tasks`, `failed_tasks`, `skipped_tasks`, `training_batch_size`, `execution_progress` |
| Concept reporting | `concept_name`, `current_stage`, `confidence`, `support_score`, `contradiction_score`, `promotion_score`, `observation_count`, `candidate_ready`, `last_updated`, `state`, `history_count` |
| Dependency reporting | `dependency_chains_executed`, `dependency_chain_depth`, `dependency_chain_coverage`, `dependency_coherence`, `dependency_reasoning_time`, `dependency_activation_state`, `dependency_failures` |
| Context reporting | `context_count`, `semantic_context_count`, `process_context_count`, `causal_context_count`, `world_context_count`, `context_generation_time`, `context_confidence`, `context_registration_rate` |
| Truth reporting | `discovering_count`, `supported_count`, `validated_count`, `candidate_count`, `committed_count`, `locked_truth_count`, `promotion_rate`, `truth_commit_rate`, `promotion_failures`, `blocking_factors` |
| Cache reporting | `cache_hits`, `cache_misses`, `reuse_rate`, `strategy_hits`, `truth_hits`, `context_hits`, `estimated_compute_saved`, `estimated_runtime_saved` |

## Implementation Notes

- `runtime/reporting/output_governor.py` owns terminal flood prevention, limits,
  archive hiding, unified schema creation, and runtime dashboard projection.
- `runtime/reporting/compact_report_builder.py` still protects large nested
  structures, but now uses governor tiers and hides historical list contents in
  `minimal`/`normal`.
- `runtime/learning/training_report.py` routes `minimal` and `normal` through
  the runtime dashboard. The legacy expanded printer remains available for
  `full`, `debug`, and `audit`.
- `main.py` accepts all five report levels and the batch preamble shows only the
  active selected task batch with governor limits.
