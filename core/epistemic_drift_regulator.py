from core.epistemic_models import BeliefState, clamp


def semantic_drift_score(context):
    context = context if isinstance(context, dict) else {}
    monitor = context.get("semantic_drift_monitor_report", {})
    if monitor:
        return clamp(
            monitor.get(
                "effective_drift",
                monitor.get(
                    "instantaneous_drift",
                    0.0,
                ),
            )
        )
    scores = [
        context.get("semantic_drift"),
        context.get("cognitive_homeostasis_report", {})
        .get("semantic_drift_detection", {})
        .get("semantic_drift"),
        context.get("stability_field_report", {})
        .get("semantic_drift", {})
        .get("semantic_drift"),
        context.get("identity_continuity_guardian_report", {})
        .get("state_transition", {})
        .get("current_state", {})
        .get("semantic_drift"),
        context.get("identity_continuity_engine_report", {})
        .get("fragmentation_guard", {})
        .get("semantic_drift"),
    ]
    values = [clamp(score) for score in scores if score is not None]
    return max(values, default=0.0)


def identity_continuity_score(context):
    context = context if isinstance(context, dict) else {}
    scores = [
        context.get("identity_continuity"),
        context.get("causal_rehearsal_report", {})
        .get("identity_forecaster", {})
        .get("identity_continuity"),
        context.get("identity_continuity_guardian_report", {})
        .get("state_transition", {})
        .get("current_state", {})
        .get("identity_continuity"),
        context.get("identity_continuity_engine_report", {})
        .get("identity_continuity"),
        context.get("identity_continuity_engine_report", {})
        .get("continuity_score"),
    ]
    values = [clamp(score) for score in scores if score is not None]
    return min(values, default=1.0)


class EpistemicDriftRegulator:
    def __init__(self):
        self.regulation_history = []

    def assess(self, context):
        drift = semantic_drift_score(context)
        continuity = identity_continuity_score(context)

        mode = (
            "semantic_containment"
            if drift >= 0.78 or continuity < 0.52
            else "restricted_belief_formation"
            if drift >= 0.58 or continuity < 0.62
            else "drift_watch"
            if drift >= 0.38 or continuity < 0.72
            else "normal_epistemic_growth"
        )
        limits = {
            "semantic_containment": (2, 0.72, 0.22, 0.68),
            "restricted_belief_formation": (4, 0.62, 0.32, 0.58),
            "drift_watch": (12, 0.48, 0.42, 0.48),
            "normal_epistemic_growth": (32, 0.0, 1.0, 0.0),
        }
        max_new, min_support, max_contradiction, min_consistency = limits[mode]
        return {
            "system": "epistemic_drift_regulator",
            "semantic_drift": drift,
            "identity_continuity": continuity,
            "regulation_mode": mode,
            "max_new_beliefs_per_cycle": max_new,
            "minimum_candidate_support": min_support,
            "maximum_candidate_contradiction": max_contradiction,
            "minimum_semantic_consistency": min_consistency,
            "truth_commit_blocked": mode == "semantic_containment",
            "weak_belief_archival_enabled": mode in [
                "semantic_containment",
                "restricted_belief_formation",
            ],
        }

    def _evidence_quality(self, concept, evidence):
        items = [
            item
            for item in evidence
            if item.get("concept") == concept
        ]
        if not items:
            return {
                "support": 0.0,
                "contradiction": 0.0,
                "semantic_consistency": 0.0,
            }

        return {
            "support": clamp(
                sum(item.get("support_score", 0.0) for item in items)
                / len(items)
            ),
            "contradiction": clamp(
                sum(item.get("contradiction_score", 0.0) for item in items)
                / len(items)
            ),
            "semantic_consistency": clamp(
                sum(item.get("semantic_consistency", 0.0) for item in items)
                / len(items)
            ),
        }

    def _quarantined_probation_allowed(self, item, assessment):
        metadata = item["hypothesis"].get(
            "metadata",
            {},
        )
        quality = item["quality"]
        return (
            assessment["regulation_mode"]
            == "semantic_containment"
            and metadata.get("promotion_state")
            == "OBSERVATIONAL_PROBATION"
            and quality["support"] >= 0.50
            and quality["contradiction"] <= 0.38
            and quality["semantic_consistency"] >= 0.64
        )

    def regulate(self, context, derived, belief_registry):
        assessment = self.assess(context)
        evidence = derived.get("epistemic_evidence", [])
        existing = belief_registry.registry
        candidates = []

        for hypothesis in derived.get("epistemic_hypotheses", []):
            concept = hypothesis["concept"]
            candidates.append({
                "hypothesis": hypothesis,
                "concept": concept,
                "quality": self._evidence_quality(concept, evidence),
                "existing": concept in existing,
            })

        for belief in belief_registry.beliefs():
            if belief.concept not in {
                item["concept"]
                for item in candidates
            } and belief.state == BeliefState.TRUTH_COMMITTED:
                candidates.append({
                    "hypothesis": {
                        "concept": belief.concept,
                        "claim": belief.claim,
                        "prior_confidence": belief.confidence,
                    },
                    "concept": belief.concept,
                    "quality": self._evidence_quality(belief.concept, evidence),
                    "existing": True,
                })

        admitted = []
        suppressed = []
        quarantined = []
        new_count = 0
        for item in sorted(
            candidates,
            key=lambda candidate: candidate["quality"]["support"],
            reverse=True,
        ):
            quality = item["quality"]
            quarantine_allowed = self._quarantined_probation_allowed(
                item,
                assessment,
            )
            accepted = item["existing"] or (
                new_count < assessment["max_new_beliefs_per_cycle"]
                and (
                    quarantine_allowed
                    or (
                        quality["support"]
                        >= assessment["minimum_candidate_support"]
                        and quality["contradiction"]
                        <= assessment["maximum_candidate_contradiction"]
                        and quality["semantic_consistency"]
                        >= assessment["minimum_semantic_consistency"]
                    )
                )
            )
            if accepted:
                admitted.append(item["hypothesis"])
                if quarantine_allowed:
                    quarantined.append(
                        item["concept"],
                    )
                if not item["existing"]:
                    new_count += 1
            else:
                suppressed.append({
                    "concept": item["concept"],
                    "reason": "semantic_drift_admission_gate",
                    "quality": quality,
                })

        admitted_concepts = {
            hypothesis["concept"]
            for hypothesis in admitted
        }
        regulated = {
            "epistemic_hypotheses": admitted,
            "epistemic_evidence": [
                item
                for item in evidence
                if item.get("concept") in admitted_concepts
            ],
        }
        assessment["admitted_hypothesis_count"] = len(admitted)
        assessment["suppressed_hypothesis_count"] = len(suppressed)
        assessment["suppressed_hypotheses"] = suppressed[:32]
        assessment["quarantined_probation_count"] = len(
            quarantined,
        )
        assessment["quarantined_probation_beliefs"] = quarantined
        self.regulation_history.append(assessment)
        self.regulation_history = self.regulation_history[-128:]
        return regulated, assessment

    def archive_weak_beliefs(self, belief_registry, assessment):
        if not assessment["weak_belief_archival_enabled"]:
            return []

        archived = []
        for belief in belief_registry.beliefs():
            if (
                belief.state in [BeliefState.CANDIDATE, BeliefState.PROBATION]
                and (
                    belief.confidence < 0.58
                    or belief.evidence_strength < 0.48
                )
            ):
                belief_registry.archive(belief.concept)
                archived.append(belief.concept)
        return archived
