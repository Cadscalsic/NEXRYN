# Phase 7 Prelude Training Curriculum

The first persistent curriculum batch adds `task_007.json` through
`task_036.json` to the original six ARC training tasks.

The scarcity follow-up batch adds `task_087.json` through `task_101.json`.
It raises metadata coverage for `topological_change`,
`topological_reasoning`, and `density_modulation` to at least `20` tasks
each.

## Distribution

| Group | Tasks | Purpose |
| --- | ---: | --- |
| density | 6 | Preserve or probe object density under movement and symmetry |
| symbolic_remapping | 6 | Learn direct, one-to-one, and many-to-one color remapping |
| replication | 4 | Duplicate objects horizontally or vertically |
| growth | 4 | Extend objects and probe topological growth |
| topology | 4 | Preserve topology under rotation, symmetry, and movement |
| mixed | 6 | Combine remapping, density, topology, growth, or replication |

The batch contains `14` direct tasks, `10` matched-boundary probes, and `6`
composite tasks. Each generated ARC file has two training examples and one
test input. `nexryn_metadata` documents the intended learning target without
changing the standard `train` and `test` ARC payload.

## Reproduction

Run:

```powershell
.\.venv\Scripts\python.exe tools\generate_training_curriculum.py
```

The generator deterministically rewrites only `task_007.json` through
`task_036.json`.

## Runtime Batches

`main.py` uses `TrainingAssistant` to execute five ARC files per runtime
cycle. The persistent cursor is stored in:

```text
runtime_data/training_assistant_state.json
```

The assistant resumes an interrupted active batch and advances only after
the current batch finishes. Selection ranks tasks by concept coverage gap
and lifecycle state. For scarce concepts, previously unseen tasks are chosen
before recycled tasks so each runtime cycle can add independent evidence.

The final training report also prints concept lifecycle maturity:

```text
DISCOVERING
SUPPORTED
GENERALIZING
BOUNDARY_REFINEMENT
TRUTH_CANDIDATE
STABLE_TRUTH
```

Task count can advance a concept through `GENERALIZING`. Promotion to
`TRUTH_CANDIDATE` and `STABLE_TRUTH` still requires the existing epistemic
and truth-registry gates.

Cross-cycle replication evidence is persisted atomically in:

```text
runtime_data/knowledge_replication_ledger.json
```

This allows five-task runtime batches to accumulate concept maturity across
separate Python processes without converting repeated task execution into
duplicate evidence.

At process startup, persisted replication records are rehydrated into the
epistemic evidence registry. The compact final report exposes both candidate
promotion and the later identity-safe truth-commit gate:

```text
TRUTH CANDIDATE REPORT
TRUTH COMMIT REPORT
```

This keeps `TRUTH_CANDIDATE` distinct from `STABLE_TRUTH`: a candidate may
remain a belief while identity continuity, semantic drift, repair, or
containment checks are unresolved.

Identity-safe recovery progress is also persisted atomically:

```text
runtime_data/semantic_spine_recovery.json
runtime_data/reversible_rehearsal_state.json
```

Restarting Python no longer discards safe recovery streaks or reuses rehearsal
cycle identifiers. Promotion still requires three distinct validated,
reversible sandbox rehearsal cycles; persistence does not bypass the gate.
Sandbox checkpoints accumulate simulated continuity gains and drift reduction
across rehearsals. They remain simulation-only until the recovery gate confirms
three safe cycles, so staged repair cannot write directly into persistent
identity.

To restart from the first batch, run:

```powershell
.\.venv\Scripts\python.exe main.py --reset-training-assistant
```
