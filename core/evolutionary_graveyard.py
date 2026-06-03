from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import threading
from collections import Counter


@dataclass
class GraveyardEntry:
    id: str
    category: str  # e.g. 'strategy', 'merge', 'concept', 'lineage', 'mutation'
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum,
            ),
        ),
        4,
    )


class CognitiveGraveyardPressureEngine:
    """Compute evolutionary psychological load from failure debris."""

    def compute(self, entries, context=None):

        if context is None:

            context = {}

        categories = Counter(
            entry.category
            for entry in entries
        )

        failed_merges = categories.get(
            "merge",
            0,
        )

        extinct_concepts = (
            categories.get(
                "strategy",
                0,
            )
            +
            categories.get(
                "concept",
                0,
            )
        )

        unsafe_evolution = len([
            entry
            for entry in entries
            if (
                entry.category == "mutation"
                or "unsafe" in entry.reason
                or "destructive" in entry.reason
            )
        ])

        unstable_lineages = len([
            lineage
            for lineage, count in Counter(
                entry.details.get(
                    "lineage",
                )
                for entry in entries
                if entry.details.get(
                    "lineage",
                )
            ).items()
            if count >= 2
        ])

        ontology_damage = _clamp(
            sum(
                _clamp(
                    entry.details.get(
                        "ontology_damage",
                        0.0,
                    )
                )
                for entry in entries
            )
        )

        entropy_pruning = 0.0

        entropy_report = context.get(
            "entropy_regulator_report",
            {},
        )

        if entropy_report.get(
            "stabilization_windows",
            {},
        ).get(
            "window_state",
        ) == "freeze_new_mutations":

            entropy_pruning = 1.0

        pressure_score = _clamp(
            failed_merges
            * 0.08
            +
            unstable_lineages
            * 0.12
            +
            ontology_damage
            * 0.18
            +
            entropy_pruning
            * 0.10
            +
            extinct_concepts
            * 0.08
            +
            unsafe_evolution
            * 0.12
        )

        return {
            "engine":
            "cognitive_graveyard_pressure_engine",

            "pressure_score":
            pressure_score,

            "pressure_state":
            (
                "graveyard_pressure_critical"
                if pressure_score >= 0.72
                else "graveyard_pressure_high"
                if pressure_score >= 0.48
                else "graveyard_pressure_elevated"
                if pressure_score >= 0.24
                else "graveyard_pressure_low"
            ),

            "factors":
            {
                "failed_merges":
                failed_merges,

                "unstable_lineages":
                unstable_lineages,

                "ontology_damage":
                ontology_damage,

                "entropy_pruning":
                entropy_pruning,

                "extinct_concepts":
                extinct_concepts,

                "unsafe_evolution":
                unsafe_evolution,
            },

            "affective_signature":
            (
                "lineage_trauma_and_merge_catastrophe_load"
                if pressure_score >= 0.48
                else "evolutionary_stress_memory"
                if pressure_score >= 0.24
                else "low_graveyard_load"
            ),
        }


class EvolutionaryGraveyard:
    """Manage and study evolutionary failure debris.

    Responsibilities:
    - record extinct strategies, failed merges, pruned concepts, failed lineages, unsafe mutations
    - provide cognitive paleontology helpers (collapse causes, toxic lineages, destructive mutations)
    - export/load reports for downstream inspection
    """

    def __init__(self) -> None:
        self._entries: List[GraveyardEntry] = []
        self._entry_keys = set()
        self._history: List[Dict[str, Any]] = []
        self.pressure_engine = CognitiveGraveyardPressureEngine()
        self._lock = threading.RLock()

    def _entry_key(
        self,
        id: str,
        category: str,
        reason: str,
    ):

        return (
            str(id),
            str(category),
            str(reason),
        )

    def add_entry(
        self,
        id: str,
        category: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> GraveyardEntry:
        """Add a graveyard entry and return it."""
        if details is None:
            details = {}

        key = self._entry_key(
            id,
            category,
            reason,
        )

        with self._lock:

            if key in self._entry_keys:

                for entry in reversed(self._entries):

                    if self._entry_key(
                        entry.id,
                        entry.category,
                        entry.reason,
                    ) == key:

                        return entry

            self._entry_keys.add(
                key,
            )

            entry = GraveyardEntry(
                id=id,
                category=category,
                reason=reason,
                details=details,
            )

            self._entries.append(entry)

        return entry

    def list_entries(self, category: Optional[str] = None) -> List[GraveyardEntry]:
        """Return entries, optionally filtered by `category`."""
        with self._lock:
            return [e for e in self._entries if category is None or e.category == category]

    def analyze_causes(self, top_n: int = 10) -> Dict[str, int]:
        """Return a frequency map of top reasons for failures."""
        with self._lock:
            counter = Counter(e.reason for e in self._entries)
            return dict(counter.most_common(top_n))

    def find_toxic_lineages(self, threshold: int = 3) -> Dict[str, int]:
        """Identify lineages that appear at least `threshold` times in details['lineage']."""
        with self._lock:
            lineage_counts = Counter(
                e.details.get("lineage") for e in self._entries if e.details.get("lineage") is not None
            )
            return {k: v for k, v in lineage_counts.items() if v >= threshold}

    def destructive_mutation_patterns(self, top_n: int = 10) -> Dict[str, int]:
        """Return destructive mutation types observed in the graveyard."""
        with self._lock:
            patterns = Counter()

            for entry in self._entries:

                mutation_type = entry.details.get(
                    "mutation_type",
                )

                if (
                    entry.category == "mutation"
                    or "unsafe" in entry.reason
                    or "destructive" in entry.reason
                ):

                    patterns[
                        mutation_type
                        or entry.reason
                    ] += 1

            return dict(
                patterns.most_common(top_n)
            )

    def collapse_patterns(self, top_n: int = 10) -> Dict[str, int]:
        """Return the most common collapse signatures."""
        with self._lock:
            patterns = Counter()

            for entry in self._entries:

                collapse_source = entry.details.get(
                    "collapse_source",
                )

                collapse_state = entry.details.get(
                    "collapse_state",
                )

                if collapse_source:

                    patterns[
                        collapse_source
                    ] += 1

                elif collapse_state:

                    patterns[
                        collapse_state
                    ] += 1

            return dict(
                patterns.most_common(top_n)
            )

    def _add_extinction_entries(self, context):

        report = context.get(
            "extinction_engine_report",
            {},
        )

        for trait in report.get(
            "extinct_traits",
            [],
        ):

            trait_id = trait.get(
                "id",
                trait.get(
                    "trait_id",
                    trait.get(
                        "name",
                        "unknown_extinct_trait",
                    ),
                ),
            )

            self.add_entry(
                trait_id,
                "strategy",
                "extinct_trait",
                {
                    "lineage":
                    trait.get(
                        "lineage",
                        trait.get(
                            "lineage_origin",
                            trait.get(
                                "niche",
                            ),
                        ),
                    ),

                    "fitness":
                    trait.get(
                        "fitness",
                    ),

                    "stability_score":
                    trait.get(
                        "stability_score",
                    ),

                    "mutation_rate":
                    trait.get(
                        "mutation_rate",
                    ),
                },
            )

        for archive_entry in report.get(
            "extinction_archive",
            [],
        ):

            if not isinstance(
                archive_entry,
                dict,
            ):

                continue

            trait = archive_entry.get(
                "trait",
                archive_entry,
            )

            trait_id = trait.get(
                "id",
                trait.get(
                    "trait_id",
                    "archived_extinction",
                ),
            )

            self.add_entry(
                trait_id,
                "concept",
                archive_entry.get(
                    "reason",
                    "archived_extinction",
                ),
                {
                    "lineage":
                    trait.get(
                        "lineage",
                        trait.get(
                            "niche",
                        ),
                    ),

                    "archive_action":
                    archive_entry.get(
                        "action",
                    ),
                },
            )

    def _add_rejected_fusion_entries(self, context):

        report = context.get(
            "concept_fusion_report",
            {},
        )

        for rejected in report.get(
            "rejected_fusions",
            [],
        ):

            if not isinstance(
                rejected,
                dict,
            ):

                continue

            meta = rejected.get(
                "meta_concept",
                {},
            )

            source_concepts = meta.get(
                "source_concepts",
                rejected.get(
                    "source_concepts",
                    [],
                ),
            )

            merge_id = rejected.get(
                "fusion_id",
                "::".join(source_concepts)
                if source_concepts
                else rejected.get(
                    "concept_id",
                    "rejected_fusion",
                ),
            )

            self.add_entry(
                merge_id,
                "merge",
                rejected.get(
                    "rejection_reason",
                    rejected.get(
                        "fusion_state",
                        "rejected_fusion",
                    ),
                ),
                {
                    "lineage":
                    "::".join(source_concepts)
                    if source_concepts
                    else None,

                    "source_concepts":
                    source_concepts,

                    "fusion_stability":
                    rejected.get(
                        "fusion_stability",
                    ),
                },
            )

    def _add_failure_memory_entries(self, context):

        latest_failure = context.get(
            "cognitive_failure_memory",
            {},
        ).get(
            "latest_failure",
            {},
        )

        collapse_source = latest_failure.get(
            "collapse_source",
        )

        if not collapse_source:

            return

        self.add_entry(
            collapse_source,
            "merge",
            latest_failure.get(
                "contradiction_type",
                "unsafe_merge",
            ),
            {
                "lineage":
                collapse_source,

                "collapse_source":
                collapse_source,

                "ontology_damage":
                latest_failure.get(
                    "ontology_damage",
                ),

                "recovery_action":
                latest_failure.get(
                    "recovery_action",
                ),
            },
        )

    def _add_lineage_entries(self, context):

        report = context.get(
            "concept_lineage_report",
            {},
        )

        watched_records = (
            report.get(
                "failure_records",
                [],
            )
            +
            report.get(
                "mutation_records",
                [],
            )
        )

        for record in watched_records:

            if not isinstance(
                record,
                dict,
            ):

                continue

            concept_id = record.get(
                "concept_id",
                "unknown_lineage",
            )

            parents = record.get(
                "parents",
                [],
            )

            for mutation in record.get(
                "mutations",
                [],
            ):

                mutation_type = mutation.get(
                    "type",
                    "mutation",
                )

                survival_state = mutation.get(
                    "survival_state",
                    "",
                )

                is_destructive = (
                    "unsafe" in mutation_type
                    or "destructive" in mutation_type
                    or survival_state in [
                        "extinct",
                        "rejected",
                        "collapsed",
                    ]
                )

                if not is_destructive:

                    continue

                self.add_entry(
                    concept_id,
                    "mutation",
                    mutation_type,
                    {
                        "lineage":
                        "::".join(
                            parents
                            +
                            [
                                concept_id,
                            ]
                        )
                        if parents
                        else concept_id,

                        "mutation_type":
                        mutation_type,

                        "survival_state":
                        survival_state,

                        "ontology_damage":
                        mutation.get(
                            "ontology_damage",
                        ),

                        "recovery_action":
                        mutation.get(
                            "recovery_action",
                        ),
                    },
                )

    def _add_identity_entries(self, context):

        report = context.get(
            "identity_reasoner_report",
            {},
        )

        for analysis in report.get(
            "identity_analyses",
            [],
        ):

            failure = analysis.get(
                "failure_explanation",
                {},
            )

            if failure.get(
                "failure_state",
            ) != "identity_failure_explained":

                continue

            reasons = failure.get(
                "failure_reasons",
                [],
            )

            concepts = analysis.get(
                "concept_pair",
                analysis.get(
                    "concepts",
                    [],
                ),
            )

            merge_id = "::".join(
                concepts,
            ) if isinstance(
                concepts,
                list,
            ) else str(
                concepts,
            )

            self.add_entry(
                merge_id,
                "merge",
                "|".join(
                    reasons,
                )
                if reasons
                else "identity_failure",
                {
                    "lineage":
                    merge_id,

                    "failure_reasons":
                    reasons,

                    "repair_actions":
                    analysis.get(
                        "repair_plan",
                        {},
                    ).get(
                        "repair_actions",
                        [],
                    ),
                },
            )

    def _add_sandbox_entries(self, context):

        report = context.get(
            "evolution_sandbox_report",
            {},
        )

        for prediction in report.get(
            "collapse_predictions",
            [],
        ):

            if not isinstance(
                prediction,
                dict,
            ):

                continue

            self.add_entry(
                prediction.get(
                    "candidate_id",
                    prediction.get(
                        "strategy_id",
                        "collapse_prediction",
                    ),
                ),
                "strategy",
                prediction.get(
                    "collapse_state",
                    "collapse_predicted",
                ),
                {
                    "lineage":
                    prediction.get(
                        "lineage",
                    ),

                    "collapse_state":
                    prediction.get(
                        "collapse_state",
                    ),

                    "collapse_risk":
                    prediction.get(
                        "collapse_risk",
                    ),
                },
            )

    def ingest_context(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        before = len(
            self._entries,
        )

        self._add_extinction_entries(
            context,
        )
        self._add_rejected_fusion_entries(
            context,
        )
        self._add_failure_memory_entries(
            context,
        )
        self._add_lineage_entries(
            context,
        )
        self._add_identity_entries(
            context,
        )
        self._add_sandbox_entries(
            context,
        )

        return len(
            self._entries,
        ) - before

    def cognitive_paleontology_report(self, context=None) -> Dict[str, Any]:
        """Analyze why evolutionary artifacts died or became unsafe."""

        top_causes = self.analyze_causes(
            20,
        )

        toxic_lineages = self.find_toxic_lineages(
            threshold=2,
        )

        destructive_patterns = self.destructive_mutation_patterns(
            20,
        )

        collapse_patterns = self.collapse_patterns(
            20,
        )

        pressure = self.pressure_engine.compute(
            self.list_entries(),
            context,
        )

        risk_markers = []

        if toxic_lineages:

            risk_markers.append(
                "toxic_lineage_recurrence",
            )

        if destructive_patterns:

            risk_markers.append(
                "destructive_mutation_memory",
            )

        if collapse_patterns:

            risk_markers.append(
                "collapse_signature_detected",
            )

        return {
            "layer":
            "cognitive_paleontology",

            "death_causes":
            top_causes,

            "toxic_lineages":
            toxic_lineages,

            "destructive_mutation_patterns":
            destructive_patterns,

            "collapse_patterns":
            collapse_patterns,

            "graveyard_pressure":
            pressure,

            "risk_markers":
            risk_markers,

            "recommended_controls":
            [
                "quarantine_recurrent_toxic_lineages",
                "rehearse_repair_before_merge_retry",
                "lower_mutation_pressure_near_collapse_signatures",
            ]
            if risk_markers
            else [],

            "paleontology_state":
            (
                "active_evolutionary_debris_detected"
                if risk_markers
                else "graveyard_quiet"
            ),
        }

    def export_report(self) -> Dict[str, Any]:
        """Produce a small JSON-serializable report summarizing the graveyard."""
        with self._lock:
            return {
                "system": "evolutionary_graveyard",
                "manager": "evolutionary_graveyard_manager",
                "pressure_engine": "cognitive_graveyard_pressure_engine",
                "total_entries": len(self._entries),
                "by_category": dict(Counter(e.category for e in self._entries)),
                "top_causes": self.analyze_causes(20),
                "toxic_lineages": self.find_toxic_lineages(),
                "destructive_mutation_patterns": self.destructive_mutation_patterns(20),
                "collapse_patterns": self.collapse_patterns(20),
                "graveyard_pressure": self.pressure_engine.compute(
                    self._entries,
                ),
            }

    def run_cycle(self, context):

        new_entries = self.ingest_context(
            context,
        )

        report = self.export_report()

        report[
            "new_entries"
        ] = new_entries

        report[
            "recent_entries"
        ] = [
            entry.__dict__
            for entry in self.list_entries()[
                -20:
            ]
        ]

        report[
            "cognitive_paleontology"
        ] = self.cognitive_paleontology_report(
            context,
        )

        report[
            "graveyard_state"
        ] = (
            "active_debris_under_analysis"
            if report.get(
                "total_entries",
                0,
            )
            else "no_evolutionary_debris_recorded"
        )

        report[
            "timestamp"
        ] = datetime.utcnow().isoformat()

        self._history.append(
            report,
        )

        self._history = self._history[-128:]

        return report

    def save(self, path: str) -> None:
        """Persist the graveyard to disk as JSON."""
        with self._lock:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([e.__dict__ for e in self._entries], f, indent=2, ensure_ascii=False)

    def load(self, path: str) -> None:
        """Load a graveyard previously saved with `save`."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        with self._lock:
            self._entries = [GraveyardEntry(**d) for d in data]
            self._entry_keys = {
                self._entry_key(
                    entry.id,
                    entry.category,
                    entry.reason,
                )
                for entry in self._entries
            }


evolutionary_graveyard = EvolutionaryGraveyard()


__all__ = [
    "CognitiveGraveyardPressureEngine",
    "GraveyardEntry",
    "EvolutionaryGraveyard",
    "evolutionary_graveyard",
]
