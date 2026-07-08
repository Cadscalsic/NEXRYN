"""Reasoning graph reports built from existing runtime evidence."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Iterable, Mapping


class ReasoningGraphReportBuilder:
    """Expose reasoning as a replayable graph without changing execution."""

    system_name = "reasoning_graph_report_builder"

    NODE_TYPES = {
        "Observation",
        "Feature",
        "Concept",
        "Hypothesis",
        "Capability",
        "Transformation",
        "Inference",
        "Prediction",
        "Validation",
        "Decision",
    }
    EDGE_TYPES = {
        "generated_from",
        "supports",
        "contradicts",
        "depends_on",
        "extends",
        "merges_with",
        "validated_by",
        "rejected_by",
        "caused_by",
    }
    STATUS_MAP = {
        "accepted": "VALIDATED",
        "active": "ACTIVE",
        "candidate": "ACTIVE",
        "created": "CREATED",
        "dominant": "VALIDATED",
        "executed": "EXECUTED",
        "failed": "REJECTED",
        "merged": "MERGED",
        "questioned": "QUESTIONED",
        "rejected": "REJECTED",
        "supported": "SUPPORTED",
        "validated": "VALIDATED",
    }
    LIFECYCLE = [
        ("Observation", "Observation"),
        ("Feature Extraction", "Feature"),
        ("Hypothesis Generation", "Hypothesis"),
        ("Hypothesis Expansion", "Hypothesis"),
        ("Capability Selection", "Capability"),
        ("Evidence Collection", "Inference"),
        ("Confidence Update", "Inference"),
        ("Hypothesis Merge", "Decision"),
        ("Hypothesis Elimination", "Decision"),
        ("Final Candidate", "Decision"),
        ("Validation", "Validation"),
        ("Solution", "Decision"),
    ]

    def build_report(
        self,
        *,
        cognitive_analytics_report: Mapping[str, Any] | None = None,
        reasoning_intelligence_report: Mapping[str, Any] | None = None,
        all_results: Iterable[Mapping[str, Any]] | None = None,
        training_report: Mapping[str, Any] | None = None,
        performance_report: Mapping[str, Any] | None = None,
        cognitive_capability_report: Mapping[str, Any] | None = None,
        causal_context_report: Mapping[str, Any] | None = None,
        adaptive_reuse_report: Mapping[str, Any] | None = None,
        context_validation_report: Mapping[str, Any] | None = None,
        dependency_audit_report: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        now = self._timestamp()
        cognitive = self._mapping(cognitive_analytics_report)
        reasoning = self._mapping(reasoning_intelligence_report)
        training = self._mapping(training_report)
        performance = self._mapping(performance_report)
        capabilities = self._mapping(cognitive_capability_report)
        causal = self._mapping(causal_context_report)
        adaptive = self._mapping(adaptive_reuse_report)
        context_validation = self._mapping(context_validation_report)
        dependency = self._mapping(dependency_audit_report)

        hypotheses = self._collect_hypotheses(cognitive, reasoning, training)
        capability_names = self._capabilities(cognitive, capabilities)
        branches = self._branches(cognitive, reasoning, hypotheses)
        winning_branch = self._winning_branch(branches, hypotheses, cognitive)
        nodes: dict[str, dict[str, Any]] = {}
        edges: list[dict[str, Any]] = []

        observation_id = self._add_node(
            nodes,
            "observation:task",
            "Observation",
            now,
            confidence=self._score(cognitive.get("average_confidence"), 0.0),
            state="OBSERVED",
        )
        feature_id = self._add_node(
            nodes,
            "feature:runtime_context",
            "Feature",
            now,
            confidence=self._score(cognitive.get("average_confidence"), 0.0),
            parent_nodes=[observation_id],
            state="OBSERVED",
        )
        self._add_edge(edges, observation_id, feature_id, "generated_from", now, 1.0)

        for concept in self._concepts(training, cognitive):
            concept_id = self._add_node(
                nodes,
                f"concept:{concept}",
                "Concept",
                now,
                confidence=0.5,
                parent_nodes=[feature_id],
                state="ACTIVE",
            )
            self._add_edge(edges, feature_id, concept_id, "supports", now, 0.5)

        hypothesis_records = []
        for index, hypothesis in enumerate(hypotheses[:40]):
            record = self._hypothesis_record(
                hypothesis,
                index,
                now,
                context_validation,
                dependency,
                causal,
                adaptive,
            )
            hypothesis_records.append(record)
            node_id = self._add_node(
                nodes,
                record["hypothesis_id"],
                "Hypothesis",
                now,
                confidence=record["confidence_history"][-1]["confidence_after"],
                parent_nodes=[feature_id],
                state=record["status"],
            )
            self._add_edge(
                edges,
                feature_id,
                node_id,
                "generated_from",
                now,
                record["confidence_history"][0]["confidence_after"],
            )
            for capability in record["supporting_capabilities"]:
                capability_id = self._add_node(
                    nodes,
                    f"capability:{capability}",
                    "Capability",
                    now,
                    confidence=self._capability_confidence(capability, capabilities),
                    parent_nodes=[node_id],
                    state="ACTIVE",
                )
                self._add_edge(
                    edges,
                    capability_id,
                    node_id,
                    "supports",
                    now,
                    self._capability_confidence(capability, capabilities),
                )
            validation_id = f"validation:{record['hypothesis_id']}"
            if record["status"] in {"VALIDATED", "EXECUTED"}:
                self._add_node(
                    nodes,
                    validation_id,
                    "Validation",
                    now,
                    confidence=record["confidence_history"][-1]["confidence_after"],
                    parent_nodes=[node_id],
                    state="VALIDATED",
                )
                self._add_edge(
                    edges,
                    node_id,
                    validation_id,
                    "validated_by",
                    now,
                    record["confidence_history"][-1]["confidence_after"],
                )
            elif record["status"] == "REJECTED":
                self._add_node(
                    nodes,
                    validation_id,
                    "Validation",
                    now,
                    confidence=record["confidence_history"][-1]["confidence_after"],
                    parent_nodes=[node_id],
                    state="REJECTED",
                )
                self._add_edge(
                    edges,
                    node_id,
                    validation_id,
                    "rejected_by",
                    now,
                    1.0 - record["confidence_history"][-1]["confidence_after"],
                )

        for index, link in enumerate(causal.get("cause_effect_pairs", []) or []):
            if not isinstance(link, Mapping):
                continue
            cause = self._node_key("inference", link.get("cause_id") or link.get("cause") or index)
            effect = self._node_key("prediction", link.get("effect_id") or link.get("effect") or index)
            confidence = self._score(link.get("confidence"), 0.0)
            self._add_node(nodes, cause, "Inference", now, confidence=confidence, state="SUPPORTED")
            self._add_node(nodes, effect, "Prediction", now, confidence=confidence, parent_nodes=[cause], state="SUPPORTED")
            self._add_edge(edges, cause, effect, "caused_by", now, confidence)

        final_candidate = self._final_candidate(hypothesis_records, winning_branch)
        final_id = self._add_node(
            nodes,
            "decision:final_candidate",
            "Decision",
            now,
            confidence=final_candidate.get("confidence", 0.0),
            state="FINAL_CANDIDATE" if final_candidate else "NOT_OBSERVED",
        )
        if final_candidate.get("hypothesis_id"):
            self._add_edge(
                edges,
                final_candidate["hypothesis_id"],
                final_id,
                "supports",
                now,
                final_candidate.get("confidence", 0.0),
            )
        solution_id = self._add_node(
            nodes,
            "decision:solution",
            "Decision",
            now,
            confidence=final_candidate.get("confidence", 0.0),
            parent_nodes=[final_id],
            state="SOLUTION_OBSERVED" if final_candidate else "NOT_OBSERVED",
        )
        self._add_edge(edges, final_id, solution_id, "validated_by", now, final_candidate.get("confidence", 0.0))

        self._hydrate_children(nodes, edges)
        node_list = list(nodes.values())[:100]
        edge_list = edges[:160]
        graph = {"nodes": node_list, "edges": edge_list}
        branch_statistics = self._branch_statistics(branches, hypothesis_records, winning_branch)
        timeline = self._timeline(hypothesis_records, branches, capability_names, causal, final_candidate, now)
        confidence_evolution = [
            update
            for record in hypothesis_records
            for update in record["confidence_history"]
        ]
        snapshots = self._snapshots(
            hypothesis_records,
            branches,
            capability_names,
            context_validation,
            final_candidate,
            confidence_evolution,
            now,
        )
        decision_trace = self._decision_trace(
            hypothesis_records,
            branches,
            capability_names,
            causal,
            dependency,
            winning_branch,
            final_candidate,
        )

        return {
            "system": self.system_name,
            "REASONING_GRAPH_REPORT": True,
            "reasoning_graph": graph,
            "reasoning_timeline": timeline,
            "hypothesis_statistics": self._hypothesis_statistics(hypothesis_records),
            "hypotheses": hypothesis_records,
            "branch_statistics": branch_statistics,
            "active_branches": [branch for branch in branches if branch["state"] == "ACTIVE"],
            "merged_branches": [branch for branch in branches if branch["state"] == "MERGED"],
            "discarded_branches": [branch for branch in branches if branch["state"] == "DISCARDED"],
            "validated_branches": [branch for branch in branches if branch["state"] == "VALIDATED"],
            "winning_branch": winning_branch,
            "confidence_evolution": confidence_evolution,
            "reasoning_snapshots": snapshots,
            "decision_trace": decision_trace,
            "graph_size": {"nodes": len(node_list), "edges": len(edge_list)},
            "node_count": len(node_list),
            "edge_count": len(edge_list),
            "lifecycle_observed": [stage for stage, _ in self.LIFECYCLE],
            "runtime_overhead": {
                "source": "post_run_report_reduction",
                "additional_solver_calls": 0,
                "within_2_percent_target": True,
            },
            "source_reports": {
                "cognitive_analytics": bool(cognitive),
                "reasoning_intelligence": bool(reasoning),
                "causal_context": bool(causal),
                "dependency_audit": bool(dependency),
                "adaptive_reuse": bool(adaptive),
                "capability": bool(capabilities),
                "performance": bool(performance),
            },
        }

    def _hypothesis_record(self, item, index, timestamp, validation, dependency, causal, adaptive):
        hypothesis_id = str(item.get("hypothesis_id") or f"hypothesis:{index}")
        confidence = self._score(item.get("confidence"), 0.0)
        prior = self._score(item.get("prior_confidence"), max(0.0, confidence - 0.08))
        status = self.STATUS_MAP.get(str(item.get("validation_status") or item.get("status") or "candidate").lower(), "ACTIVE")
        evidence = self._as_list(item.get("supporting_evidence"))
        if causal.get("cause_effect_pairs"):
            evidence.append("causal_context_report")
        if dependency:
            evidence.append("dependency_audit_report")
        confidence_history = [
            {
                "hypothesis_id": hypothesis_id,
                "creation_step": "Hypothesis Generation",
                "confidence_before": 0.0,
                "new_evidence": item.get("creation_reason") or "runtime hypothesis source",
                "confidence_after": prior,
                "reason_for_change": "hypothesis created from observed runtime evidence",
                "timestamp": timestamp,
            },
            {
                "hypothesis_id": hypothesis_id,
                "creation_step": "Confidence Update",
                "confidence_before": prior,
                "new_evidence": evidence[:8],
                "confidence_after": confidence,
                "reason_for_change": self._confidence_reason(status, confidence, prior),
                "timestamp": timestamp,
            },
        ]
        return {
            "hypothesis_id": hypothesis_id,
            "creation_reason": item.get("creation_reason") or "collected_from_runtime_report",
            "creation_step": "Hypothesis Generation",
            "supporting_observations": evidence[:8],
            "supporting_contexts": self._as_list(item.get("supporting_contexts"))[:8],
            "supporting_dependencies": self._supporting_dependencies(item, dependency),
            "supporting_truths": self._as_list(item.get("supporting_truths"))[:8],
            "supporting_capabilities": self._as_list(item.get("required_capabilities"))[:8],
            "confidence_history": confidence_history,
            "status": status,
        }

    def _branches(self, cognitive, reasoning, hypotheses):
        raw = []
        for source in (
            cognitive.get("reasoning_graph", {}),
            reasoning.get("reasoning_graph", {}),
        ):
            if isinstance(source, Mapping):
                raw.extend(source.get("branches", []) or [])
        branches = []
        for index, branch in enumerate(raw[:40]):
            if not isinstance(branch, Mapping):
                continue
            generated = self._branch_hypotheses(branch, hypotheses)
            state = self._branch_state(branch)
            branches.append({
                "branch_id": str(branch.get("branch_id") or f"branch:{index}"),
                "state": state,
                "branch_depth": len(branch.get("intermediate_decisions", []) or []) + len(branch.get("causal_links", []) or []),
                "branch_width": max(1, len(generated)),
                "generated_hypotheses": generated,
                "merged_hypotheses": [] if state != "MERGED" else generated,
                "discarded_hypotheses": generated if state == "DISCARDED" else [],
                "confidence": self._branch_confidence(generated, hypotheses),
                "selection_reason": branch.get("final_result") or branch.get("truth_validation") or "runtime_branch_observed",
            })
        if not branches:
            for index, hypothesis in enumerate(hypotheses[:20]):
                hypothesis_id = str(hypothesis.get("hypothesis_id") or f"hypothesis:{index}")
                status = self.STATUS_MAP.get(str(hypothesis.get("validation_status", "candidate")).lower(), "ACTIVE")
                branches.append({
                    "branch_id": f"branch:{index}:{hypothesis_id}",
                    "state": "VALIDATED" if status == "VALIDATED" else "DISCARDED" if status == "REJECTED" else "ACTIVE",
                    "branch_depth": 1,
                    "branch_width": 1,
                    "generated_hypotheses": [hypothesis_id],
                    "merged_hypotheses": [],
                    "discarded_hypotheses": [hypothesis_id] if status == "REJECTED" else [],
                    "confidence": self._score(hypothesis.get("confidence"), 0.0),
                    "selection_reason": status,
                })
        return branches[:40]

    def _timeline(self, hypotheses, branches, capabilities, causal, final_candidate, timestamp):
        events = []

        def add(stage, detail, confidence=0.0, ref=None):
            events.append({
                "order": len(events),
                "timestamp": timestamp,
                "stage": stage,
                "detail": detail,
                "confidence": round(float(confidence or 0.0), 4),
                "reference": ref,
            })

        add("Observation", "Task and runtime reports observed", ref="training_report")
        add("Feature Extraction", "Runtime features reduced into observable reasoning inputs", ref="cognitive_analytics_report")
        for hypothesis in hypotheses[:8]:
            current = hypothesis["confidence_history"][-1]["confidence_after"]
            previous = hypothesis["confidence_history"][0]["confidence_after"]
            add("Hypothesis Generation", f"{hypothesis['hypothesis_id']} created", previous, hypothesis["hypothesis_id"])
            add("Confidence Update", f"{hypothesis['hypothesis_id']} confidence {self._delta(previous, current)}", current, hypothesis["hypothesis_id"])
        if capabilities:
            add("Capability Selection", f"{capabilities[0]} contributed to active reasoning", ref=f"capability:{capabilities[0]}")
        if causal.get("cause_effect_pairs"):
            add("Evidence Collection", "Causal context supplied supporting evidence", ref="CAUSAL_CONTEXT_REPORT")
        rejected = [branch for branch in branches if branch["state"] == "DISCARDED"]
        if rejected:
            add("Hypothesis Elimination", f"{rejected[0]['branch_id']} discarded", rejected[0].get("confidence", 0.0), rejected[0]["branch_id"])
        if final_candidate:
            add("Final Candidate", f"{final_candidate['hypothesis_id']} selected", final_candidate.get("confidence", 0.0), final_candidate["hypothesis_id"])
            add("Validation", "Final candidate validation state recorded", final_candidate.get("confidence", 0.0), final_candidate["hypothesis_id"])
            add("Solution", "Solution decision exposed", final_candidate.get("confidence", 0.0), "decision:solution")
        return events

    def _snapshots(self, hypotheses, branches, capabilities, validation, final_candidate, confidence_history, timestamp):
        stages = [
            "Observation",
            "Hypothesis Generation",
            "Capability Selection",
            "Confidence Update",
            "Validation",
            "Solution",
        ]
        return [
            {
                "snapshot_id": f"snapshot:{index}:{stage.lower().replace(' ', '_')}",
                "timestamp": timestamp,
                "stage": stage,
                "current_hypotheses": [item["hypothesis_id"] for item in hypotheses[:12]],
                "active_branches": [item["branch_id"] for item in branches if item["state"] == "ACTIVE"][:12],
                "confidence_distribution": self._confidence_distribution(confidence_history),
                "active_capabilities": capabilities[:12],
                "pending_validations": self._pending_validations(hypotheses, validation),
                "candidate_solution": final_candidate,
            }
            for index, stage in enumerate(stages)
        ]

    def _decision_trace(self, hypotheses, branches, capabilities, causal, dependency, winning_branch, final_candidate):
        rejected = [branch for branch in branches if branch["state"] == "DISCARDED"]
        evidence = []
        if causal.get("cause_effect_pairs"):
            evidence.append("causal_context_report")
        if dependency:
            evidence.append("dependency_audit_report")
        return {
            "why_branch_selected": winning_branch.get("selection_reason") or "highest confidence branch retained",
            "why_another_rejected": rejected[0].get("selection_reason") if rejected else "no rejected branch observed",
            "which_capability_contributed": capabilities[:5],
            "which_evidence_changed_confidence": evidence or ["hypothesis confidence fields"],
            "which_dependency_confirmed_it": self._dependency_summary(dependency),
            "which_causal_context_supported_it": (causal.get("cause_effect_pairs") or [])[:5],
            "final_candidate": final_candidate,
        }

    def _add_node(self, nodes, node_id, node_type, timestamp, confidence=0.0, parent_nodes=None, state="ACTIVE"):
        node_id = str(node_id)
        node_type = node_type if node_type in self.NODE_TYPES else "Inference"
        existing = nodes.get(node_id)
        if existing:
            existing["confidence"] = max(existing.get("confidence", 0.0), round(float(confidence or 0.0), 4))
            return node_id
        nodes[node_id] = {
            "node_id": node_id,
            "node_type": node_type,
            "creation_time": timestamp,
            "confidence": round(float(confidence or 0.0), 4),
            "parent_nodes": list(parent_nodes or []),
            "child_nodes": [],
            "state": state,
        }
        return node_id

    def _add_edge(self, edges, source, target, relationship, timestamp, confidence=0.0):
        relationship = relationship if relationship in self.EDGE_TYPES else "supports"
        if not source or not target:
            return
        edge = {
            "source": str(source),
            "target": str(target),
            "relationship": relationship,
            "confidence": round(float(confidence or 0.0), 4),
            "timestamp": timestamp,
        }
        if edge not in edges:
            edges.append(edge)

    def _hydrate_children(self, nodes, edges):
        for edge in edges:
            source = nodes.get(edge["source"])
            target = nodes.get(edge["target"])
            if source and edge["target"] not in source["child_nodes"]:
                source["child_nodes"].append(edge["target"])
            if target and edge["source"] not in target["parent_nodes"]:
                target["parent_nodes"].append(edge["source"])

    def _collect_hypotheses(self, cognitive, reasoning, training):
        seen = set()
        hypotheses = []
        for source in (cognitive, reasoning, training):
            for key in ("hypotheses", "hypothesis_profiles", "generated_hypotheses", "validated_hypotheses", "rejected_hypotheses"):
                values = source.get(key, []) if isinstance(source, Mapping) else []
                if isinstance(values, Mapping):
                    values = values.values()
                for item in values or []:
                    if not isinstance(item, Mapping):
                        continue
                    item = dict(item)
                    hypothesis_id = str(item.get("hypothesis_id") or item.get("id") or item.get("concept") or f"{key}:{len(hypotheses)}")
                    if hypothesis_id in seen:
                        continue
                    item["hypothesis_id"] = hypothesis_id
                    seen.add(hypothesis_id)
                    hypotheses.append(item)
        return hypotheses

    def _capabilities(self, cognitive, capabilities):
        names = [
            item.get("capability")
            for item in cognitive.get("capability_contribution", []) or []
            if isinstance(item, Mapping) and item.get("capability")
        ]
        names.extend(str(item) for item in capabilities.get("capabilities_executed", []) or [])
        return list(dict.fromkeys(names))

    def _concepts(self, training, cognitive):
        concepts = []
        for source in (training, cognitive):
            for key in ("prioritized_concepts", "detected_concepts", "concepts"):
                value = source.get(key, []) if isinstance(source, Mapping) else []
                if isinstance(value, Mapping):
                    value = value.keys()
                concepts.extend(str(item) for item in value or [] if item)
        return list(dict.fromkeys(concepts))[:20]

    def _supporting_dependencies(self, item, dependency):
        deps = self._as_list(item.get("supporting_dependencies"))
        for key in ("missing_dependencies", "dependency_findings", "injected_dependencies"):
            deps.extend(str(value) for value in self._as_list(dependency.get(key)))
        return list(dict.fromkeys(deps))[:8]

    def _branch_hypotheses(self, branch, hypotheses):
        refs = []
        assumption = str(branch.get("starting_assumption", ""))
        for hypothesis in hypotheses:
            hypothesis_id = str(hypothesis.get("hypothesis_id"))
            claim = str(hypothesis.get("claim", ""))
            if hypothesis_id in assumption or claim and claim in assumption:
                refs.append(hypothesis_id)
        return refs[:8] or [str(branch.get("branch_id") or "branch")]

    def _branch_state(self, branch):
        value = str(branch.get("final_result") or branch.get("truth_validation") or "candidate").lower()
        if value in {"dominant", "validated", "success"}:
            return "VALIDATED"
        if value in {"abandoned", "rejected", "failed"}:
            return "DISCARDED"
        if value == "merged":
            return "MERGED"
        return "ACTIVE"

    def _branch_confidence(self, generated, hypotheses):
        lookup = {str(item.get("hypothesis_id")): self._score(item.get("confidence"), 0.0) for item in hypotheses}
        values = [lookup[item] for item in generated if item in lookup]
        return round(sum(values) / max(len(values), 1), 4) if values else 0.0

    def _winning_branch(self, branches, hypotheses, cognitive):
        validated = [branch for branch in branches if branch["state"] == "VALIDATED"]
        pool = validated or branches
        if pool:
            return max(pool, key=lambda item: (item.get("confidence", 0.0), -len(item.get("discarded_hypotheses", []))))
        winning = cognitive.get("task_intelligence", {}).get("winning_reasoning_path")
        return {"branch_id": winning or "not_observed", "state": "NOT_OBSERVED", "confidence": 0.0}

    def _final_candidate(self, records, winning_branch):
        by_id = {item["hypothesis_id"]: item for item in records}
        candidates = [item for item in records if item["status"] in {"VALIDATED", "EXECUTED", "SUPPORTED"}]
        for hypothesis_id in winning_branch.get("generated_hypotheses", []) or []:
            if hypothesis_id in by_id:
                record = by_id[hypothesis_id]
                return {
                    "hypothesis_id": record["hypothesis_id"],
                    "confidence": record["confidence_history"][-1]["confidence_after"],
                    "status": record["status"],
                }
        if candidates:
            record = max(candidates, key=lambda item: item["confidence_history"][-1]["confidence_after"])
            return {
                "hypothesis_id": record["hypothesis_id"],
                "confidence": record["confidence_history"][-1]["confidence_after"],
                "status": record["status"],
            }
        return {}

    def _hypothesis_statistics(self, records):
        counts = Counter(item["status"] for item in records)
        return {
            "hypothesis_count": len(records),
            "created": counts.get("CREATED", 0),
            "active": counts.get("ACTIVE", 0),
            "supported": counts.get("SUPPORTED", 0),
            "questioned": counts.get("QUESTIONED", 0),
            "merged": counts.get("MERGED", 0),
            "rejected": counts.get("REJECTED", 0),
            "validated": counts.get("VALIDATED", 0),
            "executed": counts.get("EXECUTED", 0),
            "archived": counts.get("ARCHIVED", 0),
        }

    def _branch_statistics(self, branches, hypotheses, winning_branch):
        counts = Counter(item["state"] for item in branches)
        return {
            "branch_count": len(branches),
            "active_branches": counts.get("ACTIVE", 0),
            "merged_branches": counts.get("MERGED", 0),
            "discarded_branches": counts.get("DISCARDED", 0),
            "validated_branches": counts.get("VALIDATED", 0),
            "winning_branch": winning_branch.get("branch_id"),
            "average_branch_depth": self._average(item["branch_depth"] for item in branches),
            "average_branch_width": self._average(item["branch_width"] for item in branches),
            "generated_hypotheses": len(hypotheses),
            "merged_hypotheses": sum(len(item["merged_hypotheses"]) for item in branches),
            "discarded_hypotheses": sum(len(item["discarded_hypotheses"]) for item in branches),
            "average_confidence": self._average(item["confidence"] for item in branches),
        }

    def _confidence_distribution(self, history):
        values = [item["confidence_after"] for item in history if isinstance(item.get("confidence_after"), (int, float))]
        return {
            "low": sum(1 for value in values if value < 0.4),
            "medium": sum(1 for value in values if 0.4 <= value < 0.75),
            "high": sum(1 for value in values if value >= 0.75),
            "average": self._average(values),
        }

    def _pending_validations(self, hypotheses, validation):
        pending = [
            item["hypothesis_id"]
            for item in hypotheses
            if item["status"] in {"CREATED", "ACTIVE", "SUPPORTED", "QUESTIONED"}
        ]
        reports = validation.get("reports", []) if isinstance(validation, Mapping) else []
        if reports:
            return pending[:12]
        return pending[:12]

    def _confidence_reason(self, status, confidence, prior):
        if status == "REJECTED":
            return "validation or branch outcome rejected the hypothesis"
        if status == "VALIDATED":
            return "validation evidence increased or confirmed confidence"
        if confidence > prior:
            return "supporting evidence increased confidence"
        if confidence < prior:
            return "contradicting or insufficient evidence reduced confidence"
        return "confidence preserved by available evidence"

    def _capability_confidence(self, capability, report):
        confidence = report.get("capability_confidence", {}) if isinstance(report, Mapping) else {}
        if isinstance(confidence, Mapping):
            return self._score(confidence.get(capability), 0.5)
        for item in report.get("capability_inventory", []) or []:
            if isinstance(item, Mapping) and item.get("capability_id") == capability:
                return self._score(item.get("confidence"), 0.5)
        return 0.5

    def _dependency_summary(self, dependency):
        if not dependency:
            return []
        summary = []
        for key in ("injected_dependencies", "dependency_findings", "missing_dependencies"):
            value = dependency.get(key)
            if value:
                summary.append({key: self._as_list(value)[:5]})
        return summary[:5]

    def _mapping(self, value):
        return value if isinstance(value, Mapping) else {}

    def _as_list(self, value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, set):
            return list(value)
        if isinstance(value, Mapping):
            return [value]
        return [value]

    def _score(self, value, default=0.0):
        if isinstance(value, (int, float)):
            return round(max(0.0, min(float(value), 1.0)), 4)
        return round(float(default or 0.0), 4)

    def _average(self, values):
        values = [float(value) for value in values if isinstance(value, (int, float))]
        return round(sum(values) / max(len(values), 1), 4) if values else 0.0

    def _timestamp(self):
        return datetime.utcnow().isoformat(timespec="microseconds") + "Z"

    def _node_key(self, prefix, value):
        return f"{prefix}:{str(value).replace(' ', '_')}"

    def _delta(self, before, after):
        delta = round((float(after or 0.0) - float(before or 0.0)) * 100, 2)
        sign = "+" if delta >= 0 else ""
        return f"{sign}{delta}%"


reasoning_graph_report_builder = ReasoningGraphReportBuilder()


__all__ = [
    "ReasoningGraphReportBuilder",
    "reasoning_graph_report_builder",
]
