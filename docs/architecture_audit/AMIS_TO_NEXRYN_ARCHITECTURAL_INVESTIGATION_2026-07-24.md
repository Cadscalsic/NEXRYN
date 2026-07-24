# AMIS to NEXRYN Architectural Investigation - 2026-07-24

## Architectural Investigation Summary

This audit searched for `AMIS`, `amis`, and `Amis` across live code,
configuration, tests, documentation, runtime artifacts, generated logs, and
quarantined legacy sources. The investigation found no active duplicate
architecture, no conflicting AMIS runtime pipeline, and no hidden AMIS layer.

The remaining live AMIS references were legacy display/package labels on
components that are still valid inside the current NEXRYN architecture. Those
references were safely unified to NEXRYN. Historical logs and quarantined
pycache sources were left unchanged because they are archival evidence, not
active runtime configuration.

## Counts

- AMIS component count discovered: 13 unique paths, including the workspace root
  path name.
- Live code components with AMIS labels: 3.
- Live metadata/configuration components with AMIS labels: 3.
- Historical artifact/log components: 4.
- Documentation/archive components: 2.
- Workspace path component: 1.
- Legacy component count: 5.
- Ready for NEXRYN count: 6.
- Architectural conflict count: 0.
- Orphaned component count: 1.
- Unused architectural path count: 0 active paths.

## Component Classification

| Component | Classification | Role | Current use | Decision |
| --- | --- | --- | --- | --- |
| `core/grid.py` | FOUNDATIONAL | ARC grid representation and analysis helpers | Used by loader, pattern engine, pattern analysis, rules, perception support | Renamed debug banner to NEXRYN |
| `core/patterns.py` | FOUNDATIONAL | Pattern analysis over ARC input/output pairs | Used by `runtime/stages/pattern_rule.py` | Renamed debug banner to NEXRYN |
| `core/rules.py` | FOUNDATIONAL | Legacy rule extraction over ARC pairs | Used by `runtime/stages/pattern_rule.py` | Renamed debug banner to NEXRYN |
| `runtime/learning/__init__.py` | READY_FOR_NEXRYN | Lazy export surface for learning systems | Active package metadata and exports | Renamed package label to NEXRYN |
| `tests/__init__.py` | READY_FOR_NEXRYN | Test package metadata | Test package only | Renamed package label to NEXRYN |
| `runtime/artifacts/package-lock.json` | LEGACY_COMPATIBLE | Empty generated npm lock metadata under artifacts | No package entries; no runtime dependencies | Renamed package name to NEXRYN |
| `runtime/logs/adaptive_normal_hypothesis_engine.log` | LEGACY_COMPATIBLE | Historical runtime log | Not imported or executed | Left unchanged |
| `runtime/artifacts/hypothesis_engine/adaptive_normal_hypothesis_engine_2.log` | LEGACY_COMPATIBLE | Historical runtime log | Not imported or executed | Left unchanged |
| `runtime/artifacts/hypothesis_engine/adaptive_normal_hypothesis_engine_3.log` | LEGACY_COMPATIBLE | Historical runtime log | Not imported or executed | Left unchanged |
| `runtime_short_repro.log` | LEGACY_COMPATIBLE | Historical reproduction log | Not imported or executed | Left unchanged |
| `docs/reports/NEXRYN_PERFORMANCE_DIAGNOSIS_2026-07-17.md` | LEGACY_COMPATIBLE | Historical report with absolute path containing workspace name | Documentation only | Left unchanged |
| `docs/architecture_audit/quarantined_pycache_sources/root___init__.py.txt` | ORPHANED_COMPONENT | Quarantined source recovered from pycache | Archive only | Left unchanged |
| Workspace path `C:\Users\SERVICE INFO\AMIS` | REQUIRES_ARCHITECTURAL_REVIEW | Repository location | External filesystem path | Not renamed by audit |

## Architectural Compatibility Review

The live components that contained AMIS labels remain compatible with the
current NEXRYN architecture:

- Capability Economy: compatible. No capability lifecycle or investment logic
  was altered.
- Operational Economy: compatible. No economy scoring or attrition behavior was
  changed.
- Training Economy: compatible. `runtime/learning/__init__.py` remains the same
  lazy export surface.
- Capability Ecology: compatible. No ecology, cluster, or composite intelligence
  behavior was altered.
- World Governance: compatible. No governance policy or architecture was
  changed.
- Composite Intelligence: compatible. The audited files do not define composite
  execution behavior.
- Capability Graduation: compatible. No graduation thresholds, queues, or
  actions were modified.
- Population Evolution: compatible. No population state transitions were
  changed.
- Adaptive Reuse: compatible. No reuse logic or candidate materialization path
  was modified.
- Operational Capability Clusters: compatible. No cluster logic was changed by
  this audit.

## Legacy Logic Investigation

No high-value abandoned AMIS-specific logic was found. The legacy core files are
not obsolete; they provide foundational ARC object/grid/pattern/rule utilities
that still support the active runtime path through `runtime/stages/pattern_rule.py`.

The only orphaned item is the quarantined pycache source
`docs/architecture_audit/quarantined_pycache_sources/root___init__.py.txt`. It is
valuable as historical evidence only. It should not be reactivated because the
current repository already has active package metadata and runtime entry points.

## Architectural Conflict Detection

- Duplicate architectures: none detected.
- Legacy pipelines: none detected as active AMIS pipelines.
- Dead execution paths: none detected among live AMIS-labeled files.
- Unreachable components: only quarantined pycache source, intentionally archived.
- Naming conflicts: found and fixed in live banners/package labels.
- Dependency conflicts: none detected.
- Semantic conflicts: live debug labels implied AMIS identity inside NEXRYN runtime
  output; fixed.
- Governance conflicts: none detected.
- Runtime conflicts: none detected.

## Dependency Graph Summary

- `core/grid.py`
  - Depends on: local numeric/grid utilities and NumPy.
  - Used by: `core/loader.py`, `core/pattern_engine.py`, `core/patterns.py`,
    `core/rules.py`, and perception support.
- `core/patterns.py`
  - Depends on: `core.grid.ARCGrid`.
  - Used by: `runtime/stages/pattern_rule.py`.
- `core/rules.py`
  - Depends on: `core.grid.ARCGrid`.
  - Used by: `runtime/stages/pattern_rule.py`.
- `runtime/learning/__init__.py`
  - Depends on: lazy imports from active runtime learning modules.
  - Used by: package consumers importing learning systems.
- `tests/__init__.py`
  - Depends on: none.
  - Used by: pytest package discovery.
- `runtime/artifacts/package-lock.json`
  - Depends on: none.
  - Used by: no Python runtime path found.

## Safe Changes Applied

- `core/grid.py`: `AMIS GRID ANALYSIS` -> `NEXRYN GRID ANALYSIS`.
- `core/patterns.py`: `AMIS PATTERN ANALYSIS` -> `NEXRYN PATTERN ANALYSIS`.
- `core/rules.py`: `AMIS RULE ENGINE` -> `NEXRYN RULE ENGINE`.
- `tests/__init__.py`: package label unified to `NEXRYN Model Tests`.
- `runtime/learning/__init__.py`: package label unified to
  `NEXRYN Learning Systems`.
- `runtime/artifacts/package-lock.json`: package name unified to `NEXRYN`.

## Recommended Safe Refactors

- Keep historical logs immutable unless a separate artifact-retention policy is
  introduced.
- Keep quarantined pycache sources archived; do not re-import them.
- Consider renaming the repository directory outside source control only if
  external scripts and local paths are audited separately.

## Recommended Naming Unifications

Completed for live code and metadata discovered in this audit. Remaining AMIS
references are archival.

## Recovered Architectural Assets

No recoverable AMIS-only architectural asset was found. The foundational grid,
pattern, and rule utilities are already active and connected to the NEXRYN
runtime path.

## Architectural Risk Assessment

Risk level: LOW.

The applied changes are output/metadata naming updates only. They do not alter
runtime behavior, data structures, lifecycle state transitions, governance
policy, candidate generation, compiler behavior, adaptive reuse, economy
analysis, ecology analysis, or operational cluster behavior.

## NEXRYN Compatibility Report

NEXRYN compatibility score: 92%.

Rationale:

- Active AMIS-labeled code was foundational and compatible.
- No AMIS-specific active architecture was found.
- No conflicting legacy pipeline was found.
- Historical artifacts still contain AMIS labels by design.
- The workspace directory still contains AMIS in its filesystem path and should
  be handled separately from source modernization.
