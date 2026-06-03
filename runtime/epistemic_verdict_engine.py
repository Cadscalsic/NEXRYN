from core.epistemic_models import clamp


class EpistemicVerdictEngine:
    REGISTERABLE_VERDICTS = {
        "CANDIDATE",
        "PROBATION",
        "SUPPORTED",
        "QUARANTINED_PROBATION",
    }

    def _quality(self, concept, evidence):
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
                "evidence_count": 0,
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
            "evidence_count": len(items),
        }

    def _simulation_state(self, concept, evidence, hypothesis):
        for item in evidence:
            if (
                item.get("concept") == concept
                and item.get("metadata", {}).get("simulation_state")
            ):
                return item["metadata"]["simulation_state"]
        return hypothesis.get("metadata", {}).get(
            "simulation_state",
            "unobserved",
        )

    def _ambiguity_resolution(self, context, concept, evidence):
        simulation_ids = {
            item.get("metadata", {})
            .get("evidence_id", "")
            .split("mutation_rehearsal:", 1)[-1]
            for item in evidence
            if item.get("concept") == concept
        }
        resolutions = context.get(
            "ambiguity_resolution_report",
            {},
        ).get(
            "resolutions",
            [],
        )
        for item in resolutions:
            simulation_id = str(
                item.get(
                    "simulation_id",
                    "",
                )
            )
            if simulation_id in simulation_ids:
                return item
        return {}

    def evaluate(self, context, hypothesis, evidence, drift_assessment):
        concept = hypothesis["concept"]
        quality = self._quality(concept, evidence)
        simulation_state = self._simulation_state(
            concept,
            evidence,
            hypothesis,
        )
        containment = (
            drift_assessment.get("regulation_mode")
            == "semantic_containment"
        )
        ambiguity_resolution = self._ambiguity_resolution(
            context,
            concept,
            evidence,
        )
        resolved_path = ambiguity_resolution.get(
            "resolution",
            "UNRESOLVED_PATH",
        )
        observational_probation = (
            hypothesis.get(
                "metadata",
                {},
            ).get(
                "promotion_state",
            )
            == "OBSERVATIONAL_PROBATION"
        )

        if (
            simulation_state == "harmful"
            or resolved_path == "REJECTED_PATH"
            or quality["contradiction"] >= 0.55
        ):
            verdict = "REJECTED"
            reason = "contradictory_or_harmful_simulation"
        elif (
            containment
            and observational_probation
            and quality["evidence_count"] >= 2
            and quality["support"] >= 0.50
            and quality["contradiction"] <= 0.38
            and quality["semantic_consistency"] >= 0.64
        ):
            verdict = "QUARANTINED_PROBATION"
            reason = "observational_belief_quarantined_during_semantic_containment"
        elif (
            containment
            and (
                quality["support"] < 0.72
                or quality["semantic_consistency"] < 0.68
            )
        ):
            verdict = "SUPPRESSED"
            reason = "critical_semantic_drift_requires_stronger_evidence"
        elif (
            quality["evidence_count"] >= 2
            and quality["support"] >= 0.68
            and quality["contradiction"] <= 0.22
        ):
            verdict = "SUPPORTED"
            reason = "multi_source_evidence_supports_registration"
        elif (
            quality["evidence_count"] >= 1
            and quality["support"] >= 0.45
            and quality["contradiction"] <= 0.45
        ):
            verdict = "PROBATION"
            reason = "ambiguous_simulation_requires_epistemic_probation"
        else:
            verdict = "CANDIDATE"
            reason = "insufficient_evidence_retained_as_candidate"

        return {
            "concept": concept,
            "simulation_state": simulation_state,
            "ambiguity_resolution": resolved_path,
            "verdict": verdict,
            "reason": reason,
            "register_belief": verdict in self.REGISTERABLE_VERDICTS,
            "quality": quality,
        }

    def run_cycle(self, context, derived, drift_assessment):
        evidence = derived.get("epistemic_evidence", [])
        verdicts = [
            self.evaluate(
                context,
                hypothesis,
                evidence,
                drift_assessment,
            )
            for hypothesis in derived.get("epistemic_hypotheses", [])
        ]
        registerable = {
            verdict["concept"]
            for verdict in verdicts
            if verdict["register_belief"]
        }
        return {
            "system": "epistemic_verdict_engine",
            "verdicts": verdicts,
            "verdict_count": len(verdicts),
            "registered_candidate_count": len(registerable),
            "suppressed_count": sum(
                verdict["verdict"] == "SUPPRESSED"
                for verdict in verdicts
            ),
            "rejected_count": sum(
                verdict["verdict"] == "REJECTED"
                for verdict in verdicts
            ),
            "epistemic_hypotheses": [
                hypothesis
                for hypothesis in derived.get("epistemic_hypotheses", [])
                if hypothesis["concept"] in registerable
            ],
            "epistemic_evidence": [
                item
                for item in evidence
                if item.get("concept") in registerable
            ],
        }


epistemic_verdict_engine = EpistemicVerdictEngine()
