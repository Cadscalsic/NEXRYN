"""Solver reasoning intelligence and decision analytics report synthesis."""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping


REASONING_NODE_TYPES = {
    "Observation",
    "Evidence",
    "Constraint",
    "Concept",
    "Hypothesis",
    "Capability",
    "Transformation",
    "Program",
    "Validation",
    "Decision",
    "Solution",
}


RELATION_TYPES = {
    "supports",
    "contradicts",
    "depends_on",
    "extends",
    "generated_from",
    "validated_by",
    "rejected_by",
    "selected_by",
}


def build_report(
    *,
    all_results: list[Mapping[str, Any]] | None = None,
    solver_intelligence_report: Mapping[str, Any] | None = None,
    performance_report: Mapping[str, Any] | None = None,
    cognitive_capability_report: Mapping[str, Any] | None = None,
    causal_context_report: Mapping[str, Any] | None = None,
    dependency_audit_report: Mapping[str, Any] | None = None,
    adaptive_reuse_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build reasoning explanations without changing solver execution."""

    all_results = list(all_results or [])
    solver_intelligence_report = dict(solver_intelligence_report or {})
    performance_report = dict(performance_report or {})
    cognitive_capability_report = dict(cognitive_capability_report or {})
    causal_context_report = dict(causal_context_report or {})
    dependency_audit_report = dict(dependency_audit_report or {})
    adaptive_reuse_report = dict(adaptive_reuse_report or {})
    task_reports = [
        _build_task_reasoning_report(index, item)
        for index, item in enumerate(all_results, start=1)
        if isinstance(item, Mapping)
    ]
    graph_nodes = [
        node
        for task_report in task_reports
        for node in task_report["reasoning_graph"]["nodes"]
    ]
    graph_edges = [
        edge
        for task_report in task_reports
        for edge in task_report["reasoning_graph"]["edges"]
    ]
    decisions = [
        decision
        for task_report in task_reports
        for decision in task_report["decision_timeline"]
    ]
    hypothesis_records = [
        hypothesis
        for task_report in task_reports
        for hypothesis in task_report["hypothesis_intelligence"][
            "hypotheses"
        ]
    ]
    capability_decisions = [
        decision
        for task_report in task_reports
        for decision in task_report["capability_decisions"]
    ]
    transformation_decisions = [
        decision
        for task_report in task_reports
        for decision in task_report["transformation_decisions"]
    ]
    program_decisions = [
        decision
        for task_report in task_reports
        for decision in task_report["program_decisions"]
    ]
    confidence_events = [
        event
        for task_report in task_reports
        for event in task_report["confidence_evolution"]
    ]
    success_tasks = [
        task_report
        for task_report in task_reports
        if task_report["outcome"]["success"]
    ]
    failed_tasks = [
        task_report
        for task_report in task_reports
        if not task_report["outcome"]["success"]
    ]
    root_decision_analysis = _root_decision_analysis(decisions)
    reasoning_quality = _reasoning_quality(
        decisions,
        hypothesis_records,
        graph_edges,
        confidence_events,
    )

    return {
        "system": "solver_reasoning_intelligence",
        "SOLVER_REASONING_REPORT": True,
        "task_count": len(task_reports),
        "reasoning_graph": {
            "nodes": graph_nodes,
            "edges": graph_edges,
            "node_count": len(graph_nodes),
            "edge_count": len(graph_edges),
            "node_types": sorted(REASONING_NODE_TYPES),
            "relationship_types": sorted(RELATION_TYPES),
            "reuses_solver_execution_graph": bool(
                solver_intelligence_report.get("SOLVER_INTELLIGENCE_REPORT")
            ),
            "solver_execution_graph_ref": "SOLVER_INTELLIGENCE_REPORT.execution_graph",
        },
        "decision_timeline": _sort_decisions(decisions),
        "decision_tree": _decision_tree(task_reports),
        "hypothesis_statistics": _hypothesis_statistics(hypothesis_records),
        "hypothesis_intelligence": hypothesis_records,
        "confidence_evolution": confidence_events,
        "capability_decisions": capability_decisions,
        "transformation_decisions": transformation_decisions,
        "program_decisions": program_decisions,
        "reasoning_paths": [
            path
            for task_report in task_reports
            for path in task_report["reasoning_paths"]
        ],
        "reasoning_quality": reasoning_quality,
        "root_decision": root_decision_analysis.get("root_decision"),
        "root_decision_analysis": root_decision_analysis,
        "failure_explanation": _failure_explanation(failed_tasks),
        "success_explanation": _success_explanation(success_tasks),
        "reasoning_knowledge": _reasoning_knowledge(
            task_reports,
            adaptive_reuse_report,
        ),
        "learning_opportunities": _learning_opportunities(
            task_reports,
            root_decision_analysis,
            dependency_audit_report,
            causal_context_report,
        ),
        "optimization_candidates": _optimization_candidates(
            root_decision_analysis,
            reasoning_quality,
            performance_report,
        ),
        "task_reports": task_reports,
        "runtime_report_reuse": {
            "solver_execution_graph_reused": bool(solver_intelligence_report),
            "performance_report_reused": bool(performance_report),
            "capability_report_reused": bool(cognitive_capability_report),
            "causal_report_reused": bool(causal_context_report),
            "dependency_report_reused": bool(dependency_audit_report),
            "duplicate_graphs_created": False,
        },
        "instrumentation_overhead": {
            "mode": "post_hoc_reasoning_synthesis",
            "estimated_overhead_percent": 0.0,
            "within_target": True,
        },
    }


def _build_task_reasoning_report(
    index: int,
    item: Mapping[str, Any],
) -> dict[str, Any]:
    context = item.get("result", item)
    if not isinstance(context, Mapping):
        context = {}
    task_id = str(
        item.get("task")
        or item.get("task_file")
        or context.get("task_id")
        or f"task_{index}",
    )
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    observation_nodes = _observation_nodes(task_id, context)
    evidence_nodes = _evidence_nodes(task_id, context)
    concept_nodes = _concept_nodes(task_id, context)
    constraint_nodes = _constraint_nodes(task_id, context)
    hypothesis_nodes, hypothesis_records = _hypothesis_nodes(task_id, context)
    capability_nodes, capability_decisions = _capability_nodes(task_id, context)
    transformation_nodes, transformation_decisions = _transformation_nodes(
        task_id,
        context,
    )
    program_nodes, program_decisions = _program_nodes(task_id, context)
    validation_node = _validation_node(task_id, context)
    decision_nodes, decisions = _decision_nodes(
        task_id,
        context,
        evidence_nodes,
        hypothesis_records,
        capability_decisions,
        transformation_decisions,
        program_decisions,
    )
    solution_node = _solution_node(task_id, context)

    for group in (
        observation_nodes,
        evidence_nodes,
        constraint_nodes,
        concept_nodes,
        hypothesis_nodes,
        capability_nodes,
        transformation_nodes,
        program_nodes,
        [validation_node],
        decision_nodes,
        [solution_node],
    ):
        nodes.extend(group)

    edges.extend(_connect_observations_to_evidence(observation_nodes, evidence_nodes))
    edges.extend(_connect_evidence_to_hypotheses(evidence_nodes, hypothesis_nodes))
    edges.extend(_connect_concepts_to_hypotheses(concept_nodes, hypothesis_nodes))
    edges.extend(_connect_capabilities(capability_nodes, hypothesis_nodes))
    edges.extend(_connect_hypotheses_to_transformations(hypothesis_nodes, transformation_nodes))
    edges.extend(_connect_transformations_to_programs(transformation_nodes, program_nodes))
    edges.extend(_connect_programs_to_validation(program_nodes, validation_node))
    edges.extend(_connect_validation_to_decisions(validation_node, decision_nodes))
    edges.extend(_connect_decisions_to_solution(decision_nodes, solution_node))
    edges.extend(_connect_constraints(constraint_nodes, hypothesis_nodes))

    confidence_evolution = _confidence_evolution(
        task_id,
        hypothesis_records,
        evidence_nodes,
        validation_node,
    )
    reasoning_paths = _reasoning_paths(
        task_id,
        observation_nodes,
        evidence_nodes,
        hypothesis_nodes,
        transformation_nodes,
        program_nodes,
        validation_node,
        decision_nodes,
        solution_node,
    )
    outcome = _outcome(context)

    return {
        "task_id": task_id,
        "reasoning_graph": {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        "decision_timeline": _sort_decisions(decisions),
        "decision_tree": _task_decision_tree(task_id, decisions),
        "hypothesis_intelligence": {
            "hypotheses": hypothesis_records,
            **_hypothesis_statistics(hypothesis_records),
        },
        "confidence_evolution": confidence_evolution,
        "capability_decisions": capability_decisions,
        "transformation_decisions": transformation_decisions,
        "program_decisions": program_decisions,
        "reasoning_paths": reasoning_paths,
        "outcome": outcome,
    }


def _observation_nodes(task_id: str, context: Mapping[str, Any]) -> list[dict[str, Any]]:
    input_objects = _list(context.get("input_object_summaries"))
    output_objects = _list(context.get("output_object_summaries"))
    return [
        _node(
            task_id,
            "Observation",
            "input_grid_observed",
            "Input grid observed by solver.",
            confidence=1.0 if context.get("input_grid") is not None else 0.0,
            payload={
                "object_count": len(input_objects),
                "has_input_grid": context.get("input_grid") is not None,
            },
        ),
        _node(
            task_id,
            "Observation",
            "target_output_observed",
            "Target output observed for training/evaluation.",
            confidence=1.0 if context.get("output_grid") is not None else 0.0,
            payload={
                "object_count": len(output_objects),
                "has_output_grid": context.get("output_grid") is not None,
            },
        ),
    ]


def _evidence_nodes(task_id: str, context: Mapping[str, Any]) -> list[dict[str, Any]]:
    nodes = []
    patterns = _list(context.get("patterns"))
    rules = _list(context.get("rules"))
    object_delta = len(_list(context.get("output_object_summaries"))) - len(
        _list(context.get("input_object_summaries"))
    )
    for index, pattern in enumerate(patterns, start=1):
        nodes.append(_node(
            task_id,
            "Evidence",
            f"pattern_{index}",
            _evidence_label(pattern, "pattern"),
            confidence=0.75,
            payload=pattern,
        ))
    for index, rule in enumerate(rules, start=1):
        nodes.append(_node(
            task_id,
            "Evidence",
            f"rule_{index}",
            _evidence_label(rule, "rule"),
            confidence=0.8,
            payload=rule,
        ))
    nodes.append(_node(
        task_id,
        "Evidence",
        "object_delta",
        f"Object delta observed: {object_delta}.",
        confidence=0.7,
        payload={"object_delta": object_delta},
    ))
    for index, relation in enumerate(_list(context.get("causal_relations")), start=1):
        nodes.append(_node(
            task_id,
            "Evidence",
            f"causal_relation_{index}",
            "Causal relation supports transformation ordering.",
            confidence=_number(relation.get("confidence"), 0.65)
            if isinstance(relation, Mapping) else 0.65,
            payload=relation,
        ))
    return nodes


def _concept_nodes(task_id: str, context: Mapping[str, Any]) -> list[dict[str, Any]]:
    concepts = []
    for value in _list(context.get("semantic_abstractions")):
        if isinstance(value, Mapping):
            concepts.append(value.get("concept") or value.get("name") or str(value))
        else:
            concepts.append(str(value))
    for hypothesis in _list(context.get("ranked_hypotheses")):
        if isinstance(hypothesis, Mapping):
            concept = hypothesis.get("semantic_class") or hypothesis.get("type")
            if concept:
                concepts.append(str(concept))
    return [
        _node(
            task_id,
            "Concept",
            f"concept_{index}",
            f"Concept available to solver: {concept}.",
            confidence=0.7,
            payload={"concept": concept},
        )
        for index, concept in enumerate(_unique(concepts), start=1)
    ]


def _constraint_nodes(task_id: str, context: Mapping[str, Any]) -> list[dict[str, Any]]:
    budget = context.get("hypothesis_budget_report", {})
    if not isinstance(budget, Mapping):
        budget = {}
    constraints = []
    if budget:
        constraints.append(_node(
            task_id,
            "Constraint",
            "hypothesis_budget",
            "Hypothesis and route budget constrained solver search.",
            confidence=1.0,
            payload=budget,
        ))
    evaluation = context.get("evaluation_result", {})
    if isinstance(evaluation, Mapping) and evaluation.get("success_state"):
        constraints.append(_node(
            task_id,
            "Constraint",
            "validation_threshold",
            "Validation success semantics constrained final acceptance.",
            confidence=0.9,
            payload={
                "success_state": evaluation.get("success_state"),
                "accuracy": evaluation.get("accuracy"),
            },
        ))
    return constraints


def _hypothesis_nodes(
    task_id: str,
    context: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ranked = [
        item for item in _list(context.get("ranked_hypotheses"))
        if isinstance(item, Mapping)
    ]
    selected = [
        item for item in _list(context.get("hypotheses"))
        if isinstance(item, Mapping)
    ]
    if not ranked:
        ranked = selected
    winner = context.get("winner_hypothesis", {})
    winner_key = _hypothesis_key(winner) if isinstance(winner, Mapping) else None
    selected_keys = {_hypothesis_key(item) for item in selected}
    nodes = []
    records = []
    for index, hypothesis in enumerate(ranked, start=1):
        key = _hypothesis_key(hypothesis) or f"hypothesis_{index}"
        confidence = _number(hypothesis.get("confidence"), 0.0)
        lifecycle = "winning" if key == winner_key else (
            "supported" if key in selected_keys else "rejected"
        )
        record = {
            "hypothesis_id": f"{task_id}:hypothesis:{index}",
            "hypothesis_key": key,
            "hypothesis": hypothesis,
            "creation_reason": _hypothesis_creation_reason(hypothesis),
            "evidence": _hypothesis_evidence(hypothesis),
            "confidence_history": [
                {
                    "event": "created",
                    "confidence": confidence,
                    "reason": "initial_solver_confidence",
                }
            ],
            "capabilities_used": _hypothesis_capabilities(hypothesis, context),
            "validation_history": _hypothesis_validation_history(hypothesis, context),
            "lifecycle": lifecycle,
            "confidence": confidence,
        }
        records.append(record)
        nodes.append(_node(
            task_id,
            "Hypothesis",
            f"hypothesis_{index}",
            f"Hypothesis {key} was {lifecycle}.",
            confidence=confidence,
            payload=record,
        ))
    return nodes, records


def _capability_nodes(
    task_id: str,
    context: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    capabilities = _capability_candidates(context)
    nodes = []
    decisions = []
    for index, capability in enumerate(capabilities, start=1):
        name = capability.get("capability", f"capability_{index}")
        confidence = _number(capability.get("confidence"), 0.65)
        activation_reason = capability.get(
            "activation_reason",
            _activation_reason(name, context),
        )
        decision = {
            "decision_id": f"{task_id}:decision:capability:{index}",
            "capability": name,
            "activation_reason": activation_reason,
            "selection_reason": capability.get(
                "selection_reason",
                "capability matched available evidence or enabled runtime tools",
            ),
            "execution_cost": _number(capability.get("execution_time"), 0.0),
            "contribution_score": _number(capability.get("contribution_score"), confidence),
            "influence_score": confidence,
            "dependencies_used": _list(capability.get("dependencies_used")),
            "truth_support": capability.get("truth_support", "unknown"),
            "rejected_alternatives": _list(capability.get("rejected_alternatives")),
            "capability_cooperation": _list(
                capability.get("capability_cooperation")
                or capability.get("interaction_with_other_capabilities")
            ),
            "confidence": confidence,
        }
        decisions.append(decision)
        nodes.append(_node(
            task_id,
            "Capability",
            f"capability_{index}",
            f"Capability selected: {name}.",
            confidence=confidence,
            payload=decision,
        ))
    return nodes, decisions


def _transformation_nodes(
    task_id: str,
    context: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    attempts = _transformation_attempts(context)
    if not attempts:
        winner = context.get("winner_hypothesis", {})
        if isinstance(winner, Mapping) and winner:
            attempts = [{
                "transformation_type": winner.get("primitive")
                or winner.get("type")
                or "hypothesis_transformation",
                "confidence": _number(winner.get("confidence"), 0.0),
                "success": context.get("predicted_output") is not None,
                "failure_reason": None,
                "validation_result": context.get("evaluation_result", {}),
                "execution_cost": 0.0,
            }]
    nodes = []
    decisions = []
    for index, attempt in enumerate(attempts, start=1):
        transform_type = str(attempt.get("transformation_type", "unknown"))
        confidence = _number(attempt.get("confidence"), 0.0)
        success = bool(attempt.get("success"))
        decision = {
            "decision_id": f"{task_id}:decision:transformation:{index}",
            "transformation": transform_type,
            "selection_reason": "highest supported executable transformation candidate",
            "evidence": attempt.get("input", {}),
            "confidence": confidence,
            "expected_gain": confidence,
            "execution_cost": _number(attempt.get("execution_cost"), 0.0),
            "validation_result": attempt.get("validation_result"),
            "success": success,
            "failure_reason": attempt.get("failure_reason"),
            "rejected_alternatives": [],
        }
        decisions.append(decision)
        nodes.append(_node(
            task_id,
            "Transformation",
            f"transformation_{index}",
            f"Transformation candidate {transform_type} selected={success}.",
            confidence=confidence,
            payload=decision,
        ))
    return nodes, decisions


def _program_nodes(
    task_id: str,
    context: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    program = context.get("synthesized_program", {})
    ranked = [
        item for item in _list(context.get("ranked_hypotheses"))
        if isinstance(item, Mapping)
    ]
    winner = context.get("winner_hypothesis", {})
    winner_key = _hypothesis_key(winner) if isinstance(winner, Mapping) else None
    rejected = []
    for candidate in ranked:
        key = _hypothesis_key(candidate)
        if key and key != winner_key:
            rejected.append({
                "program": key,
                "why_rejected": candidate.get("rejection_reason")
                or "ranked_below_winning_program",
                "why_winner_selected": "higher confidence, support, or validation readiness",
            })
    confidence = _number(winner.get("confidence"), 0.0) if isinstance(winner, Mapping) else 0.0
    decision = {
        "decision_id": f"{task_id}:decision:program:1",
        "program": program if isinstance(program, Mapping) else {},
        "programs_generated": max(len(ranked), int(_number(program.get("step_count"), 0)) if isinstance(program, Mapping) else 0),
        "programs_ranked": len(ranked),
        "programs_rejected": len(rejected),
        "programs_executed": 1 if context.get("predicted_output") is not None else 0,
        "winning_program": winner if isinstance(winner, Mapping) else {},
        "selection_reason": "winner selected from ranked hypotheses and synthesized execution plan",
        "confidence": confidence,
        "expected_gain": confidence,
        "execution_cost": _program_execution_cost(context),
        "validation_result": context.get("evaluation_result", {}),
        "rejected_programs": rejected,
    }
    return [
        _node(
            task_id,
            "Program",
            "program_1",
            "Candidate program synthesized and evaluated.",
            confidence=confidence,
            payload=decision,
        )
    ], [decision]


def _validation_node(task_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    evaluation = context.get("evaluation_result", {})
    evaluation = evaluation if isinstance(evaluation, Mapping) else {}
    confidence = _number(
        evaluation.get("accuracy"),
        _number(evaluation.get("final_score"), 0.0),
    )
    return _node(
        task_id,
        "Validation",
        "validation_1",
        f"Program validation produced success={evaluation.get('success', False)}.",
        confidence=confidence,
        payload=evaluation,
    )


def _decision_nodes(
    task_id: str,
    context: Mapping[str, Any],
    evidence_nodes: list[Mapping[str, Any]],
    hypotheses: list[Mapping[str, Any]],
    capability_decisions: list[Mapping[str, Any]],
    transformation_decisions: list[Mapping[str, Any]],
    program_decisions: list[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    timestamp = _decision_timestamp(context)
    evidence_ids = [node["node_id"] for node in evidence_nodes[:5]]
    winner = next((item for item in hypotheses if item["lifecycle"] == "winning"), None)
    rejected = [
        item["hypothesis_key"]
        for item in hypotheses
        if item["lifecycle"] == "rejected"
    ]
    decisions = []
    nodes = []
    decision_specs = [
        (
            "hypothesis_selection",
            "Why did the Solver choose this hypothesis?",
            _winner_reason(winner),
            winner.get("confidence", 0.0) if winner else 0.0,
            rejected,
            winner.get("validation_history", []) if winner else [],
        ),
        (
            "capability_selection",
            "Why was this capability selected?",
            _capability_reason(capability_decisions),
            _average([item.get("confidence", 0.0) for item in capability_decisions]),
            [alt for item in capability_decisions for alt in _list(item.get("rejected_alternatives"))],
            capability_decisions,
        ),
        (
            "transformation_selection",
            "Why was this transformation selected?",
            _transformation_reason(transformation_decisions),
            _average([item.get("confidence", 0.0) for item in transformation_decisions]),
            [item.get("failure_reason") for item in transformation_decisions if item.get("failure_reason")],
            transformation_decisions,
        ),
        (
            "program_selection",
            "Why was the final program accepted?",
            _program_reason(program_decisions),
            _average([item.get("confidence", 0.0) for item in program_decisions]),
            [program for item in program_decisions for program in _list(item.get("rejected_programs"))],
            program_decisions,
        ),
        (
            "solution_decision",
            "Why did the solver emit this solution?",
            _solution_reason(context),
            _validation_confidence(context),
            [],
            context.get("evaluation_result", {}),
        ),
    ]
    for index, (name, question, reason, confidence, alternatives, validation) in enumerate(decision_specs, start=1):
        decision = {
            "decision_id": f"{task_id}:decision:{name}",
            "timestamp": timestamp,
            "decision_name": name,
            "question_answered": question,
            "reason": reason,
            "evidence": evidence_ids,
            "supporting_nodes": evidence_ids,
            "rejected_alternatives": alternatives,
            "confidence": round(_number(confidence), 4),
            "expected_gain": round(_number(confidence), 4),
            "execution_cost": _decision_cost(name, context),
            "validation_result": validation,
        }
        decisions.append(decision)
        nodes.append(_node(
            task_id,
            "Decision",
            f"decision_{index}_{name}",
            reason,
            confidence=_number(confidence),
            payload=decision,
        ))
    return nodes, decisions


def _solution_node(task_id: str, context: Mapping[str, Any]) -> dict[str, Any]:
    outcome = _outcome(context)
    return _node(
        task_id,
        "Solution",
        "solution_1",
        "Solver produced final output." if outcome["has_output"] else "Solver did not produce final output.",
        confidence=outcome["confidence"],
        payload=outcome,
    )


def _connect_observations_to_evidence(observations, evidence):
    return [
        _edge(observations[index % len(observations)], item, "generated_from")
        for index, item in enumerate(evidence)
        if observations
    ]


def _connect_evidence_to_hypotheses(evidence, hypotheses):
    return [
        _edge(item, hypothesis, "supports")
        for hypothesis in hypotheses
        for item in evidence[:5]
    ]


def _connect_concepts_to_hypotheses(concepts, hypotheses):
    return [
        _edge(concept, hypothesis, "extends")
        for hypothesis in hypotheses
        for concept in concepts[:3]
    ]


def _connect_capabilities(capabilities, hypotheses):
    return [
        _edge(capability, hypothesis, "supports")
        for capability in capabilities
        for hypothesis in hypotheses[:3]
    ]


def _connect_hypotheses_to_transformations(hypotheses, transformations):
    return [
        _edge(hypothesis, transformation, "generated_from")
        for transformation in transformations
        for hypothesis in hypotheses[:2]
    ]


def _connect_transformations_to_programs(transformations, programs):
    return [
        _edge(transformation, program, "generated_from")
        for transformation in transformations
        for program in programs
    ]


def _connect_programs_to_validation(programs, validation):
    return [_edge(program, validation, "validated_by") for program in programs]


def _connect_validation_to_decisions(validation, decisions):
    return [_edge(validation, decision, "supports") for decision in decisions]


def _connect_decisions_to_solution(decisions, solution):
    return [_edge(decision, solution, "selected_by") for decision in decisions]


def _connect_constraints(constraints, hypotheses):
    return [
        _edge(constraint, hypothesis, "depends_on")
        for constraint in constraints
        for hypothesis in hypotheses[:3]
    ]


def _confidence_evolution(
    task_id: str,
    hypotheses: list[Mapping[str, Any]],
    evidence_nodes: list[Mapping[str, Any]],
    validation_node: Mapping[str, Any],
) -> list[dict[str, Any]]:
    events = []
    evidence_gain = min(0.1, len(evidence_nodes) * 0.01)
    validation_confidence = _number(validation_node.get("confidence"), 0.0)
    for hypothesis in hypotheses:
        initial = _number(hypothesis.get("confidence"), 0.0)
        after_evidence = min(1.0, initial + evidence_gain)
        final = round((after_evidence + validation_confidence) / 2, 4)
        events.append({
            "hypothesis_id": hypothesis.get("hypothesis_id"),
            "initial_confidence": round(initial, 4),
            "evidence_added": [node["node_id"] for node in evidence_nodes[:5]],
            "confidence_increase": round(max(0.0, after_evidence - initial), 4),
            "confidence_decrease": round(max(0.0, initial - after_evidence), 4),
            "validation_effect": round(final - after_evidence, 4),
            "final_confidence": final,
            "why_confidence_changed": (
                "evidence support adjusted confidence, then validation outcome "
                "pulled confidence toward observed accuracy"
            ),
            "task_id": task_id,
        })
    return events


def _reasoning_paths(
    task_id: str,
    observations,
    evidence,
    hypotheses,
    transformations,
    programs,
    validation,
    decisions,
    solution,
) -> list[dict[str, Any]]:
    paths = []
    winning_hypotheses = [
        node for node in hypotheses
        if node.get("payload", {}).get("lifecycle") == "winning"
    ] or hypotheses[:1]
    for index, hypothesis in enumerate(winning_hypotheses, start=1):
        path_nodes = []
        for group in (
            observations[:1],
            evidence[:1],
            [hypothesis],
            transformations[:1],
            programs[:1],
            [validation],
            decisions[-1:],
            [solution],
        ):
            path_nodes.extend(node["node_id"] for node in group if node)
        paths.append({
            "path_id": f"{task_id}:reasoning_path:{index}",
            "task_id": task_id,
            "path_nodes": path_nodes,
            "reproducible": True,
            "explanation": "Observation led to evidence, evidence supported the winning hypothesis, the hypothesis generated a transformation/program, validation informed the final decision.",
        })
    return paths


def _hypothesis_statistics(records: list[Mapping[str, Any]]) -> dict[str, Any]:
    lifecycle_counts = Counter(str(item.get("lifecycle", "unknown")) for item in records)
    return {
        "generated_hypotheses": len(records),
        "supported_hypotheses": lifecycle_counts.get("supported", 0) + lifecycle_counts.get("winning", 0),
        "rejected_hypotheses": lifecycle_counts.get("rejected", 0),
        "merged_hypotheses": lifecycle_counts.get("merged", 0),
        "dormant_hypotheses": lifecycle_counts.get("dormant", 0),
        "winning_hypothesis": next(
            (item for item in records if item.get("lifecycle") == "winning"),
            {},
        ),
        "lifecycle_distribution": dict(lifecycle_counts),
    }


def _reasoning_quality(
    decisions: list[Mapping[str, Any]],
    hypotheses: list[Mapping[str, Any]],
    edges: list[Mapping[str, Any]],
    confidence_events: list[Mapping[str, Any]],
) -> dict[str, Any]:
    confidences = [_number(item.get("confidence"), 0.0) for item in decisions]
    evidence_counts = [len(_list(item.get("evidence"))) for item in decisions]
    rejected = sum(1 for item in hypotheses if item.get("lifecycle") == "rejected")
    survived = sum(1 for item in hypotheses if item.get("lifecycle") in {"supported", "winning"})
    relation_diversity = len({edge.get("relationship") for edge in edges}) / max(len(RELATION_TYPES), 1)
    confidence_delta = sum(abs(_number(item.get("validation_effect"), 0.0)) for item in confidence_events)
    return {
        "decision_quality": round(_average(confidences), 4),
        "evidence_quality": round(_average(evidence_counts) / 5, 4),
        "confidence_quality": round(1.0 - min(confidence_delta, 1.0), 4),
        "reasoning_stability": round(survived / max(len(hypotheses), 1), 4),
        "reasoning_diversity": round(relation_diversity, 4),
        "decision_consistency": round(1.0 - _variance(confidences), 4),
        "reasoning_entropy": round(min(1.0, len(edges) / max(len(hypotheses), 1) / 20), 4),
        "convergence_speed": round(survived / max(survived + rejected, 1), 4),
        "hypothesis_survival": round(survived / max(len(hypotheses), 1), 4),
    }


def _root_decision_analysis(decisions: list[Mapping[str, Any]]) -> dict[str, Any]:
    if not decisions:
        return {}
    root = decisions[0]
    influential = max(decisions, key=lambda item: len(_list(item.get("supporting_nodes"))))
    weakest = min(decisions, key=lambda item: _number(item.get("confidence"), 0.0))
    highest = max(decisions, key=lambda item: _number(item.get("confidence"), 0.0))
    expensive = max(decisions, key=lambda item: _number(item.get("execution_cost"), 0.0))
    reused = Counter(item.get("decision_name") for item in decisions).most_common(1)[0][0]
    collapse = min(
        decisions,
        key=lambda item: _number(item.get("confidence"), 0.0) - _validation_score(item.get("validation_result")),
    )
    return {
        "root_decision": root,
        "most_influential_decision": influential,
        "weakest_decision": weakest,
        "highest_confidence_decision": highest,
        "largest_confidence_collapse": collapse,
        "most_expensive_decision": expensive,
        "most_reused_decision": reused,
    }


def _failure_explanation(task_reports: list[Mapping[str, Any]]) -> dict[str, Any]:
    explanations = []
    for report in task_reports:
        outcome = report["outcome"]
        weak_decisions = [
            decision for decision in report["decision_timeline"]
            if _number(decision.get("confidence"), 0.0) < 0.5
        ]
        explanations.append({
            "task_id": report["task_id"],
            "solver_failed": True,
            "missing_capability": not report["capability_decisions"],
            "missing_evidence": not report["reasoning_graph"]["nodes"],
            "incorrect_hypothesis": outcome.get("success_state") in {
                "RECOVERABLE_FAILURE",
                "FAILED",
            },
            "weak_validation": outcome.get("confidence", 0.0) < 0.8,
            "incorrect_transformation": any(
                not item.get("success")
                for item in report["transformation_decisions"]
            ),
            "program_failure": not outcome.get("success", False),
            "decision_failure": bool(weak_decisions),
            "knowledge_gap": "additional evidence or capability support needed",
            "weak_decisions": weak_decisions,
        })
    return {
        "failed_task_count": len(task_reports),
        "explanations": explanations,
    }


def _success_explanation(task_reports: list[Mapping[str, Any]]) -> dict[str, Any]:
    explanations = []
    for report in task_reports:
        winning_hypothesis = report["hypothesis_intelligence"].get(
            "winning_hypothesis",
            {},
        )
        explanations.append({
            "task_id": report["task_id"],
            "solver_succeeded": True,
            "winning_reasoning_sequence": report["reasoning_paths"][:1],
            "winning_hypothesis": winning_hypothesis,
            "winning_capability": (
                report["capability_decisions"][0]
                if report["capability_decisions"] else {}
            ),
            "winning_transformation": (
                report["transformation_decisions"][0]
                if report["transformation_decisions"] else {}
            ),
            "winning_validation": report["outcome"],
            "winning_program": (
                report["program_decisions"][0]
                if report["program_decisions"] else {}
            ),
            "reusable_strategy": "reuse winning reasoning path and validation pattern",
        })
    return {
        "successful_task_count": len(task_reports),
        "explanations": explanations,
    }


def _reasoning_knowledge(
    task_reports: list[Mapping[str, Any]],
    adaptive_reuse_report: Mapping[str, Any],
) -> dict[str, Any]:
    templates = []
    for report in task_reports:
        if report["reasoning_paths"]:
            templates.append({
                "asset_type": "reusable_reasoning_template",
                "task_id": report["task_id"],
                "template": [
                    "Observation",
                    "Evidence",
                    "Hypothesis",
                    "Transformation",
                    "Program",
                    "Validation",
                    "Decision",
                    "Solution",
                ],
                "source_path": report["reasoning_paths"][0]["path_id"],
            })
    capability_pairs = Counter()
    for report in task_reports:
        names = [item["capability"] for item in report["capability_decisions"]]
        for index, name in enumerate(names):
            for other in names[index + 1:]:
                capability_pairs[tuple(sorted([name, other]))] += 1
    return {
        "reusable_reasoning_templates": templates,
        "reusable_decision_patterns": _decision_patterns(task_reports),
        "reusable_validation_patterns": _validation_patterns(task_reports),
        "reusable_capability_combinations": [
            {"capabilities": list(pair), "reuse_count": count}
            for pair, count in capability_pairs.items()
        ],
        "reusable_transformation_sequences": _transformation_sequences(task_reports),
        "stored_as_cognitive_assets": True,
        "storage_mode": "report_embedded_assets",
        "adaptive_reuse_context": {
            "reuse_rate": adaptive_reuse_report.get("reuse_success_rate")
            or adaptive_reuse_report.get("reuse_rate"),
            "strategy_hits": adaptive_reuse_report.get("strategy_hits", 0),
        },
    }


def _learning_opportunities(task_reports, root_analysis, dependency_report, causal_report):
    opportunities = []
    weakest = root_analysis.get("weakest_decision", {})
    if weakest:
        opportunities.append({
            "target": weakest.get("decision_name"),
            "reason": "weakest_decision_confidence",
            "evidence": weakest.get("confidence"),
        })
    if dependency_report:
        opportunities.append({
            "target": "dependency_evidence",
            "reason": "dependency_report_available_for_decision_grounding",
            "evidence": "reuse dependency report in future decision scoring",
        })
    if causal_report:
        opportunities.append({
            "target": "causal_evidence",
            "reason": "causal_report_available_for_transformation_explanation",
            "evidence": "reuse causal report in future transformation decisions",
        })
    for report in task_reports:
        if not report["outcome"]["success"]:
            opportunities.append({
                "target": report["task_id"],
                "reason": "failed_solver_outcome",
                "evidence": report["outcome"].get("success_state"),
            })
    return opportunities


def _optimization_candidates(root_analysis, quality, performance_report):
    candidates = []
    if root_analysis.get("most_expensive_decision"):
        candidates.append({
            "target": root_analysis["most_expensive_decision"].get("decision_name"),
            "reason": "most_expensive_decision",
            "evidence": root_analysis["most_expensive_decision"].get("execution_cost"),
        })
    if quality.get("evidence_quality", 1.0) < 0.6:
        candidates.append({
            "target": "evidence_extraction",
            "reason": "low_evidence_quality",
            "evidence": quality.get("evidence_quality"),
        })
    if _number(performance_report.get("reasoning_time_seconds"), 0.0) > 0:
        candidates.append({
            "target": "reasoning_decision_pipeline",
            "reason": "reasoning_time_measured",
            "evidence": performance_report.get("reasoning_time_seconds"),
        })
    return candidates


def _decision_tree(task_reports):
    return {
        "name": "Solver Reasoning",
        "children": [
            report["decision_tree"]
            for report in task_reports
        ],
    }


def _task_decision_tree(task_id, decisions):
    return {
        "name": task_id,
        "children": [
            {
                "name": decision["decision_name"],
                "decision_id": decision["decision_id"],
                "confidence": decision["confidence"],
                "reason": decision["reason"],
            }
            for decision in decisions
        ],
    }


def _decision_patterns(task_reports):
    counter = Counter(
        decision["decision_name"]
        for report in task_reports
        for decision in report["decision_timeline"]
    )
    return [
        {"pattern": name, "reuse_count": count}
        for name, count in counter.items()
    ]


def _validation_patterns(task_reports):
    counter = Counter(
        str(report["outcome"].get("success_state", "unknown"))
        for report in task_reports
    )
    return [
        {"validation_pattern": name, "count": count}
        for name, count in counter.items()
    ]


def _transformation_sequences(task_reports):
    sequences = []
    for report in task_reports:
        sequence = [
            item.get("transformation")
            for item in report["transformation_decisions"]
            if item.get("transformation")
        ]
        if sequence:
            sequences.append({
                "task_id": report["task_id"],
                "sequence": sequence,
            })
    return sequences


def _node(task_id, node_type, local_id, label, confidence=0.0, payload=None):
    return {
        "node_id": f"{task_id}:reasoning:{node_type.lower()}:{local_id}",
        "node_type": node_type,
        "label": label,
        "confidence": round(_number(confidence), 4),
        "payload": payload or {},
    }


def _edge(source, target, relationship):
    return {
        "from": source["node_id"],
        "to": target["node_id"],
        "relationship": relationship,
    }


def _outcome(context):
    evaluation = context.get("evaluation_result", {})
    evaluation = evaluation if isinstance(evaluation, Mapping) else {}
    return {
        "success": bool(evaluation.get("success", False)),
        "success_state": evaluation.get("success_state"),
        "confidence": _number(
            evaluation.get("accuracy"),
            _number(evaluation.get("final_score"), 0.0),
        ),
        "has_output": context.get("predicted_output") is not None,
        "validation_result": evaluation,
    }


def _capability_candidates(context):
    capabilities = []
    report = context.get("COGNITIVE_CAPABILITY_REPORT") or context.get(
        "cognitive_capability_report",
        {},
    )
    if isinstance(report, Mapping):
        for item in _list(report.get("capabilities_executed")):
            if isinstance(item, Mapping):
                capabilities.append(dict(item))
            else:
                capabilities.append({"capability": str(item)})
    tool_report = context.get("tool_selection_report", {})
    if isinstance(tool_report, Mapping):
        for tool in _list(tool_report.get("enabled_tools")):
            capabilities.append({
                "capability": str(tool),
                "activation_reason": tool_report.get("selection_reason", {}).get(tool)
                if isinstance(tool_report.get("selection_reason"), Mapping)
                else "enabled by tool selection report",
                "confidence": 0.65,
            })
    if not capabilities and context.get("patterns"):
        capabilities.append({
            "capability": "pattern_reasoning",
            "activation_reason": "patterns available in solver context",
            "confidence": 0.65,
        })
    return capabilities


def _transformation_attempts(context):
    report = context.get("transformation_report", {})
    trace = []
    if isinstance(report, Mapping):
        trace.extend(_list(report.get("execution_trace")))
        sandbox = report.get("sandbox_execution", {})
        if isinstance(sandbox, Mapping):
            trace.extend(_list(sandbox.get("simulation_trace")))
    trace.extend(_list(context.get("transformation_execution_trace")))
    attempts = []
    for item in trace:
        item = item if isinstance(item, Mapping) else {"operation": str(item)}
        status = str(item.get("status", "")).lower()
        success = status in {"success", "completed", "executed", "simulated"}
        attempts.append({
            "transformation_type": item.get("operation")
            or item.get("primitive")
            or item.get("type")
            or "unknown",
            "input": item.get("input") or item.get("parameters", {}),
            "confidence": _number(item.get("confidence"), 0.0),
            "success": success,
            "failure_reason": item.get("failure_reason")
            or (None if success else item.get("status", "not_successful")),
            "validation_result": item.get("validation_result", item.get("status")),
            "execution_cost": _number(item.get("execution_cost"), 0.0),
        })
    return attempts


def _hypothesis_key(hypothesis):
    if not isinstance(hypothesis, Mapping):
        return None
    return str(
        hypothesis.get("id")
        or hypothesis.get("type")
        or hypothesis.get("primitive")
        or hypothesis.get("semantic_class")
        or ""
    )


def _hypothesis_creation_reason(hypothesis):
    if not isinstance(hypothesis, Mapping):
        return "unknown"
    if hypothesis.get("geometric_grounding"):
        return "generated from geometric grounding evidence"
    if hypothesis.get("semantic_class"):
        return "generated from semantic class evidence"
    if hypothesis.get("primitive"):
        return "generated from executable primitive candidate"
    return "generated by solver hypothesis search"


def _hypothesis_evidence(hypothesis):
    if not isinstance(hypothesis, Mapping):
        return []
    evidence = []
    for key in (
        "geometric_grounding",
        "semantic_support",
        "causal_support",
        "world_model_fit",
        "residual_reduction",
        "explanatory_power",
    ):
        if hypothesis.get(key) is not None:
            evidence.append({key: hypothesis.get(key)})
    return evidence


def _hypothesis_capabilities(hypothesis, context):
    capabilities = []
    text = str(hypothesis).lower()
    if "color" in text:
        capabilities.append("color_mapping")
    if "spatial" in text or "position" in text:
        capabilities.append("spatial_reasoning")
    if "causal" in text:
        capabilities.append("causal_validation")
    if not capabilities and context.get("patterns"):
        capabilities.append("pattern_reasoning")
    return capabilities


def _hypothesis_validation_history(hypothesis, context):
    evaluation = context.get("evaluation_result", {})
    evaluation = evaluation if isinstance(evaluation, Mapping) else {}
    return [{
        "validation": "evaluation_result",
        "accuracy": evaluation.get("accuracy"),
        "success": evaluation.get("success"),
        "success_state": evaluation.get("success_state"),
    }] if evaluation else []


def _evidence_label(value, kind):
    if isinstance(value, Mapping):
        name = value.get(kind) or value.get("type") or value.get("rule") or value.get("pattern")
        return f"{kind.title()} evidence: {name}."
    return f"{kind.title()} evidence: {value}."


def _activation_reason(name, context):
    lowered = str(name).lower()
    if "color" in lowered and context.get("rules"):
        return "color evidence was present in rule analysis"
    if "dependency" in lowered:
        return "dependency reasoning was enabled for solver grounding"
    if "causal" in lowered:
        return "causal validation was available for transformation support"
    if "object" in lowered:
        return "object summaries were available"
    return "capability matched solver context"


def _winner_reason(winner):
    if not winner:
        return "No explicit winning hypothesis was available."
    return (
        f"Hypothesis {winner.get('hypothesis_key')} won because it had the "
        "strongest observed support among retained hypotheses."
    )


def _capability_reason(decisions):
    if not decisions:
        return "No explicit capability decision was available."
    return "Capabilities were selected because their activation reasons matched extracted solver evidence."


def _transformation_reason(decisions):
    if not decisions:
        return "No explicit transformation decision was available."
    return "Transformation was selected from executable candidates supported by the winning hypothesis."


def _program_reason(decisions):
    if not decisions:
        return "No explicit program decision was available."
    return "Program was accepted from the synthesized plan and ranked hypothesis winner."


def _solution_reason(context):
    evaluation = context.get("evaluation_result", {})
    if isinstance(evaluation, Mapping) and evaluation.get("success"):
        return "Final output was accepted because validation succeeded."
    if context.get("predicted_output") is not None:
        return "Final output was emitted as the best available prediction after validation."
    return "No final output was emitted."


def _decision_cost(name, context):
    timings = context.get("performance_report", {}).get("module_timings", [])
    if not isinstance(timings, list):
        return 0.0
    mapping = {
        "hypothesis_selection": "inference",
        "capability_selection": "capability",
        "transformation_selection": "transformation",
        "program_selection": "inference",
        "solution_decision": "evaluation",
    }
    needle = mapping.get(name, "")
    return round(sum(
        _number(item.get("seconds"), 0.0)
        for item in timings
        if isinstance(item, Mapping) and needle in str(item.get("module", ""))
    ), 6)


def _program_execution_cost(context):
    return _decision_cost("program_selection", context)


def _validation_confidence(context):
    evaluation = context.get("evaluation_result", {})
    if not isinstance(evaluation, Mapping):
        return 0.0
    return _number(evaluation.get("accuracy"), _number(evaluation.get("final_score"), 0.0))


def _decision_timestamp(context):
    for key in ("inference_stage_report", "evaluation_stage_report", "timestamp"):
        value = context.get(key)
        if isinstance(value, Mapping) and value.get("timestamp"):
            return value.get("timestamp")
        if isinstance(value, str):
            return value
    return None


def _sort_decisions(decisions):
    return sorted(
        decisions,
        key=lambda item: str(item.get("timestamp") or "") + str(item.get("decision_id") or ""),
    )


def _validation_score(validation):
    if isinstance(validation, Mapping):
        return _number(validation.get("accuracy"), _number(validation.get("final_score"), 0.0))
    if isinstance(validation, list):
        return _average([
            _validation_score(item)
            for item in validation
        ])
    return 0.0


def _list(value):
    return value if isinstance(value, list) else []


def _unique(values):
    seen = set()
    output = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output


def _number(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _average(values):
    values = [_number(value, 0.0) for value in values]
    return sum(values) / max(len(values), 1)


def _variance(values):
    values = [_number(value, 0.0) for value in values]
    if not values:
        return 0.0
    avg = _average(values)
    return min(1.0, sum((value - avg) ** 2 for value in values) / len(values))

