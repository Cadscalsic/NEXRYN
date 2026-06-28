# ============================================
# NEXRYN EPISTEMIC CONSTITUTION
# OPTIMIZED / BOUNDED GOVERNANCE VERSION
# ============================================

import hashlib
import json
from datetime import datetime


def _clamp(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class EpistemicConstitution:

    def __init__(self):
        self.last_signature = None
        self.last_report = None
        self.cache_hits = 0
        self.cache_misses = 0
        self.history = []

    # ========================================
    # CACHE / SIGNATURE
    # ========================================

    def _stable_hash(self, payload):
        try:
            encoded = json.dumps(payload, sort_keys=True, default=str)
        except Exception:
            encoded = str(payload)

        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _signature(self, context):
        return self._stable_hash({
            "runtime_entropy": context.get("runtime_entropy", 0.0),
            "semantic_drift": context.get("semantic_drift", 0.0),
            "memory_pressure_score": context.get(
                "memory_pressure_score",
                context.get("working_memory_pressure", 0.0),
            ),
            "trust_band": context.get("trust_band"),
            "reputation_anchor_report": context.get(
                "reputation_anchor_report",
                {},
            ),
            "concept_reputation_engine_report": context.get(
                "concept_reputation_engine_report",
                {},
            ),
            "concept_admission_pipeline_report": context.get(
                "concept_admission_pipeline_report",
                {},
            ),
            "conceptive_neurogenesis_report": context.get(
                "conceptive_neurogenesis_report",
                {},
            ),
            "agent_count": context.get("agent_count"),
            "parallel_thread_count": context.get("parallel_thread_count"),
        })

    def _fast_mode(self, context):
        return (
            context.get("episode_completed") is True
            or context.get("shutdown_mode") == "fast"
            or context.get("post_success_mode") == "fast"
            or context.get("post_success_shutdown", {}).get("enabled") is True
        )

    def _critical_change_present(self, context):
        entropy = _clamp(context.get("runtime_entropy", 0.0))
        drift = _clamp(context.get("semantic_drift", 0.0))
        pressure = _clamp(
            context.get(
                "memory_pressure_score",
                context.get("working_memory_pressure", 0.0),
            )
        )

        return (
            entropy >= 0.82
            or drift >= 0.72
            or pressure >= 0.92
            or context.get("freeze_new_fusions") is True
            or context.get("sandbox_only_mode") is True
            or context.get("emergency_compression_active") is True
        )

    def _cache_report(self):
        total = self.cache_hits + self.cache_misses

        return {
            "system": "epistemic_constitution_cache",
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": (
                round(self.cache_hits / total, 4)
                if total
                else 0.0
            ),
            "history_size": len(self.history),
        }

    def _store_history(self, report):
        self.history.append({
            "constitutional_state": report.get("constitutional_state"),
            "executive_mode": report.get(
                "executive_cognitive_governance",
                {},
            ).get("executive_mode"),
            "cache_hit": report.get("epistemic_cache_hit", False),
            "timestamp": report.get("timestamp"),
        })

        self.history = self.history[-32:]

    def _reused_report(self, signature, reason):
        report = dict(self.last_report or {})
        report["epistemic_cache_hit"] = True
        report["epistemic_cache_state"] = reason
        report["cache_signature"] = signature
        report["timestamp"] = str(datetime.utcnow())
        report["epistemic_cache_report"] = self._cache_report()
        return report

    # ========================================
    # REPUTATION
    # ========================================

    def reputation(self, context):
        anchor = context.get("reputation_anchor_report", {})

        if anchor:
            return {
                "strength": _clamp(anchor.get("strength", 0.0)),
                "state": anchor.get("reputation_state", "unknown"),
                "source": anchor.get("anchor_source", "unknown"),
            }

        concept_reputation = context.get(
            "concept_reputation_engine_report",
            {},
        )

        return {
            "strength": _clamp(
                concept_reputation.get(
                    "average_concept_reputation",
                    0.0,
                )
            ),
            "state": concept_reputation.get(
                "reputation_state",
                "unknown",
            ),
            "source": "concept_reputation_engine",
        }

    # ========================================
    # EPISTEMIC JUDICIARY
    # ========================================

    def epistemic_judiciary(self, context):
        reputation = self.reputation(context)

        admission = context.get(
            "concept_admission_pipeline_report",
            {},
        )

        evaluations = admission.get("evaluations", [])
        if not isinstance(evaluations, list):
            evaluations = []

        legitimacy_scores = [
            item.get("legitimacy_testing", {}).get(
                "legitimacy_score",
                0.0,
            )
            for item in evaluations
            if isinstance(item, dict)
        ]

        average_legitimacy = _clamp(
            sum(legitimacy_scores) / max(len(legitimacy_scores), 1)
        )

        anchor = context.get("reputation_anchor_report", {})

        contradiction_load = _clamp(
            anchor.get("contradiction_load", 0.0)
        )

        failure_propagation = _clamp(
            anchor.get("failure_propagation_score", 0.0)
        )

        truth_score = _clamp(
            average_legitimacy * 0.42
            + reputation["strength"] * 0.40
            + (1.0 - contradiction_load) * 0.10
            + (1.0 - failure_propagation) * 0.08
        )

        stability_score = _clamp(
            1.0
            - _clamp(context.get("runtime_entropy", 0.0)) * 0.45
            - _clamp(context.get("semantic_drift", 0.0)) * 0.35
        )

        generated_count = (
            context.get("conceptive_neurogenesis_report", {})
            .get("generated_count", 0)
        )

        try:
            generated_count = max(0, int(generated_count or 0))
        except Exception:
            generated_count = 0

        spread_score = _clamp(generated_count / 24)

        parasitic_risk = _clamp(
            spread_score * 0.35
            + failure_propagation * 0.35
            + contradiction_load * 0.30
        )

        decision = (
            "epistemically_legitimate"
            if truth_score >= 0.68 and parasitic_risk < 0.35
            else "requires_epistemic_trial"
            if truth_score >= 0.42
            else "epistemically_untrusted"
        )

        return {
            "system": "epistemic_legitimacy_engine",
            "judiciary_scope": [
                "truth",
                "stability",
                "spread",
                "power",
                "imitation",
                "parasitism",
            ],
            "truth_score": truth_score,
            "stability_score": stability_score,
            "spread_score": spread_score,
            "parasitic_risk": parasitic_risk,
            "reputation_strength": reputation["strength"],
            "reputation_state": reputation["state"],
            "decision": decision,
            "survival_is_not_truth": True,
        }

    # ========================================
    # ONTOLOGICAL GROWTH
    # ========================================

    def ontological_growth_constitution(self, context, judiciary):
        admission = context.get(
            "concept_admission_pipeline_report",
            {},
        )

        decision_counts = admission.get("decision_counts", {})
        if not isinstance(decision_counts, dict):
            decision_counts = {}

        staged = decision_counts.get("staged_rehearsal", 0)
        reputation_required = decision_counts.get(
            "historical_reputation_required",
            0,
        )

        try:
            staged = max(0, int(staged or 0))
        except Exception:
            staged = 0

        try:
            reputation_required = max(
                0,
                int(reputation_required or 0),
            )
        except Exception:
            reputation_required = 0

        entropy = _clamp(context.get("runtime_entropy", 0.0))
        drift = _clamp(context.get("semantic_drift", 0.0))

        growth_pressure = _clamp(
            min(staged * 0.05, 0.25)
            + min(reputation_required * 0.06, 0.30)
            + entropy * 0.35
            + drift * 0.35
        )

        causal_value = _clamp(judiciary.get("truth_score", 0.0))

        policy = (
            "freeze_ontology_growth"
            if growth_pressure >= 0.76
            else "quarantine_new_concepts"
            if growth_pressure >= 0.52
            else "allow_costed_birth"
        )

        return {
            "system": "ontological_growth_constitution",
            "laws": [
                "concept_birth_requires_epistemic_value",
                "growth_pays_entropy_cost",
                "causal_value_must_exceed_fragmentation_risk",
                "bridge_hypotheses_are_not_concepts",
                "reputation_precedes_core_integration",
            ],
            "growth_pressure": growth_pressure,
            "causal_value": causal_value,
            "concept_birth_policy": policy,
            "freeze_new_fusions": policy == "freeze_ontology_growth",
        }

    # ========================================
    # VALUE HIERARCHY
    # ========================================

    def value_hierarchy(self, context, judiciary, ontology):
        truth = 0.30
        coherence = 0.20
        stability = 0.16
        survival = 0.14
        adaptability = 0.10
        exploration = 0.06
        autonomy = 0.04

        if judiciary.get("decision") != "epistemically_legitimate":
            truth += 0.08
            exploration -= 0.03
            autonomy -= 0.02
            stability += 0.02

        if ontology.get("concept_birth_policy") == "freeze_ontology_growth":
            stability += 0.06
            exploration -= 0.04
            adaptability -= 0.02

        values = {
            "truth": _clamp(truth),
            "coherence": _clamp(coherence),
            "stability": _clamp(stability),
            "survival": _clamp(survival),
            "adaptability": _clamp(adaptability),
            "exploration": _clamp(exploration),
            "autonomy": _clamp(autonomy),
        }

        return {
            "system": "value_hierarchy_system",
            "values": values,
            "ordering": [
                key
                for key, value in sorted(
                    values.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            ],
            "anti_collapse_rule":
            "truth_over_survival_when_survival_lacks_legitimacy",
        }

    # ========================================
    # RESOURCE ALLOCATION
    # ========================================

    def resource_allocation(self, context, values, ontology):
        entropy = _clamp(context.get("runtime_entropy", 0.0))
        pressure = _clamp(
            context.get(
                "memory_pressure_score",
                context.get("working_memory_pressure", 0.0),
            )
        )

        allocations = {
            "attention_to_truth_validation": _clamp(
                values.get("truth", 0.0) + entropy * 0.12
            ),
            "reasoning_to_causal_tests": _clamp(
                values.get("coherence", 0.0)
                + values.get("truth", 0.0) * 0.35
            ),
            "energy_to_stabilization": _clamp(
                values.get("stability", 0.0)
                + pressure * 0.18
            ),
            "budget_to_exploration": _clamp(
                values.get("exploration", 0.0)
                * (
                    0.35
                    if ontology.get("freeze_new_fusions", False)
                    else 1.0
                )
            ),
        }

        return {
            "system": "resource_allocation_intelligence",
            "attention_economy": allocations,
            "resource_policy": (
                "truth_and_stability_first"
                if entropy >= 0.62 or pressure >= 0.62
                else "balanced_epistemic_growth"
            ),
        }

    # ========================================
    # ETHICS
    # ========================================

    def civilizational_ethics(self, judiciary, ontology, values):
        return {
            "system": "civilizational_ethics_layer",
            "rights_and_limits": {
                "delete_concepts":
                "allowed_only_after_reputation_failure_and_gc_review",
                "suppress_traits":
                "allowed_when_failure_propagation_exceeds_causal_value",
                "permit_extinction":
                "only_for_parasitic_or_contradictory_lineages",
                "identity_sacrifice":
                "forbidden_without_supervised_rewrite_and_rollback",
                "innovation_vs_stability": (
                    "stability_precedes_innovation"
                    if ontology.get("freeze_new_fusions", False)
                    else "innovation_allowed_under_epistemic_trial"
                ),
            },
            "ethical_priority": (
                "prevent_false_survival"
                if judiciary.get("decision") != "epistemically_legitimate"
                else "permit_responsible_growth"
            ),
            "highest_value": (
                max(values, key=values.get)
                if values
                else "truth"
            ),
        }

    # ========================================
    # DISTRIBUTED CONSTITUTION
    # ========================================

    def distributed_constitution(self, context, judiciary):
        try:
            agent_count = int(
                context.get(
                    "agent_count",
                    context.get("parallel_thread_count", 1),
                )
                or 1
            )
        except Exception:
            agent_count = 1

        agent_count = max(1, agent_count)

        return {
            "system": "distributed_constitutional_cognition",
            "federation_policy": (
                "single_agent_constitutional_mode"
                if agent_count <= 1
                else "federated_agents_require_shared_epistemic_court"
            ),
            "agent_count": agent_count,
            "shared_requirements": [
                "shared_value_hierarchy",
                "local_sandbox_write_barriers",
                "cross_agent_reputation_ledger",
                "no_agent_can_commit_false_survival",
            ],
            "commit_policy": (
                "federated_commit_blocked_until_legitimate"
                if judiciary.get("decision") != "epistemically_legitimate"
                else "federated_commit_allowed_with_audit"
            ),
        }

    # ========================================
    # EXECUTIVE GOVERNANCE
    # ========================================

    def executive_governance(
        self,
        judiciary,
        ontology,
        values,
        resources,
        ethics,
        distributed,
    ):
        if judiciary.get("decision") == "epistemically_untrusted":
            mode = "epistemic_quarantine"
            action = "block_core_commit_and_start_truth_trial"

        elif ontology.get("freeze_new_fusions", False):
            mode = "ontological_stabilization"
            action = "freeze_growth_and_reallocate_to_reputation"

        else:
            mode = "constitutional_growth"
            action = "allow_costed_growth_under_judiciary"

        return {
            "system": "executive_cognitive_governance",
            "executive_mode": mode,
            "selected_action": action,
            "conflict_resolution": {
                "truth_vs_survival":
                "truth_precedes_survival_claims",
                "stability_vs_exploration": (
                    "stability_wins_temporarily"
                    if resources.get("resource_policy")
                    == "truth_and_stability_first"
                    else "exploration_allowed_with_budget"
                ),
                "autonomy_vs_constitution":
                "constitution_precedes_unverified_autonomy",
            },
            "sacrifice_policy": ethics.get("rights_and_limits", {}),
            "distributed_commit_policy": distributed.get("commit_policy"),
        }

    # ========================================
    # MAIN CYCLE
    # ========================================

    def run_cycle(self, context):
        if not isinstance(context, dict):
            context = {}

        signature = self._signature(context)
        fast_mode = self._fast_mode(context)
        critical_change = self._critical_change_present(context)

        if (
            self.last_signature == signature
            and self.last_report is not None
            and not critical_change
        ):
            self.cache_hits += 1
            report = self._reused_report(
                signature,
                "exact_signature_reuse",
            )
            self._store_history(report)
            return report

        if (
            fast_mode
            and self.last_report is not None
            and not critical_change
        ):
            self.cache_hits += 1
            report = self._reused_report(
                signature,
                "fast_mode_reuse_previous_epistemic_constitution",
            )
            self._store_history(report)
            return report

        self.cache_misses += 1

        judiciary = self.epistemic_judiciary(context)

        ontology = self.ontological_growth_constitution(
            context,
            judiciary,
        )

        values = self.value_hierarchy(
            context,
            judiciary,
            ontology,
        )

        value_map = values.get("values", {})

        resources = self.resource_allocation(
            context,
            value_map,
            ontology,
        )

        ethics = self.civilizational_ethics(
            judiciary,
            ontology,
            value_map,
        )

        distributed = self.distributed_constitution(
            context,
            judiciary,
        )

        executive = self.executive_governance(
            judiciary,
            ontology,
            value_map,
            resources,
            ethics,
            distributed,
        )

        constitutional_state = (
            "epistemic_trial_required"
            if judiciary.get("decision") != "epistemically_legitimate"
            else "constitutional_cognition_stable"
        )

        report = {
            "system": "epistemic_constitution",
            "epistemic_legitimacy_engine": judiciary,
            "ontological_growth_constitution": ontology,
            "value_hierarchy_system": values,
            "resource_allocation_intelligence": resources,
            "civilizational_ethics_layer": ethics,
            "distributed_constitutional_cognition": distributed,
            "executive_cognitive_governance": executive,
            "constitutional_state": constitutional_state,
            "epistemic_cache_hit": False,
            "epistemic_cache_state": "computed",
            "epistemic_cache_report": self._cache_report(),
            "cache_signature": signature,
            "timestamp": str(datetime.utcnow()),
        }

        self.last_signature = signature
        self.last_report = dict(report)

        self._store_history(report)

        return report