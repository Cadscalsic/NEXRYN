def build_training_report(
    training_batch=None,
    training_assistant_report=None,
    multi_task_results=None,
    ledger_report=None,
    concept_lifecycle_report=None,
    curriculum_coverage_report=None,
    include_truth_evaluations=False,
    report_level="normal",
):
    discovery_only_mode = not include_truth_evaluations
    report_level = str(report_level or "normal").lower()
    training_batch = training_batch or {}
    training_assistant_report = training_assistant_report or {}
    multi_task_results = list(multi_task_results or [])
    ledger_report = ledger_report or {}
    concept_lifecycle_report = concept_lifecycle_report or {}
    curriculum_coverage_report = curriculum_coverage_report or {}

    def candidate_metric(evaluation, metric_name):
        return next(
            (
                metric
                for metric in evaluation.get("metrics", [])
                if metric.get("metric") == metric_name
            ),
            {},
        )

    def average(values):
        numbers = []
        for value in values:
            try:
                numbers.append(float(value))
            except Exception:
                continue
        if not numbers:
            return None
        return round(sum(numbers) / len(numbers), 4)

    def build_architecture_bottleneck_report(
        causal_reports,
        context_reports,
        semantic_reports,
        contextual_reports,
        candidate_evaluations=None,
    ):
        candidate_evaluations = candidate_evaluations or {}

        def safe_float(value, default=0.0):
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        def safe_int(value, default=0):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        def explanation_path_from(report):
            explanation_path = report.get("explanation_path")
            if explanation_path:
                return explanation_path

            dependency_explanation = report.get(
                "dependency_explanation",
                {},
            )
            if isinstance(dependency_explanation, dict):
                return dependency_explanation.get("explanation_path", [])

            return []

        def resolved_dependency_chain_from(report):
            for key in (
                "resolved_dependency_chain",
                "chain",
                "dependencies",
            ):
                chain = report.get(key)
                if isinstance(chain, list):
                    return list(chain)
            return []

        def dependency_telemetry_from_report(concept, report, source):
            report = report if isinstance(report, dict) else {}
            if not report:
                return None

            concept = (
                concept
                or report.get("concept")
                or report.get("process_family")
            )
            if not concept:
                return None

            links_loaded = safe_int(
                report.get("process_dependency_links_loaded"),
            )
            links_used = safe_int(
                report.get("process_dependency_links_used"),
            )
            chain_depth = safe_int(
                report.get("dependency_chain_depth"),
            )
            coverage = safe_float(
                report.get("dependency_chain_coverage"),
            )
            coherence = safe_float(
                report.get(
                    "dependency_coherence_average",
                    report.get(
                        "dependency_coherence",
                        report.get("dependency_confidence"),
                    ),
                ),
            )
            explanation_quality = safe_float(
                report.get(
                    "dependency_explanation_quality",
                    report.get("explanation_quality"),
                ),
            )
            resolved_dependency_chain = resolved_dependency_chain_from(report)

            if (
                links_loaded <= 0
                and links_used <= 0
                and chain_depth <= 0
                and coverage <= 0.0
                and coherence <= 0.0
            ):
                return None

            return {
                "concept": str(concept),
                "source": source,
                "links_loaded": links_loaded,
                "links_used": links_used,
                "chain_depth": chain_depth,
                "coverage": round(coverage, 4),
                "coherence": round(coherence, 4),
                "dependency_explanation_quality":
                round(explanation_quality, 4),
                "explanation_path": explanation_path_from(report),
                "resolved_dependency_chain": resolved_dependency_chain,
                "reasoned_dependency_chain": bool(
                    report.get("reasoned_dependency_chain")
                    or resolved_dependency_chain
                    or report.get("dependency_graph")
                ),
            }

        def collect_dependency_telemetry():
            telemetry = {}

            def add(concept, report, source):
                item = dependency_telemetry_from_report(
                    concept,
                    report,
                    source,
                )
                if item is None:
                    return

                existing = telemetry.get(item["concept"])
                if existing is None:
                    telemetry[item["concept"]] = item
                    return

                telemetry[item["concept"]] = {
                    **existing,
                    **{
                        key: max(existing.get(key, 0), item.get(key, 0))
                        for key in [
                            "links_loaded",
                            "links_used",
                            "chain_depth",
                            "coverage",
                            "coherence",
                            "dependency_explanation_quality",
                        ]
                    },
                    "source": (
                        existing.get("source")
                        if existing.get("links_used", 0)
                        >= item.get("links_used", 0)
                        else item.get("source")
                    ),
                    "explanation_path": (
                        existing.get("explanation_path")
                        or item.get("explanation_path", [])
                    ),
                    "resolved_dependency_chain": (
                        existing.get("resolved_dependency_chain")
                        or item.get("resolved_dependency_chain", [])
                    ),
                    "reasoned_dependency_chain": (
                        existing.get("reasoned_dependency_chain", False)
                        or item.get("reasoned_dependency_chain", False)
                    ),
                }

            for item in multi_task_results:
                result = item.get("result", {})
                if not isinstance(result, dict):
                    continue

                add(
                    None,
                    result.get("process_dependency_memory", {}),
                    "runtime.process_dependency_memory",
                )

                for concept, report in result.get(
                    "process_dependency_chains",
                    {},
                ).items():
                    add(
                        concept,
                        report,
                        "runtime.process_dependency_chains",
                    )

                for trace in result.get("dependency_execution_trace", []):
                    if not isinstance(trace, dict):
                        continue
                    add(
                        trace.get("concept"),
                        {
                            "concept": trace.get("concept"),
                            "process_dependency_links_loaded":
                            trace.get("process_dependency_links_loaded"),
                            "process_dependency_links_used":
                            trace.get("process_dependency_links_used"),
                            "dependency_chain_depth":
                            trace.get("dependency_chain_depth"),
                            "dependency_chain_coverage":
                            trace.get("dependency_chain_coverage"),
                        },
                        "runtime.dependency_execution_trace",
                    )

                for evaluation in result.get(
                    "epistemic_cognition_report",
                    {},
                ).get("evaluations", []):
                    add(
                        evaluation.get("concept"),
                        evaluation.get("process_dependency_memory", {}),
                        "epistemic_evaluation.process_dependency_memory",
                    )

            return list(telemetry.values())

        dependency_telemetry_report = collect_dependency_telemetry()

        def collect_dependency_lifecycle():
            states = []
            times = []
            executions = []
            for item in multi_task_results:
                result = item.get("result", {})
                if not isinstance(result, dict):
                    continue
                enabled_tools = set(result.get("enabled_tools", []) or [])
                tool_selection_report = result.get("tool_selection_report", {})
                if isinstance(tool_selection_report, dict):
                    enabled_tools.update(
                        tool_selection_report.get("enabled_tools", []) or []
                    )
                runtime_tool_requests = result.get("runtime_tool_requests", {})
                dependency_request = (
                    runtime_tool_requests.get("dependency_reasoning", {})
                    if isinstance(runtime_tool_requests, dict)
                    else {}
                )
                if (
                    "dependency_reasoning" in enabled_tools
                    or dependency_request.get("request_state") == "REQUESTED"
                ):
                    states.append("REQUESTED")
                for key in (
                    "dependency_lifecycle_report",
                    "dependency_reasoning_report",
                    "performance_report",
                    "PERFORMANCE_REPORT",
                ):
                    report = result.get(key, {})
                    if not isinstance(report, dict):
                        continue
                    state = (
                        report.get("dependency_activation_state")
                        or report.get("dependency_lifecycle_state")
                    )
                    if state:
                        states.append(str(state).upper())
                    time_value = report.get(
                        "dependency_time",
                        report.get(
                            "dependency_reasoning_time",
                            report.get("dependency_reasoning_time_seconds"),
                        ),
                    )
                    if time_value is not None:
                        times.append(safe_float(time_value))
                    executed = report.get("dependency_chains_executed")
                    if executed is not None:
                        executions.append(safe_int(executed))
            precedence = [
                "COMPLETED",
                "EXECUTING",
                "ACTIVATED",
                "FAILED",
                "SKIPPED",
                "REQUESTED",
                "NOT_REQUESTED",
            ]
            state = next(
                (
                    candidate
                    for candidate in precedence
                    if candidate in states
                ),
                "NOT_REQUESTED",
            )
            return {
                "dependency_activation_state": state,
                "dependency_reasoning_time": round(max(times or [0.0]), 4),
                "dependency_chains_executed": max(executions or [0]),
            }

        dependency_lifecycle = collect_dependency_lifecycle()

        try:
            from core.dependency import (
                DependencyReasoningOperator,
                ProcessDependencyMemory,
                ProcessDependencyGraph,
            )

            dependency_reasoning_operator_available = (
                DependencyReasoningOperator is not None
            )

            process_dependency_memory = (
                ProcessDependencyMemory(
                    seed_defaults=True,
                )
            )

            process_dependency_graph = (
                ProcessDependencyGraph(
                    process_dependency_memory=process_dependency_memory,
                )
            )

            process_dependency_memory_available = (
                process_dependency_memory.links_loaded > 0
            )

        except Exception:
            process_dependency_graph = None
            dependency_reasoning_operator_available = False
            process_dependency_memory_available = False

        process_concepts = {
            "growth",
            "propagation",
            "replication",
            "topological_growth",
            "identity_persistence",
            "identity_forking",
            "directional_motion",
        }
        process_concepts_in_boundary_refinement = [
            item.get("concept")
            for item in concept_lifecycle_report.get("concepts", [])
            if item.get("concept") in process_concepts
            and item.get("state") == "BOUNDARY_REFINEMENT"
        ]
        boundary_refinement_dependency_debug = []
        if process_dependency_graph is not None:
            boundary_refinement_dependency_debug = [
                process_dependency_graph.resolve_dependency_chain(concept)
                for concept in process_concepts_in_boundary_refinement
            ]
        process_dependency_links_loaded = (
            process_dependency_graph.process_dependency_memory.links_loaded
            if process_dependency_graph is not None
            else 0
        )
        runtime_links_loaded = max(
            [
                safe_int(item.get("links_loaded"))
                for item in dependency_telemetry_report
            ]
            or [0]
        )
        process_dependency_links_loaded = max(
            process_dependency_links_loaded,
            runtime_links_loaded,
        )
        process_dependency_links_used = sum(
            int(item.get("process_dependency_links_used", 0) or 0)
            for item in boundary_refinement_dependency_debug
        )
        runtime_links_used = sum(
            safe_int(item.get("links_used"))
            for item in dependency_telemetry_report
        )
        process_dependency_links_used = max(
            process_dependency_links_used,
            runtime_links_used,
        )
        chain_depths = [
            int(item.get("dependency_chain_depth", 0) or 0)
            for item in boundary_refinement_dependency_debug
        ]
        chain_depths.extend(
            safe_int(item.get("chain_depth"))
            for item in dependency_telemetry_report
        )
        chain_coverages = [
            float(item.get("dependency_chain_coverage", 0.0) or 0.0)
            for item in boundary_refinement_dependency_debug
        ]
        chain_coverages.extend(
            safe_float(item.get("coverage"))
            for item in dependency_telemetry_report
            if safe_float(item.get("coverage")) > 0.0
        )
        debug_by_concept = {
            item.get("concept"): dict(item)
            for item in boundary_refinement_dependency_debug
        }
        for telemetry in dependency_telemetry_report:
            concept = telemetry.get("concept")
            if not concept:
                continue
            telemetry_debug = {
                "concept": concept,
                "process_dependency_links_loaded":
                telemetry.get("links_loaded", 0),
                "process_dependency_links_used":
                telemetry.get("links_used", 0),
                "dependency_chain_depth":
                telemetry.get("chain_depth", 0),
                "dependency_chain_coverage":
                telemetry.get("coverage", 0.0),
                "dependency_confidence":
                telemetry.get("coherence", 0.0),
                "dependency_coherence_average":
                telemetry.get("coherence", 0.0),
                "dependency_explanation_quality":
                telemetry.get("dependency_explanation_quality", 0.0),
                "explanation_path":
                telemetry.get("explanation_path", []),
                "resolved_dependency_chain":
                telemetry.get("resolved_dependency_chain", []),
                "reasoned_dependency_chain":
                telemetry.get("reasoned_dependency_chain", False),
                "source": telemetry.get("source"),
            }
            existing = debug_by_concept.get(concept)
            if existing is None:
                debug_by_concept[concept] = telemetry_debug
                continue

            telemetry_is_richer = (
                telemetry_debug.get("dependency_chain_depth", 0)
                > int(existing.get("dependency_chain_depth", 0) or 0)
                or (
                    not existing.get("resolved_dependency_chain")
                    and telemetry_debug.get("resolved_dependency_chain")
                )
                or (
                    not existing.get("reasoned_dependency_chain")
                    and telemetry_debug.get("reasoned_dependency_chain")
                )
            )
            if telemetry_is_richer:
                debug_by_concept[concept] = {
                    **existing,
                    **telemetry_debug,
                    "missing_dependencies": existing.get(
                        "missing_dependencies",
                        [],
                    ),
                }
            else:
                debug_by_concept[concept] = {
                    **existing,
                    "process_dependency_links_loaded": max(
                        int(
                            existing.get(
                                "process_dependency_links_loaded",
                                0,
                            )
                            or 0
                        ),
                        telemetry_debug[
                            "process_dependency_links_loaded"
                        ],
                    ),
                    "process_dependency_links_used": max(
                        int(
                            existing.get(
                                "process_dependency_links_used",
                                0,
                            )
                            or 0
                        ),
                        telemetry_debug["process_dependency_links_used"],
                    ),
                    "dependency_chain_coverage": max(
                        float(
                            existing.get(
                                "dependency_chain_coverage",
                                0.0,
                            )
                            or 0.0
                        ),
                        telemetry_debug["dependency_chain_coverage"],
                    ),
                    "dependency_explanation_quality": max(
                        float(
                            existing.get(
                                "dependency_explanation_quality",
                                0.0,
                            )
                            or 0.0
                        ),
                        telemetry_debug["dependency_explanation_quality"],
                    ),
                }
        boundary_refinement_dependency_debug = list(
            debug_by_concept.values()
        )
        dependency_promotion_blocker_names = {
            "dependency_confidence_below_promotion_floor",
            "dependency_chain_depth_below_promotion_floor",
            "dependency_chain_missing_dependencies",
        }

        def dependency_ready(dependency_debug):
            return (
                float(
                    dependency_debug.get("dependency_confidence", 0.0)
                    or 0.0
                ) > 0.85
                and dependency_debug.get("missing_dependencies", []) == []
                and int(
                    dependency_debug.get("dependency_chain_depth", 0)
                    or 0
                ) >= 4
            )

        def promotion_from_dependency_debug(dependency_debug):
            dependency_confidence = float(
                dependency_debug.get("dependency_confidence", 0.0) or 0.0
            )
            dependency_coverage = float(
                dependency_debug.get("dependency_chain_coverage", 0.0) or 0.0
            )
            dependency_depth = int(
                dependency_debug.get("dependency_chain_depth", 0) or 0
            )
            depth_score = min(dependency_depth / 5.0, 1.0)

            promotion_score = round(
                min(
                    dependency_confidence * 0.46
                    + dependency_coverage * 0.34
                    + depth_score * 0.20,
                    1.0,
                ),
                4,
            )

            return {
                "promotion_dependency_score": promotion_score,
                "promotion_dependency_bonus": (
                    round(min((promotion_score - 0.80) * 0.25, 0.08), 4)
                    if promotion_score > 0.80
                    else 0.0
                ),
                "dependency_confidence": dependency_confidence,
                "dependency_chain_depth": dependency_depth,
                "dependency_chain_coverage": dependency_coverage,
                "missing_dependencies":
                list(dependency_debug.get("missing_dependencies", [])),
            }

        def reconcile_dependency_promotion(promotion, dependency_debug):
            promotion = dict(promotion or {})
            dependency_metrics = promotion_from_dependency_debug(
                dependency_debug,
            )
            promotion.update({
                key: (
                    promotion.get(key)
                    if promotion.get(key) not in [None, 0, 0.0, []]
                    else value
                )
                for key, value in dependency_metrics.items()
            })

            if dependency_ready(dependency_debug):
                promotion.update(dependency_metrics)
                blockers = [
                    blocker
                    for blocker in promotion.get(
                        "dependency_promotion_blockers",
                        [],
                    )
                    if blocker not in dependency_promotion_blocker_names
                ]
                promotion["dependency_promotion_blockers"] = blockers
                promotion[
                    "dependency_promotion_metrics_source"
                ] = "process_dependency_memory"

            return promotion

        dependency_ready_boundary_refinement_blockers = []
        for item in concept_lifecycle_report.get("concepts", []):
            concept = item.get("concept")
            if item.get("state") != "BOUNDARY_REFINEMENT":
                continue
            dependency_debug = debug_by_concept.get(concept, {})
            if not dependency_ready(dependency_debug):
                continue
            promotion = candidate_evaluations.get(
                concept,
                item.get("truth_candidate_promotion", {}),
            )

            if not promotion:
                promotion = {
                    "stage_eligible_for_truth_candidate": None,
                    "eligible_for_truth_candidate": None,
                    "blocked_metrics": [],
                    "eligibility_reason": "computed_from_dependency_debug",
                    "dependency_promotion_blockers": [],
                }

            promotion = reconcile_dependency_promotion(
                promotion,
                dependency_debug,
            )

            blockers = list(
                promotion.get(
                    "dependency_promotion_blockers",
                    promotion.get("failed_gates", []),
                )
            )

            if not blockers:
                blockers = [
                    f"promotion_gate_blocked:{gate}"
                    for gate in promotion.get("failed_gates", [])
                ]

            dependency_ready_boundary_refinement_blockers.append({
                "concept": concept,
                "dependency_confidence":
                dependency_debug.get("dependency_confidence"),
                "dependency_chain_depth":
                dependency_debug.get("dependency_chain_depth"),
                "dependency_chain_coverage":
                dependency_debug.get("dependency_chain_coverage"),
                "missing_dependencies":
                dependency_debug.get("missing_dependencies", []),
                "candidate_ready":
                item.get("preliminary_truth_candidate_ready", False),
                "state": item.get("state"),
                "exact_blocker": blockers,
                "promotion_dependency_score":
                promotion.get("promotion_dependency_score"),
                "promotion_dependency_bonus":
                promotion.get("promotion_dependency_bonus"),
                "stage_eligible_for_truth_candidate":
                promotion.get("stage_eligible_for_truth_candidate"),
                "eligible_for_truth_candidate":
                promotion.get("eligible_for_truth_candidate"),
                "blocked_metrics":
                promotion.get("blocked_metrics", []),
                "eligibility_reason":
                promotion.get("eligibility_reason"),
                "dependency_promotion_metrics_source":
                promotion.get("dependency_promotion_metrics_source"),
            })

        causal_values = list(causal_reports.values())
        raw_dependency_average = average(
            item.get("dependency_coherence")
            for item in causal_values
        )
        dependency_evidence_values = [
            item.get("dependency_coherence")
            for item in causal_values
        ]
        process_dependency_evidence_sources = []

        def typed_dependency_evidence_from_debug(concept, dependency_debug):
            dependency_debug = (
                dependency_debug
                if isinstance(dependency_debug, dict)
                else {}
            )
            typed_relations = dependency_debug.get(
                "typed_dependency_relations",
                [],
            )
            if not typed_relations:
                return None
            try:
                relation_score = float(
                    dependency_debug.get("relation_semantics_score", 0.0)
                    or 0.0
                )
                dependency_confidence = float(
                    dependency_debug.get("dependency_confidence", 0.0)
                    or 0.0
                )
                dependency_chain_depth = int(
                    dependency_debug.get("dependency_chain_depth", 0)
                    or 0
                )
                dependency_chain_coverage = float(
                    dependency_debug.get("dependency_chain_coverage", 0.0)
                    or 0.0
                )
            except (TypeError, ValueError):
                return None
            missing_dependencies = list(
                dependency_debug.get("missing_dependencies", [])
            )
            if (
                dependency_confidence <= 0.85
                or dependency_chain_depth < 4
                or dependency_chain_coverage < 0.70
                or missing_dependencies
                or relation_score <= 0.0
            ):
                return None
            depth_score = min(dependency_chain_depth / 5.0, 1.0)
            semantic_dependency_score = min(
                dependency_confidence * 0.36
                + dependency_chain_coverage * 0.24
                + depth_score * 0.14
                + relation_score * 0.26,
                1.0,
            )
            return {
                "concept": concept,
                "source": "typed_process_dependency_memory_relations",
                "semantic_dependency_score":
                round(semantic_dependency_score, 4),
                "relation_semantics_score": round(relation_score, 4),
                "typed_dependency_relation_count": len(typed_relations),
                "dependency_confidence": round(dependency_confidence, 4),
                "dependency_chain_depth": dependency_chain_depth,
                "dependency_chain_coverage":
                round(dependency_chain_coverage, 4),
            }

        for concept in process_concepts_in_boundary_refinement:
            typed_evidence = typed_dependency_evidence_from_debug(
                concept,
                debug_by_concept.get(concept, {}),
            )
            if typed_evidence is None:
                continue
            dependency_evidence_values.append(
                typed_evidence["semantic_dependency_score"]
            )
            process_dependency_evidence_sources.append(typed_evidence)

        for concept, evaluation in candidate_evaluations.items():
            if concept not in process_concepts:
                continue
            dependency_confidence = evaluation.get("dependency_confidence")
            dependency_chain_depth = evaluation.get("dependency_chain_depth")
            dependency_chain_coverage = evaluation.get(
                "dependency_chain_coverage",
            )
            missing_dependencies = evaluation.get("missing_dependencies", [])
            try:
                dependency_confidence = float(dependency_confidence)
                dependency_chain_depth = int(dependency_chain_depth)
                dependency_chain_coverage = float(dependency_chain_coverage)
            except (TypeError, ValueError):
                continue
            if (
                dependency_confidence <= 0.85
                or dependency_chain_depth < 4
                or missing_dependencies
            ):
                continue
            promotion_score = evaluation.get("promotion_dependency_score")
            try:
                promotion_score = float(promotion_score)
            except (TypeError, ValueError):
                depth_score = min(dependency_chain_depth / 5.0, 1.0)
                promotion_score = min(
                    dependency_confidence * 0.46
                    + dependency_chain_coverage * 0.34
                    + depth_score * 0.20,
                    1.0,
                )
            dependency_evidence_values.append(promotion_score)
            process_dependency_evidence_sources.append({
                "concept": concept,
                "source": "typed_process_dependency_memory",
                "promotion_dependency_score": round(promotion_score, 4),
                "dependency_confidence": round(dependency_confidence, 4),
                "dependency_chain_depth": dependency_chain_depth,
                "dependency_chain_coverage":
                round(dependency_chain_coverage, 4),
            })
        for telemetry in dependency_telemetry_report:
            if (
                telemetry.get("coherence", 0.0) < 0.80
                or telemetry.get("links_used", 0) <= 0
                or telemetry.get("chain_depth", 0) <= 0
                or telemetry.get("coverage", 0.0) <= 0.0
            ):
                continue
            dependency_evidence_values.append(telemetry["coherence"])
            process_dependency_evidence_sources.append({
                "concept": telemetry["concept"],
                "source": "dependency_execution_telemetry",
                "dependency_coherence_average":
                telemetry["coherence"],
                "process_dependency_links_loaded":
                telemetry["links_loaded"],
                "process_dependency_links_used":
                telemetry["links_used"],
                "dependency_chain_depth":
                telemetry["chain_depth"],
                "dependency_chain_coverage":
                telemetry["coverage"],
                "dependency_explanation_quality":
                telemetry["dependency_explanation_quality"],
            })
        dependency_average = average(dependency_evidence_values)
        promotion_candidates = []
        for evaluation in candidate_evaluations.values():
            try:
                promotion_dependency_score = float(
                    evaluation.get("promotion_dependency_score")
                )
            except (TypeError, ValueError):
                continue
            promotion_candidates.append((
                promotion_dependency_score,
                evaluation,
            ))
        strongest_promotion = (
            max(promotion_candidates, key=lambda item: item[0])[1]
            if promotion_candidates
            else {}
        )
        validation_average = average(
            item.get("validation_score")
            for item in causal_values
        )
        stability_average = average(
            item.get("cross_task_stability")
            for item in causal_values
        )
        context_consistency_average = average(
            item.get("context_consistency")
            for item in causal_values
        )
        identity_average = average(
            item.get("identity_compatibility")
            for item in causal_values
        )

        governance_reports = [
            evaluation.get("context_governance_report", {})
            for evaluation in candidate_evaluations.values()
            if isinstance(
                evaluation.get("context_governance_report", {}),
                dict,
            )
            and evaluation.get("context_governance_report", {})
        ]
        governance_visible_context_ids = sorted({
            context_id
            for report in governance_reports
            for context_id in report.get("visible_context_ids", [])
        })
        governance_runtime_context_count = max(
            [
                int(report.get("runtime_context_count", 0) or 0)
                for report in governance_reports
            ]
            or [0]
        )
        governance_context_count = (
            len(governance_visible_context_ids)
            if governance_reports
            else 0
        )
        context_registration_gap = (
            max(governance_runtime_context_count - governance_context_count, 0)
            if governance_reports
            else None
        )
        registration_coverage = (
            round(
                governance_context_count / governance_runtime_context_count,
                4,
            )
            if governance_reports and governance_runtime_context_count
            else 1.0
            if governance_reports
            else None
        )
        context_count = (
            governance_context_count
            if governance_reports
            else len(context_reports)
        )
        semantic_context_count = len(semantic_reports)
        contextual_truth_count = len(contextual_reports)
        context_surface_established = (
            context_count > 0
            and semantic_context_count > 0
            and contextual_truth_count > 0
        )
        evidence_saturated = (
            stability_average is not None
            and stability_average >= 0.90
            and context_consistency_average is not None
            and context_consistency_average >= 0.90
            and identity_average is not None
            and identity_average >= 0.90
        )
        dependency_plateau = (
            dependency_average is not None
            and 0.55 <= dependency_average < 0.75
        )
        architecture_bottleneck = (
            dependency_plateau
            and evidence_saturated
            and context_surface_established
        )

        if architecture_bottleneck:
            bottleneck_type = "ARCHITECTURE_BOTTLENECK"
            recommended_next_step = (
                "ingest_process_dependency_memory"
                if process_dependency_memory_available
                and process_concepts_in_boundary_refinement
                else "ingest_reasoned_dependency_chains"
                if dependency_reasoning_operator_available
                else "add_dependency_reasoning_operator"
            )
            diagnosis = (
                "Evidence and contexts are stable, but dependency "
                "coherence is plateaued below the truth-grade threshold. "
                + (
                    "Process dependency memory is available; ingest typed "
                    "process relations for boundary-refinement concepts next."
                    if process_dependency_memory_available
                    and process_concepts_in_boundary_refinement
                    else
                    "The dependency reasoning operator is available; "
                    "ingest explicit truth-to-truth dependency chains next."
                    if dependency_reasoning_operator_available
                    else "A dependency reasoning operator is still needed."
                )
            )
        elif dependency_plateau:
            bottleneck_type = "DEPENDENCY_EVIDENCE_GAP"
            recommended_next_step = "collect_targeted_dependency_evidence"
            diagnosis = (
                "Dependency coherence is below threshold, but the report "
                "does not yet show saturated contextual support."
            )
        else:
            bottleneck_type = "NO_ARCHITECTURE_BOTTLENECK_DETECTED"
            recommended_next_step = "continue_adaptive_training"
            diagnosis = (
                "The current report does not show a dependency-coherence "
                "plateau with saturated context evidence."
            )

        return {
            "system": "architecture_bottleneck_analyzer",
            "bottleneck_type": bottleneck_type,
            "architecture_bottleneck": architecture_bottleneck,
            "diagnosis": diagnosis,
            "dependency_coherence_average": dependency_average,
            "raw_dependency_coherence_average": raw_dependency_average,
            "effective_dependency_evidence_average": dependency_average,
            "process_dependency_evidence_sources":
            process_dependency_evidence_sources,
            "causal_validation_average": validation_average,
            "cross_task_stability_average": stability_average,
            "context_consistency_average": context_consistency_average,
            "identity_compatibility_average": identity_average,
            "context_count": context_count,
            "raw_runtime_context_count": len(context_reports),
            "governance_context_count": governance_context_count,
            "governance_visible_contexts": governance_visible_context_ids,
            "context_registration_gap": context_registration_gap,
            "registration_coverage": registration_coverage,
            "semantic_context_count": semantic_context_count,
            "contextual_truth_count": contextual_truth_count,
            "dependency_reasoning_operator_available":
            dependency_reasoning_operator_available,
            "process_dependency_memory_available":
            process_dependency_memory_available,
            "process_concepts_in_boundary_refinement":
            process_concepts_in_boundary_refinement,
            "process_dependency_links_loaded":
            process_dependency_links_loaded,
            "process_dependency_links_used":
            process_dependency_links_used,
            "dependency_chains_executed":
            dependency_lifecycle["dependency_chains_executed"],
            "dependency_reasoning_time":
            dependency_lifecycle["dependency_reasoning_time"],
            "dependency_activation_state":
            dependency_lifecycle["dependency_activation_state"],
            "dependency_chain_depth": (
                max(chain_depths)
                if chain_depths
                else 0
            ),
            "dependency_chain_coverage": (
                round(sum(chain_coverages) / len(chain_coverages), 4)
                if chain_coverages
                else 0.0
            ),
            "dependency_explanation_quality": (
                max(
                    item.get("dependency_explanation_quality", 0.0)
                    for item in dependency_telemetry_report
                )
                if dependency_telemetry_report
                else 0.0
            ),
            "dependency_telemetry_report":
            dependency_telemetry_report,
            "boundary_refinement_dependency_debug":
            boundary_refinement_dependency_debug,
            "dependency_ready_boundary_refinement_blockers":
            dependency_ready_boundary_refinement_blockers,
            "evidence_saturated": evidence_saturated,
            "candidate_ready":
            strongest_promotion.get("candidate_ready"),
            "promotion_score":
            strongest_promotion.get("promotion_score"),
            "promotion_dependency_score":
            strongest_promotion.get("promotion_dependency_score"),
            "promotion_dependency_bonus":
            strongest_promotion.get("promotion_dependency_bonus"),
            "eligible_for_truth_candidate":
            strongest_promotion.get("eligible_for_truth_candidate"),
            "stage_eligible_for_truth_candidate":
            strongest_promotion.get("stage_eligible_for_truth_candidate"),
            "blocked_metrics":
            strongest_promotion.get("blocked_metrics"),
            "eligibility_reason":
            strongest_promotion.get("eligibility_reason"),
            "dependency_plateau": dependency_plateau,
            "recommended_next_step": recommended_next_step,
            "why": [
                "context surface is already established"
                if context_surface_established
                else "context surface still needs evidence",
                "cross-task, context, and identity signals are saturated"
                if evidence_saturated
                else "support signals are not yet saturated",
                "dependency coherence is below truth-grade threshold"
                if dependency_plateau
                else "dependency coherence is not plateaued",
                "dependency reasoning operator is available"
                if dependency_reasoning_operator_available
                else "dependency reasoning operator is not available",
                "process dependency memory is available"
                if process_dependency_memory_available
                else "process dependency memory is not available",
                "process concepts remain in boundary refinement"
                if process_concepts_in_boundary_refinement
                else "no process-concept boundary plateau detected",
            ],
            "anti_pattern": (
                "Repeating more tasks is unlikely to resolve this without "
                + (
                    "ingesting typed process dependency memory."
                    if process_dependency_memory_available
                    and process_concepts_in_boundary_refinement
                    else "ingesting explicit dependency reasoning chains."
                    if dependency_reasoning_operator_available
                    else "a new dependency reasoning mechanism."
                )
                if architecture_bottleneck
                else None
            ),
        }

    lifecycle_by_concept = {
        item.get("concept"): item
        for item in concept_lifecycle_report.get("concepts", [])
        if item.get("concept")
    }

    def average_contradiction_for_concept(concept):
        concept_name = str(concept.get("concept", ""))
        lifecycle = lifecycle_by_concept.get(concept_name, {})
        for source in (concept, lifecycle):
            for key in (
                "ledger_average_contradiction_score",
                "average_contradiction_score",
                "contradiction_score",
            ):
                if source.get(key) is not None:
                    try:
                        return round(float(source.get(key)), 4)
                    except (TypeError, ValueError):
                        return 0.0
        records = [
            record
            for record in concept.get("records", [])
            if isinstance(record, dict)
        ]
        if not records:
            return 0.0
        total = 0.0
        for record in records:
            if record.get("contradiction_score") is not None:
                total += float(record.get("contradiction_score") or 0.0)
            elif record.get("success") is False:
                total += 1.0
        return round(total / len(records), 4)

    concept_memory = {}
    for concept in ledger_report.get("concepts", []):
        concept_name = concept.get("concept")
        if not concept_name:
            continue
        ledger_average_contradiction = average_contradiction_for_concept(
            concept,
        )
        concept_memory[str(concept_name)] = {
            "used_task_count": concept.get("used_task_count", 0),
            "task_ids": list(concept.get("used_task_ids", [])),
            "independent_success_rate":
            concept.get("independent_success_rate", 0.0),
            "lifecycle_state":
            "DISCOVERING",
            "preliminary_truth_candidate_ready":
            False,
            "ledger_average_contradiction_score":
            ledger_average_contradiction,
            "average_contradiction_score":
            ledger_average_contradiction,
        }

    task_results = [
        {
            "task": item.get("task"),
            "status": item.get("status"),
            **(
                {"error": item.get("error")}
                if item.get("error")
                else {}
            ),
        }
        for item in multi_task_results
    ]
    projection_guard = {
        "report_level": report_level,
        "multi_task_results_projected": True,
        "raw_task_result_payloads_omitted": True,
        "max_task_result_fields": 3,
    }

    def aggregate_execution_layer_audit_report():
        audits = []
        for item in multi_task_results:
            result = item.get("result", {})
            if not isinstance(result, dict):
                continue
            audit = (
                result.get("EXECUTION_LAYER_AUDIT_REPORT")
                or result.get("execution_layer_audit_report")
            )
            if not isinstance(audit, dict):
                continue
            audits.append({
                **audit,
                "task": item.get("task"),
                "status": item.get("status"),
            })

        def union_list(key):
            values = []
            for audit in audits:
                values.extend(audit.get(key, []) or [])
            normalized = []
            for value in values:
                try:
                    hash(value)
                    normalized.append(value)
                except TypeError:
                    normalized.append(str(value))
            return sorted(set(normalized))

        def concat_list(key):
            values = []
            for audit in audits:
                entries = audit.get(key, []) or []
                if isinstance(entries, list):
                    values.extend(
                        entry
                        for entry in entries
                        if not (
                            isinstance(entry, dict)
                            and entry.get("recursive_context_reference") is True
                        )
                    )
            return values

        dependency_selected = any(
            audit.get("dependency_tool_selected") is True
            for audit in audits
        )
        dependency_request_created = any(
            audit.get("dependency_activation_request_created") is True
            for audit in audits
        )
        process_selected = any(
            audit.get("process_tool_selected") is True
            for audit in audits
        )
        process_stage_created = any(
            audit.get("process_stage_created") is True
            for audit in audits
        )
        causal_selected = any(
            audit.get("causal_tool_selected") is True
            for audit in audits
        )
        causal_stage_created = any(
            audit.get("causal_stage_created") is True
            for audit in audits
        )
        silent_drop = any(
            audit.get("silent_drop_detected") is True
            for audit in audits
        )
        suspected_breakpoints = [
            audit.get("suspected_breakpoint")
            for audit in audits
            if audit.get("suspected_breakpoint")
            and audit.get("suspected_breakpoint") != "none_detected"
        ]
        raw_budget_blocks = concat_list("budget_blocks")
        selective_blocks = concat_list("selective_execution_blocks")
        def to_int(value):
            try:
                return int(value or 0)
            except (TypeError, ValueError):
                return 0

        active_routes = max(
            [to_int(audit.get("active_routes")) for audit in audits] or [0]
        )
        execution_nodes = max(
            [to_int(audit.get("execution_nodes")) for audit in audits] or [0]
        )
        selected_tools_union = union_list("selected_tools")
        enabled_layers_union = union_list("enabled_layers")
        disabled_layers_union = union_list("disabled_layers")
        deferred_layers_union = union_list("deferred_layers")
        missing_execution_nodes = union_list("missing_execution_nodes")
        layer_aliases = {
            "dependency_reasoning": "dependency_reasoning",
            "process_semantics": "process_semantic_synthesis",
            "causal_validation": "causal_validation",
            "truth_governance": "truth_candidate",
            "identity_governance": "deep_governance",
            "object_tracking": "object_detection",
            "spatial_reasoning": "inference",
            "color_mapping": "transformation_solver",
        }
        route_to_node_mapping = {
            tool: {
                "mapped_layer": layer_aliases.get(tool),
                "layer_enabled": layer_aliases.get(tool) in set(enabled_layers_union),
                "execution_node": None
                if tool in missing_execution_nodes
                else "runtime_activity_node",
                "execution_node_created": tool not in missing_execution_nodes,
            }
            for tool in selected_tools_union
        }
        pruned_routes = [
            {
                "route": route,
                "mapped_layer": layer_aliases.get(route),
                "reason": None,
                "pruned_without_reason": active_routes > execution_nodes,
            }
            for route in missing_execution_nodes
        ]
        budget_blocks = []
        if raw_budget_blocks:
            if process_selected and not process_stage_created:
                budget_blocks.append({
                    "tool": "process_semantics",
                    "state": "BLOCKED_BY_BUDGET",
                    "reason": "process_semantics_enabled=False",
                })
            if dependency_selected and not dependency_request_created:
                budget_blocks.append({
                    "tool": "dependency_reasoning",
                    "state": "BLOCKED_BY_BUDGET",
                    "reason": "dependency_budget_block_reported",
                })
        suspected_breakpoint = (
            suspected_breakpoints[0]
            if suspected_breakpoints
            else "none_detected"
        )
        recommended_next_fix = (
            "surface_budget_block_before_runtime_execution"
            if budget_blocks
            else "surface_selective_execution_block_before_runtime_execution"
            if selective_blocks
            else "add_intent_compiler_from_selected_tools_to_runtime_tool_requests"
            if suspected_breakpoint == "tool_selection_to_execution_plan"
            else "add_stage_compiler_or_explicit_non_stage_diagnostic_for_selected_tools"
            if suspected_breakpoint == "tool_selection_to_runtime_stage"
            else "map_active_routes_to_execution_nodes_or_record_prune_reasons"
            if suspected_breakpoint == "route_to_execution_node_compilation"
            else "no_execution_layer_drop_detected"
        )

        dependency_states = [
            audit.get("dependency_activation_state")
            for audit in audits
            if audit.get("dependency_activation_state")
        ]
        return {
            "system": "execution_layer_audit",
            "report_state": "final",
            "EXECUTION_LAYER_AUDIT_REPORT": True,
            "selected_tools": selected_tools_union,
            "enabled_layers": enabled_layers_union,
            "disabled_layers": disabled_layers_union,
            "deferred_layers": deferred_layers_union,
            "active_routes": active_routes,
            "execution_nodes": execution_nodes,
            "route_to_node_mapping": route_to_node_mapping,
            "pruned_routes": pruned_routes,
            "missing_execution_nodes": missing_execution_nodes,
            "dependency_tool_selected": dependency_selected,
            "dependency_activation_request_created":
            dependency_request_created,
            "dependency_activation_state": (
                dependency_states[0] if dependency_states else "NOT_REQUESTED"
            ),
            "process_tool_selected": process_selected,
            "process_stage_created": process_stage_created,
            "causal_tool_selected": causal_selected,
            "causal_stage_created": causal_stage_created,
            "budget_blocks": budget_blocks,
            "selective_execution_blocks": selective_blocks,
            "silent_drop_detected": silent_drop,
            "suspected_breakpoint": suspected_breakpoint,
            "recommended_next_fix": recommended_next_fix,
            "per_task_report_count": len(audits),
        }

    def aggregate_execution_plan_report():
        reports = []
        canonical_plans = []
        for item in multi_task_results:
            result = item.get("result", {})
            if not isinstance(result, dict):
                continue
            canonical_plan = (
                result.get("canonical_execution_plan")
                or result.get("CANONICAL_EXECUTION_PLAN_REPORT")
            )
            if isinstance(canonical_plan, dict):
                canonical_plans.append({
                    "task": item.get("task"),
                    "status": item.get("status"),
                    "plan": canonical_plan,
                })
            report = (
                result.get("EXECUTION_PLAN_REPORT")
                or result.get("execution_plan_report")
            )
            if isinstance(report, dict):
                reports.append(report)

        def plan_sort_key(item):
            plan = item["plan"]
            return (
                0 if plan.get("execution_plan_validation_state") == "VALID" else 1,
                0 if plan.get("execution_plan_finalized") is True else 1,
                str(item.get("task") or ""),
                str(plan.get("execution_plan_id") or ""),
            )

        selected_plan_record = (
            sorted(canonical_plans, key=plan_sort_key)[0]
            if canonical_plans
            else None
        )
        if selected_plan_record is not None:
            selected_plan = dict(selected_plan_record["plan"])
            return {
                "system": "execution_planner",
                "report_state": "final",
                "EXECUTION_PLAN_REPORT": True,
                "execution_plan_schema_version": selected_plan.get(
                    "execution_plan_schema_version"
                ),
                "execution_plan_id": selected_plan.get("execution_plan_id"),
                "execution_plan_state": selected_plan.get("planning_state"),
                "execution_plan_finalized": selected_plan.get(
                    "execution_plan_finalized"
                ),
                "execution_plan_immutable": selected_plan.get(
                    "execution_plan_immutable"
                ),
                "execution_plan_forwarded": selected_plan.get(
                    "execution_plan_forwarded"
                ),
                "selected_tool_count": selected_plan.get("selected_tool_count", 0),
                "reconciled_tool_count": len(
                    selected_plan.get("tool_reconciliation", []) or []
                ),
                "selected_layer_count": selected_plan.get("selected_layer_count", 0),
                "reconciled_layer_count": len(
                    selected_plan.get("layer_reconciliation", []) or []
                ),
                "active_route_count": selected_plan.get("active_route_count", 0),
                "reconciled_route_count": len(
                    selected_plan.get("route_reconciliation", []) or []
                ),
                "execution_node_count": selected_plan.get("execution_node_count", 0),
                "dependency_activation_request_count": len(
                    selected_plan.get("dependency_activation_requests", []) or []
                ),
                "process_stage_request_count": len(
                    selected_plan.get("process_stage_requests", []) or []
                ),
                "unresolved_selected_item_count": selected_plan.get(
                    "unresolved_selected_item_count",
                    0,
                ),
                "execution_plan_reconciliation_state": selected_plan.get(
                    "execution_plan_reconciliation_state"
                ),
                "execution_plan_validation_state": selected_plan.get(
                    "execution_plan_validation_state"
                ),
                "execution_plan_failure_cause": selected_plan.get(
                    "execution_plan_failure_cause"
                ),
                "dependency_activation_state": selected_plan.get(
                    "dependency_activation_state",
                    "NOT_REQUESTED",
                ),
                "process_stage_state": selected_plan.get(
                    "process_stage_state",
                    "NOT_REQUESTED",
                ),
                "RUNTIME_BUDGET_ENFORCEMENT_REPORT": selected_plan.get(
                    "RUNTIME_BUDGET_ENFORCEMENT_REPORT",
                    selected_plan.get("runtime_budget_enforcement_report", {}),
                ),
                "runtime_budget_enforcement_report": selected_plan.get(
                    "runtime_budget_enforcement_report",
                    selected_plan.get("RUNTIME_BUDGET_ENFORCEMENT_REPORT", {}),
                ),
                "canonical_execution_plan": selected_plan,
                "CANONICAL_EXECUTION_PLAN_REPORT": selected_plan,
                "batch_plan_propagation_state": "CANONICAL_PLAN_PROPAGATED",
                "batch_plan_source_task": selected_plan_record.get("task"),
                "batch_task_plan_count": len(canonical_plans),
                "batch_task_report_count": len(reports),
            }

        def to_int(value, default=0):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        def to_float(value, default=0.0):
            try:
                return float(value)
            except (TypeError, ValueError):
                return default

        def union_list(key):
            values = []
            for report in reports:
                entries = report.get(key, []) or []
                if isinstance(entries, list):
                    values.extend(entries)
            normalized = []
            for value in values:
                try:
                    hash(value)
                    normalized.append(value)
                except TypeError:
                    normalized.append(str(value))
            return sorted(set(normalized))

        def concat_nodes(key):
            nodes = []
            for report in reports:
                entries = report.get(key, []) or []
                if isinstance(entries, list):
                    nodes.extend(
                        node
                        for node in entries
                        if not (
                            isinstance(node, dict)
                            and node.get("recursive_context_reference") is True
                        )
                    )
            return nodes

        selected_tools_union = union_list("selected_tools")
        stage_map = {
            "dependency_reasoning": "dependency_execution",
            "process_semantics": "process_semantic_execution",
            "causal_validation": "causal_validation_execution",
            "truth_governance": "truth_governance_execution",
            "identity_governance": "identity_governance_execution",
            "object_tracking": "object_tracking_execution",
            "color_mapping": "color_mapping_execution",
            "spatial_reasoning": "spatial_reasoning_execution",
            "contradiction_checks": "contradiction_check_execution",
        }
        raw_blocked = concat_nodes("blocked_nodes")
        blocked_tools = {
            node.get("originating_tool")
            for node in raw_blocked
            if isinstance(node, dict)
            and node.get("originating_tool")
        }
        raw_pruning = concat_nodes("pruning_log")
        pruning_by_tool = {
            item.get("tool"): item
            for item in raw_pruning
            if isinstance(item, dict)
            and item.get("tool")
        }
        all_nodes = []
        for index, tool in enumerate(selected_tools_union):
            status = "BLOCKED" if tool in blocked_tools else "PENDING"
            all_nodes.append({
                "node_id": f"aggregate_exec_{index + 1}_{tool}",
                "stage": stage_map.get(tool, f"{tool}_execution"),
                "originating_tool": tool,
                "originating_concept": None,
                "activation_reason": "aggregated_from_task_execution_plans",
                "status": status,
                "parent_node": (
                    f"aggregate_exec_{index}_{selected_tools_union[index - 1]}"
                    if index > 0
                    else None
                ),
                "child_nodes": (
                    [f"aggregate_exec_{index + 2}_{selected_tools_union[index + 1]}"]
                    if index + 1 < len(selected_tools_union)
                    else []
                ),
            })

        def clone_node(node):
            return {
                **node,
                "child_nodes": list(node.get("child_nodes", []) or []),
            }

        generated_nodes = [
            clone_node(node)
            for node in all_nodes
            if node.get("status") != "BLOCKED"
        ]
        dependency_nodes = [
            clone_node(node) for node in all_nodes
            if node.get("originating_tool") == "dependency_reasoning"
        ]
        process_nodes = [
            clone_node(node) for node in all_nodes
            if node.get("originating_tool") == "process_semantics"
        ]
        causal_nodes = [
            clone_node(node) for node in all_nodes
            if node.get("originating_tool") == "causal_validation"
        ]
        blocked_nodes = [
            clone_node(node)
            for node in all_nodes if node.get("status") == "BLOCKED"
        ]
        deferred_nodes = []
        pruning_log = [
            {
                "tool": tool,
                "node_id": f"aggregate_exec_{selected_tools_union.index(tool) + 1}_{tool}",
                "decision": item.get("decision", "BLOCKED"),
                "reason": item.get("reason", "blocked_in_task_execution_plan"),
            }
            for tool, item in pruning_by_tool.items()
            if tool in selected_tools_union
        ]
        execution_order = [
            node.get("node_id")
            for node in generated_nodes
        ]
        active_routes = max(
            [
                to_int(report.get("active_routes"))
                for report in reports
            ] or [0]
        )
        execution_nodes = max(
            [
                to_int(report.get("execution_nodes"))
                for report in reports
            ] or [0]
        )
        confidences = [
            to_float(report.get("planner_confidence"))
            for report in reports
            if report.get("planner_confidence") is not None
        ]
        return {
            "system": "execution_planner",
            "report_state": "final",
            "EXECUTION_PLAN_REPORT": True,
            "batch_plan_propagation_state": (
                "PLAN_DROPPED_BY_BATCH_AGGREGATION"
                if reports
                else "PLAN_BUILDER_NOT_INVOKED"
            ),
            "execution_plan_state": "LEGACY_PLAN_UNAVAILABLE",
            "selected_tools": selected_tools_union,
            "attributed_concepts": union_list("attributed_concepts"),
            "generated_intents": [
                {
                    "tool": tool,
                    "reason": "aggregated_from_task_execution_plans",
                    "confidence": 0.75,
                    "priority": len(selected_tools_union) - index,
                    "estimated_cost": 1.0,
                    "required_budget": {},
                    "required_contexts": [],
                    "required_truths": [],
                    "dependencies": [],
                    "activation_state": (
                        "BLOCKED" if tool in blocked_tools else "REQUESTED"
                    ),
                }
                for index, tool in enumerate(selected_tools_union)
            ],
            "generated_execution_nodes": generated_nodes,
            "dependency_nodes": dependency_nodes,
            "process_nodes": process_nodes,
            "causal_nodes": causal_nodes,
            "blocked_nodes": blocked_nodes,
            "deferred_nodes": deferred_nodes,
            "pruning_log": pruning_log,
            "execution_order": list(dict.fromkeys(execution_order)),
            "active_routes": active_routes,
            "execution_nodes": execution_nodes,
            "planner_confidence": (
                round(sum(confidences) / len(confidences), 4)
                if confidences
                else 0.0
            ),
            "planner_summary": {
                "task_reports": len(reports),
                "nodes_generated": len(generated_nodes),
                "dependency_nodes": len(dependency_nodes),
                "process_nodes": len(process_nodes),
                "causal_nodes": len(causal_nodes),
                "blocked_nodes": len(blocked_nodes),
                "deferred_nodes": len(deferred_nodes),
            },
        }

    def aggregate_execution_dispatch_report():
        reports = []
        for item in multi_task_results:
            result = item.get("result", {})
            if not isinstance(result, dict):
                continue
            report = (
                result.get("EXECUTION_DISPATCH_REPORT")
                or result.get("execution_dispatch_report")
            )
            if isinstance(report, dict):
                reports.append(report)

        def to_int(value, default=0):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default

        def sum_key(key):
            return sum(to_int(report.get(key)) for report in reports)

        def any_key(key):
            return any(bool(report.get(key)) for report in reports)

        def concat_clean(key):
            items = []
            for report in reports:
                entries = report.get(key, []) or []
                if isinstance(entries, list):
                    for entry in entries:
                        if isinstance(entry, dict):
                            items.append({
                                item_key: item_value
                                for item_key, item_value in entry.items()
                                if item_key != "runtime_context"
                            })
                        else:
                            items.append(entry)
            return items

        block_reasons = {}
        for report in reports:
            reasons = report.get("block_reasons", {})
            if isinstance(reasons, dict):
                block_reasons.update(reasons)

        return {
            "system": "execution_dispatcher",
            "report_state": "final",
            "EXECUTION_DISPATCH_REPORT": True,
            "execution_plan_received": any_key("execution_plan_received"),
            "execution_nodes_received": sum_key("execution_nodes_received"),
            "nodes_ready": sum_key("nodes_ready"),
            "nodes_dispatched": sum_key("nodes_dispatched"),
            "nodes_completed": sum_key("nodes_completed"),
            "nodes_failed": sum_key("nodes_failed"),
            "nodes_blocked": sum_key("nodes_blocked"),
            "execution_nodes_completed": sum_key("execution_nodes_completed"),
            "dependency_nodes_dispatched":
            sum_key("dependency_nodes_dispatched"),
            "process_nodes_dispatched": sum_key("process_nodes_dispatched"),
            "causal_nodes_dispatched": sum_key("causal_nodes_dispatched"),
            "dependency_runtime_called":
            any_key("dependency_runtime_called"),
            "process_runtime_called": any_key("process_runtime_called"),
            "causal_runtime_called": any_key("causal_runtime_called"),
            "dependency_chains_executed":
            sum_key("dependency_chains_executed"),
            "process_context_count": sum_key("process_context_count"),
            "causal_context_count": sum_key("causal_context_count"),
            "execution_failures": concat_clean("execution_failures"),
            "block_reasons": block_reasons,
            "planned_nodes_after_dispatch": concat_clean(
                "planned_nodes_after_dispatch"
            ),
            "execution_summary": {
                "task_reports": len(reports),
                "completed": sum_key("nodes_completed"),
                "failed": sum_key("nodes_failed"),
                "blocked": sum_key("nodes_blocked"),
                "dependency_runtime_called":
                any_key("dependency_runtime_called"),
                "process_runtime_called": any_key("process_runtime_called"),
                "causal_runtime_called": any_key("causal_runtime_called"),
                "dependency_chains_executed":
                sum_key("dependency_chains_executed"),
                "process_context_count": sum_key("process_context_count"),
                "causal_context_count": sum_key("causal_context_count"),
            },
        }

    candidate_evaluations = {}
    truth_commit_evaluations = {}
    candidate_context_evaluations = {}

    def nested_score(report, paths, default=0.0):
        for path in paths:
            data = report if isinstance(report, dict) else {}
            for key in path:
                if not isinstance(data, dict):
                    data = None
                    break
                data = data.get(key)
            if data is not None:
                try:
                    return max(0.0, min(float(data), 1.0))
                except (TypeError, ValueError):
                    continue
        return default

    def context_strength_for_evaluation(evaluation):
        return max(
            nested_score(
                evaluation,
                [
                    ("contextual_truth_authority", "effective_contextual_truth"),
                    ("contextual_truth", "effective_contextual_truth"),
                    ("contextual_truth", "contextual_truth_score"),
                ],
            ),
            nested_score(
                evaluation,
                [
                    ("context_hierarchy", "context_hierarchy_score"),
                    ("context_hierarchy", "score"),
                ],
            ),
            nested_score(
                evaluation,
                [
                    ("semantic_context", "semantic_context_score"),
                    ("semantic_context", "confidence"),
                ],
            ),
        )

    def candidate_report_sources(result):
        reports = []

        def add_report(report, source):
            if isinstance(report, dict) and report:
                reports.append((report, source))

        add_report(
            result.get("truth_candidate_report", {}),
            "truth_candidate_report",
        )
        for cognition_key in (
            "epistemic_cognition_report",
            "epistemic_cognition_layer",
            "cognition_report",
        ):
            cognition_report = result.get(cognition_key, {})
            if not isinstance(cognition_report, dict):
                continue
            add_report(
                cognition_report.get("truth_candidate_engine", {}),
                f"{cognition_key}.truth_candidate_engine",
            )
        return reports

    def record_candidate_evaluation(evaluation, source):
        concept = evaluation.get("concept")
        if concept:
            candidate_context_evaluations[str(concept)] = evaluation
        if discovery_only_mode:
            return
        if not concept:
            return
        if evaluation.get("candidate_state") == "TRUTH_STATE_LOCKED":
            return
        contradiction_metric = candidate_metric(
            evaluation,
            "contradiction_score",
        )
        context_strength = context_strength_for_evaluation(evaluation)
        candidate_ready = evaluation.get(
            "candidate_ready",
            evaluation.get("eligible_for_truth_candidate", False),
        )
        candidate_ready = bool(candidate_ready)
        eligible = bool(
            evaluation.get("eligible_for_truth_candidate", candidate_ready)
        )
        stage_eligible = evaluation.get(
            "stage_eligible_for_truth_candidate",
            candidate_ready,
        )
        stage_eligible = bool(stage_eligible)
        promotion_score = evaluation.get("promotion_score")
        if promotion_score is None:
            promotion_score = context_strength
        candidate_evaluations[str(concept)] = {
            "concept": str(concept),
            "candidate_state": evaluation.get("candidate_state"),
            "candidate_ready": candidate_ready,
            "promotion_score": promotion_score,
            "eligible_for_truth_candidate": eligible,
            "stage_eligible_for_truth_candidate": stage_eligible,
            "eligibility_reason":
            evaluation.get("eligibility_reason"),
            "blocked_metrics": list(
                evaluation.get("blocked_metrics", [])
            ),
            "effective_contradiction_score":
            contradiction_metric.get(
                "current_value",
                evaluation.get("effective_contradiction_score"),
            ),
            "contradiction_threshold":
            contradiction_metric.get(
                "threshold",
                {},
            ).get(
                "required",
                evaluation.get("contradiction_threshold"),
            ),
            "contradiction_gap":
            contradiction_metric.get(
                "gap",
                evaluation.get("contradiction_gap"),
            ),
            "contradiction_metric_status":
            contradiction_metric.get("status"),
            "contradiction_review_required":
            evaluation.get(
                "contradiction_review_required",
                False,
            ),
            "contradiction_review_zone":
            evaluation.get("contradiction_review_zone"),
            "within_soft_review_zone":
            evaluation.get("within_soft_review_zone", False),
            "contradiction_review_severity":
            evaluation.get("contradiction_review_severity"),
            "contradiction_score_source":
            "truth_candidate_effective_runtime_aggregate",
            "promotion_dependency_score":
            evaluation.get("promotion_dependency_score"),
            "promotion_dependency_bonus":
            evaluation.get("promotion_dependency_bonus"),
            "dependency_promotion_blockers":
            list(evaluation.get("dependency_promotion_blockers", [])),
            "dependency_confidence":
            evaluation.get("dependency_confidence"),
            "dependency_chain_depth":
            evaluation.get("dependency_chain_depth"),
            "dependency_chain_coverage":
            evaluation.get("dependency_chain_coverage"),
            "missing_dependencies":
            list(evaluation.get("missing_dependencies", [])),
            "context_strength": context_strength,
            "context_strength_source": source,
            "causal_graph_alignment":
            evaluation.get("causal_graph_alignment", {}),
            "causal_explanation":
            evaluation.get("causal_explanation", {}),
            "causal_validation":
            evaluation.get("causal_validation", {}),
            "contextual_truth":
            evaluation.get("contextual_truth", {}),
            "contextual_truth_authority":
            evaluation.get("contextual_truth_authority", {}),
            "context_discovery":
            evaluation.get("context_discovery", {}),
            "context_governance_report":
            evaluation.get("context_governance_report", {}),
            "context_hierarchy":
            evaluation.get("context_hierarchy", {}),
            "semantic_context":
            evaluation.get("semantic_context", {}),
        }

    def record_lifecycle_candidate_promotion(item):
        concept = item.get("concept")
        promotion = item.get("truth_candidate_promotion", {})
        if not concept or not isinstance(promotion, dict) or not promotion:
            return

        concept = str(concept)
        memory = concept_memory.setdefault(
            concept,
            {
                "used_task_count": item.get("used_task_count", 0),
                "task_ids": list(item.get("task_ids", [])),
                "independent_success_rate":
                item.get("independent_success_rate", 0.0),
            },
        )
        context_candidate_ready = (
            promotion.get("context_candidate_ready") is True
        )
        memory.update({
            "lifecycle_state": item.get(
                "promotion_stage",
                item.get(
                    "state",
                    memory.get("lifecycle_state", "DISCOVERING"),
                ),
            ),
            "promotion_stage": item.get(
                "promotion_stage",
                item.get("state"),
            ),
            "promotion_score": item.get(
                "promotion_score",
                promotion.get("promotion_score"),
            ),
            "candidate_ready": item.get(
                "candidate_ready",
                item.get("preliminary_truth_candidate_ready", False),
            ),
            "preliminary_truth_candidate_ready":
            item.get("preliminary_truth_candidate_ready", False),
            "eligible_for_context": item.get(
                "eligible_for_context",
                promotion.get("eligible_for_context", False),
            ),
            "eligible_for_truth_candidate": item.get(
                "eligible_for_truth_candidate",
                promotion.get("eligible_for_truth_candidate", False),
            ),
            "blocked_metrics": list(
                item.get(
                    "blocked_metrics",
                    promotion.get("blocked_metrics", []),
                )
            ),
            "promotion_reason": item.get(
                "promotion_reason",
                promotion.get("promotion_reason"),
            ),
            "truth_candidate_promotion": promotion,
            "epistemic_graduation": item.get(
                "epistemic_graduation",
                promotion.get("epistemic_graduation", {}),
            ),
            "context_candidate_ready": context_candidate_ready,
            "promotion_dependency_score":
            promotion.get("promotion_dependency_score"),
            "promotion_dependency_bonus":
            promotion.get("promotion_dependency_bonus"),
            "dependency_confidence":
            promotion.get("dependency_confidence"),
            "dependency_chain_coverage":
            promotion.get("dependency_chain_coverage"),
        })
        candidate_ready = promotion.get(
            "candidate_ready",
            item.get("preliminary_truth_candidate_ready", False),
        )
        candidate_ready = bool(candidate_ready)
        promotion_score = promotion.get("promotion_score")
        if promotion_score is None:
            promotion_score = 1.0 if candidate_ready else 0.0
        target_evaluations = (
            candidate_context_evaluations
            if discovery_only_mode
            else candidate_evaluations
        )
        evaluation = target_evaluations.setdefault(
            concept,
            {
                "concept": concept,
                "candidate_state": item.get("state"),
                "candidate_ready": candidate_ready,
                "promotion_score": promotion_score,
                "eligible_for_truth_candidate": bool(
                    promotion.get(
                        "eligible_for_truth_candidate",
                        candidate_ready,
                    )
                ),
                "stage_eligible_for_truth_candidate": bool(
                    promotion.get(
                        "stage_eligible_for_truth_candidate",
                        candidate_ready,
                    )
                ),
                "blocked_metrics": [],
                "dependency_promotion_blockers": [],
                "missing_dependencies": [],
                "causal_graph_alignment": {},
                "causal_explanation": {},
                "causal_validation": {},
                "contextual_truth": {},
                "contextual_truth_authority": {},
                "context_discovery": {},
                "context_governance_report": {},
                "context_hierarchy": {},
                "semantic_context": {},
            },
        )
        lifecycle_values = {
            "candidate_ready": candidate_ready,
            "promotion_score": promotion_score,
            "eligible_for_truth_candidate": promotion.get(
                "eligible_for_truth_candidate",
                candidate_ready,
            ),
            "stage_eligible_for_truth_candidate": promotion.get(
                "stage_eligible_for_truth_candidate",
                candidate_ready,
            ),
            "eligibility_reason": promotion.get(
                "eligibility_reason",
                promotion.get("decision"),
            ),
            "blocked_metrics": list(
                promotion.get(
                    "blocked_metrics",
                    promotion.get("failed_gates", []),
                )
            ),
            "promotion_dependency_score":
            promotion.get("promotion_dependency_score"),
            "promotion_dependency_bonus":
            promotion.get("promotion_dependency_bonus"),
            "dependency_promotion_blockers": list(
                promotion.get("dependency_promotion_blockers", [])
            ),
            "dependency_confidence":
            promotion.get("dependency_confidence"),
            "dependency_chain_depth":
            promotion.get("dependency_chain_depth"),
            "dependency_chain_coverage":
            promotion.get("dependency_chain_coverage"),
            "missing_dependencies":
            list(promotion.get("missing_dependencies", [])),
        }
        for key, value in lifecycle_values.items():
            if evaluation.get(key) in (None, [], {}):
                evaluation[key] = value

    def build_concept_advancement_audit():
        def greater_than(value, threshold):
            try:
                return float(value) > float(threshold)
            except (TypeError, ValueError):
                return False

        audit = {}
        for concept, memory in concept_memory.items():
            lifecycle = lifecycle_by_concept.get(concept, {})
            promotion = memory.get("truth_candidate_promotion", {})
            graduation = (
                memory.get("epistemic_graduation")
                or promotion.get("epistemic_graduation", {})
                or lifecycle.get("epistemic_graduation", {})
            )
            thresholds = graduation.get("thresholds", {})
            blocked_metrics = list(
                memory.get(
                    "blocked_metrics",
                    graduation.get("blocked_metrics", []),
                )
                or []
            )
            promotion_score = memory.get(
                "promotion_score",
                graduation.get("promotion_score"),
            )
            current_stage = memory.get(
                "promotion_stage",
                memory.get("lifecycle_state", "DISCOVERING"),
            )
            contradiction = memory.get(
                "ledger_average_contradiction_score",
                memory.get(
                    "average_contradiction_score",
                    graduation.get("contradiction_rate"),
                ),
            )
            contradiction_required = thresholds.get(
                "maximum_contradiction_rate",
                0.10,
            )
            next_required_evidence = list(
                graduation.get("next_required_evidence", [])
            )
            missing_promotion_score = promotion_score is None
            missing_graduation = not bool(graduation)
            context_block = (
                "context_support" in blocked_metrics
                or "context_strength" in blocked_metrics
                or current_stage not in {
                    "PROCESS_CONTEXT",
                    "TRUTH_CANDIDATE",
                    "ESTABLISHED_TRUTH",
                }
                and memory.get("eligible_for_context") is not True
            )
            audit[concept] = {
                "concept": concept,
                "observations": memory.get("used_task_count", 0),
                "confidence": memory.get("independent_success_rate", 0.0),
                "current_stage": current_stage,
                "next_stage": graduation.get("next_stage"),
                "candidate_ready": memory.get(
                    "candidate_ready",
                    memory.get("preliminary_truth_candidate_ready", False),
                ),
                "promotion_score": promotion_score,
                "promotion_score_required_next": (
                    next_required_evidence[0].get("required")
                    if next_required_evidence
                    and next_required_evidence[0].get("metric")
                    == "promotion_score"
                    else None
                ),
                "eligible_for_context":
                memory.get("eligible_for_context", False),
                "eligible_for_truth_candidate":
                memory.get("eligible_for_truth_candidate", False),
                "blocked_by": blocked_metrics,
                "missing_promotion_score": missing_promotion_score,
                "missing_epistemic_graduation": missing_graduation,
                "contradiction_block": (
                    "contradiction_rate" in blocked_metrics
                    or greater_than(contradiction, contradiction_required)
                ),
                "contradiction_current": contradiction,
                "contradiction_required": f"<= {contradiction_required}",
                "saturation_block": (
                    "observations" in blocked_metrics
                    or "cross_task_validation" in blocked_metrics
                ),
                "observation_saturation": thresholds.get(
                    "observation_saturation",
                    32,
                ),
                "plateau_block": any(
                    metric in blocked_metrics
                    for metric in [
                        "cross_task_stability",
                        "causal_support",
                        "dependency_confidence",
                    ]
                ),
                "context_block": context_block,
                "dependency_confidence":
                memory.get("dependency_confidence"),
                "dependency_chain_coverage":
                memory.get("dependency_chain_coverage"),
                "next_required_evidence": next_required_evidence,
                "promotion_reason": memory.get(
                    "promotion_reason",
                    graduation.get("promotion_reason"),
                ),
            }
        return audit

    for item in multi_task_results:
        result = item.get("result", {})
        for report, source in candidate_report_sources(result):
            for evaluation in report.get("evaluations", []):
                record_candidate_evaluation(evaluation, source)
        for cognition_report in (
            result.get("epistemic_cognition_report", {}),
            result.get("epistemic_cognition_layer", {}),
            result.get("cognition_report", {}),
        ):
            if not isinstance(cognition_report, dict):
                continue
            for evaluation in cognition_report.get("evaluations", []):
                if discovery_only_mode:
                    continue
                concept = evaluation.get("concept")
                if not concept:
                    continue
                truth_commit = evaluation.get("truth_commit", {})
                identity_integration = evaluation.get(
                    "identity_safe_truth_integration",
                    {},
                )
                identity_runtime = evaluation.get(
                    "identity_runtime_report",
                    {},
                )
                semantic_spine_recovery = evaluation.get(
                    "semantic_spine_recovery",
                    {},
                )
                final_commit = truth_commit.get(
                    "metadata",
                    {},
                ).get(
                    "final_commit_decision",
                    {},
                )
                if (
                    final_commit.get("final_commit_state")
                    == "LOCKED_TRUTH_REVIEW_REQUIRED"
                ):
                    continue
                truth_commit_evaluations[str(concept)] = {
                    "concept": str(concept),
                    "decision": truth_commit.get("decision"),
                    "reason": truth_commit.get("reason"),
                    "failed_gates": list(
                        final_commit.get(
                            "effective_failed_gates",
                            truth_commit.get("reasons", []),
                        )
                    ),
                    "final_commit_state":
                    final_commit.get("final_commit_state"),
                    "forbid_automatic_truth_revocation":
                    final_commit.get(
                        "forbid_automatic_truth_revocation",
                        False,
                    ),
                    "revocation_severity":
                    final_commit.get("revocation_severity"),
                    "revocation_grace_period":
                    final_commit.get("revocation_grace_period"),
                    "revocation_grace_period_active":
                    final_commit.get(
                        "revocation_grace_period_active",
                        False,
                    ),
                    "low_risk_review_streak":
                    final_commit.get("low_risk_review_streak", 0),
                    "preventive_review_observation":
                    final_commit.get(
                        "preventive_review_observation",
                        False,
                    ),
                    "identity_governance_state":
                    truth_commit.get(
                        "metadata",
                        {},
                    ).get("identity_governance_state"),
                    "failed_identity_governance_gates": list(
                        truth_commit.get(
                            "metadata",
                            {},
                        ).get("failed_identity_governance_gates", [])
                    ),
                    "identity_integration_state":
                    identity_integration.get("integration_state"),
                    "identity_runtime_state":
                    identity_runtime.get("runtime_state"),
                    "identity_runtime_ready":
                    identity_runtime.get("runtime_ready"),
                    "identity_runtime_continuity":
                    identity_runtime.get("identity_continuity"),
                    "identity_runtime_split":
                    identity_runtime.get("identity_split"),
                    "identity_runtime_merged":
                    identity_runtime.get("identity_merged"),
                    "identity_failed_checks": list(
                        identity_integration.get("failed_checks", [])
                    ),
                    "recovery_state":
                    semantic_spine_recovery.get("recovery_state"),
                    "recovery_streak":
                    semantic_spine_recovery.get("recovery_streak", 0),
                    "remaining_recovery_cycles":
                    semantic_spine_recovery.get(
                        "remaining_recovery_cycles",
                    ),
                    "rehearsal_validation_pending":
                    semantic_spine_recovery.get(
                        "rehearsal_validation_pending",
                        False,
                    ),
                    "recovery_blocker_type":
                    semantic_spine_recovery.get("recovery_blocker_type"),
                    "recovery_failed_checks": list(
                        semantic_spine_recovery.get("failed_checks", [])
                    ),
                    "causal_graph_alignment":
                    truth_commit.get(
                        "metadata",
                        {},
                    ).get("causal_graph_alignment", {}),
                    "causal_explanation":
                    truth_commit.get(
                        "metadata",
                        {},
                    ).get("causal_explanation", {}),
                    "causal_validation":
                    truth_commit.get(
                        "metadata",
                        {},
                    ).get("causal_validation", {}),
                    "contextual_truth":
                    truth_commit.get(
                        "metadata",
                        {},
                    ).get("contextual_truth", {}),
                    "contextual_truth_authority":
                    truth_commit.get(
                        "metadata",
                        {},
                    ).get("contextual_truth_authority", {}),
                    "context_hierarchy":
                    truth_commit.get(
                        "metadata",
                        {},
                    ).get("context_hierarchy", {}),
                    "semantic_context":
                    truth_commit.get(
                        "metadata",
                        {},
                    ).get("semantic_context", {}),
                    "stable_truth_why_chain":
                    truth_commit.get(
                        "metadata",
                        {},
                    ).get("causal_explanation", {}).get("why", []),
                    "stable_truth_how_we_know":
                    truth_commit.get(
                        "metadata",
                        {},
                    ).get("causal_validation", {}).get("how_we_know", []),
                    "stable_truth_when_valid":
                    truth_commit.get(
                        "metadata",
                        {},
                    ).get("contextual_truth", {}).get("when_valid", []),
                    "stable_truth_when_invalid":
                    truth_commit.get(
                        "metadata",
                        {},
                    ).get("contextual_truth", {}).get("when_invalid", []),
                }

    for item in concept_lifecycle_report.get("concepts", []):
        record_lifecycle_candidate_promotion(item)

    def cognition_reports(result):
        for key in (
            "epistemic_cognition_report",
            "epistemic_cognition_layer",
            "cognition_report",
        ):
            report = result.get(key, {})
            if isinstance(report, dict):
                yield report

    causal_validation_reports = {}
    for item in multi_task_results:
        result = item.get("result", {})
        for cognition_report in cognition_reports(result):
            for evaluation in cognition_report.get(
                "causal_validation_engine",
                {},
            ).get("evaluations", []):
                hypothesis = evaluation.get("hypothesis", {})
                concept = hypothesis.get("target_concept")
                if concept:
                    causal_validation_reports[str(concept)] = evaluation
    contextual_truth_reports = {}
    context_discovery_reports = {}
    context_hierarchy_reports = {}
    semantic_context_reports = {}

    def structured_context(value, fallback_name="", report=None):
        from runtime.context.context_serialization_engine import normalize_context

        normalized = normalize_context(value or fallback_name)
        if report and isinstance(report, dict):
            context_id = (
                normalized.get("context_id")
                or normalized.get("context_name")
                or fallback_name
            )
            context_type = normalized.get("context_type")
            if context_type in {None, "TEXT_CONTEXT"}:
                context_type = report.get("context_type", "SEMANTIC_CONTEXT")
            normalized = {
                **normalized,
                "context_id": context_id,
                "context_name": normalized.get("context_name", context_id),
                "concept": normalized.get("concept", report.get("concept")),
                "context_type": context_type,
                "context_strength": normalized.get(
                    "context_strength",
                    report.get(
                        "context_confidence",
                        report.get("confidence"),
                    ),
                ),
            }
        return normalized

    def semantic_report_payload(report, context_name, score=None):
        confidence = report.get("confidence", report.get("context_confidence", score))
        return {
            **report,
            "context": structured_context(
                report.get("context", context_name),
                context_name,
                report,
            ),
            "context_name": report.get("context_name", context_name),
            "semantic_context_score": report.get(
                "semantic_context_score",
                report.get("context_confidence", score),
            ),
            "confidence": confidence,
        }

    def record_process_context_report(report):
        if not isinstance(report, dict):
            return
        concept = report.get("concept")
        context_name = (
            report.get("context_name")
            or report.get("semantic_context")
            or report.get("process_context")
            or report.get("generated_context")
        )
        key = str(concept or context_name or "")
        if not key:
            return

        if (
            report.get("system") == "process_context_discovery_engine"
            or "transition_family" in report
            or "expected_outcomes" in report
        ):
            context_discovery_reports.setdefault(key, report)

        if (
            report.get("system") == "process_semantic_context_engine"
            or report.get("process_context_synthesis")
            or report.get("semantic_context")
        ):
            semantic_context_reports.setdefault(
                str(context_name or key),
                semantic_report_payload(report, context_name or key),
            )

        governance_report = report.get("context_governance_report", {})
        if isinstance(governance_report, dict) and governance_report:
            context_hierarchy_reports.setdefault(
                str(context_name or key),
                {
                    "system": "context_governance_registry",
                    "contexts": [{
                        "context_name": context_name or key,
                    }],
                    "context_hierarchy_score":
                    governance_report.get("registration_coverage"),
                    "hierarchy_ready":
                    governance_report.get("registration_coverage", 0) > 0,
                    "context_governance_report": governance_report,
                },
            )

    def collect_process_context_reports(value):
        if isinstance(value, dict):
            if value.get("system") in {
                "process_context_discovery_engine",
                "process_semantic_context_engine",
            }:
                record_process_context_report(value)
            for key in (
                "process_context_discovery_report",
                "process_context_report",
                "process_context_engine_report",
                "temporal_process_context_report",
                "process_semantic_context_report",
            ):
                nested = value.get(key)
                if isinstance(nested, dict):
                    record_process_context_report(nested)
            for nested in value.values():
                collect_process_context_reports(nested)
        elif isinstance(value, list):
            for nested in value:
                collect_process_context_reports(nested)

    def record_lifecycle_generated_context(context):
        from runtime.utils.normalization import normalize_context_object

        context = normalize_context_object(context)
        if not isinstance(context, dict):
            return
        concept = str(
            context.get("concept")
            or context.get("context_name")
            or context.get("context_id")
            or ""
        )
        if not concept:
            return
        context_name = (
            context.get("context_name")
            or context.get("context_id")
            or concept
        )
        context_type = str(context.get("context_type", "")).upper()
        confidence = context.get(
            "confidence",
            context.get("context_confidence"),
        )
        if context_type == "PROCESS_CONTEXT":
            context_discovery_reports.setdefault(
                concept,
                {
                    **context,
                    "system": "lifecycle_process_context_generation",
                    "transition_family": context.get("transitions", []),
                    "confidence": confidence,
                },
            )
        elif context_type == "SEMANTIC_CONTEXT":
            semantic_context_reports.setdefault(
                str(context_name),
                semantic_report_payload(
                    {
                        **context,
                        "system": "lifecycle_semantic_context_generation",
                    },
                    context_name,
                    confidence,
                ),
            )
        elif context_type == "DEPENDENCY_SURFACE":
            context_hierarchy_reports.setdefault(
                str(context_name),
                {
                    **context,
                    "system": "lifecycle_dependency_surface_generation",
                    "context_hierarchy_score": confidence,
                    "hierarchy_ready": True,
                },
            )

    lifecycle_contexts = list(
        concept_lifecycle_report.get("generated_contexts", [])
    )
    for concept in concept_lifecycle_report.get("concepts", []):
        lifecycle_contexts.extend(
            concept.get("context_artifacts", {}).get("contexts", [])
        )
    for context in lifecycle_contexts:
        record_lifecycle_generated_context(context)

    def context_score_from_discovery(report):
        confidence = report.get(
            "context_strength",
            report.get(
                "process_context_strength",
                report.get(
                    "context_confidence",
                    report.get("confidence"),
                ),
            ),
        )
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        transition_count = len(report.get("transition_family", []) or [])
        if transition_count == 0:
            transition_count = len(report.get("transitions", []) or [])
        precondition_count = len(report.get("preconditions", []) or [])
        outcome_count = len(report.get("expected_outcomes", []) or [])
        if outcome_count == 0:
            outcome_count = len(report.get("outcomes", []) or [])

        structural_score = min(
            1.0,
            0.48
            + min(transition_count, 2) * 0.14
            + min(precondition_count, 2) * 0.12
            + min(outcome_count, 2) * 0.10,
        )
        return round(max(0.0, min(max(confidence, structural_score), 1.0)), 4)

    def synthesize_context_consumption_scores():
        target_evaluations = (
            candidate_context_evaluations
            if discovery_only_mode
            else candidate_evaluations
        )

        def fill_missing(target, source):
            if not isinstance(target, dict):
                return source
            if not isinstance(source, dict):
                return target
            for key, value in source.items():
                if target.get(key) is None or target.get(key) in ({}, []):
                    target[key] = value
            return target

        def report_for_concept(reports, concept):
            for key, report in reports.items():
                if (
                    isinstance(report, dict)
                    and (
                        str(key) == concept
                        or str(report.get("concept", "")) == concept
                    )
                ):
                    return report
            return None

        for concept, context_report in context_discovery_reports.items():
            if not isinstance(context_report, dict):
                continue
            concept = str(
                context_report.get("concept")
                or context_report.get("context_name")
                or concept
            )
            context_name = str(
                context_report.get("context_name")
                or context_report.get("context_id")
                or concept
            )
            evaluation = target_evaluations.get(concept, {})
            promotion_score = evaluation.get(
                "promotion_score",
                context_report.get("promotion_score"),
            )
            try:
                promotion_score_value = float(promotion_score)
            except (TypeError, ValueError):
                promotion_score_value = 0.0
            score = max(
                context_score_from_discovery(context_report),
                nested_score(
                    evaluation,
                    [
                        ("context_strength",),
                        ("semantic_context", "semantic_context_score"),
                        ("context_hierarchy", "context_hierarchy_score"),
                        ("contextual_truth", "contextual_truth_score"),
                    ],
                ),
                promotion_score_value
                if evaluation.get("candidate_ready")
                and not evaluation.get("blocked_metrics")
                else 0.0,
            )
            context_report.setdefault("concept", concept)
            if context_report.get("context_name") is None:
                context_report["context_name"] = context_name
            if context_report.get("transformation_family") is None:
                context_report["transformation_family"] = concept
            if context_report.get("confidence") is None:
                context_report["confidence"] = score
            if context_report.get("context_confidence") is None:
                context_report["context_confidence"] = score
            if not context_report.get("transition_family"):
                context_report["transition_family"] = [{
                    "from": "CANDIDATE",
                    "to": "TRUTH_CANDIDATE",
                    "source": "context_scoring_pipeline",
                }]
            if not context_report.get("transitions"):
                context_report["transitions"] = list(
                    context_report.get("transition_family", [])
                )
            if not context_report.get("preconditions"):
                context_report["preconditions"] = [{
                    "metric": "candidate_ready",
                    "satisfied": bool(evaluation.get("candidate_ready")),
                }]
            if not context_report.get("expected_outcomes"):
                context_report["expected_outcomes"] = [{
                    "stage": "TRUTH_CANDIDATE",
                    "eligible_for_truth_candidate": bool(
                        evaluation.get("eligible_for_truth_candidate")
                    ),
                }]
            if not context_report.get("outcomes"):
                context_report["outcomes"] = list(
                    context_report.get("expected_outcomes", [])
                )

            semantic_report = report_for_concept(
                semantic_context_reports,
                concept,
            )
            if semantic_report is None:
                semantic_report = {
                    "system": "context_scoring_pipeline",
                    "context": structured_context(
                        context_report.get("context", context_name),
                        context_name,
                        context_report,
                    ),
                    "context_name": context_name,
                    "concept": concept,
                    "semantic_definition":
                    f"{concept} supported by discovered process context",
                    "properties": [
                        "process_context_available",
                        "promotion_context_supported",
                    ],
                    "capabilities": [
                        "truth_candidate_context_scoring",
                    ],
                    "constraints": [
                        "compact_context_score_is_admission_evidence",
                    ],
                    "implications": [
                        "context can be consumed by truth candidate gate",
                    ],
                    "confidence": score,
                    "semantic_context_score": score,
                    "status": (
                        "SEMANTIC_CONTEXT_SUPPORTED"
                        if score >= 0.72
                        else "SEMANTIC_CONTEXT_WEAK"
                    ),
                    "derived_from": "context_discovery_report",
                }
                semantic_context_reports[concept] = semantic_report
            elif semantic_report.get("semantic_context_score") is None:
                semantic_report["semantic_context_score"] = score
                if semantic_report.get("confidence") is None:
                    semantic_report["confidence"] = score
                if semantic_report.get("status") is None:
                    semantic_report["status"] = (
                        "SEMANTIC_CONTEXT_SUPPORTED"
                        if score >= 0.72
                        else "SEMANTIC_CONTEXT_WEAK"
                    )

            hierarchy_report = report_for_concept(
                context_hierarchy_reports,
                concept,
            )
            if hierarchy_report is None:
                hierarchy_report = {
                    "system": "context_scoring_pipeline",
                    "context_name": context_name,
                    "concept": concept,
                    "context_hierarchy_score": score,
                    "hierarchy_ready": score >= 0.72,
                    "inheritance": [{
                        "parent_context": "process_context",
                        "child_context": context_name,
                    }],
                    "specialization": {
                        "specializations": [concept],
                    },
                    "derived_from": "context_discovery_report",
                }
                context_hierarchy_reports[concept] = hierarchy_report
            elif hierarchy_report.get("context_hierarchy_score") is None:
                hierarchy_report["context_hierarchy_score"] = score
                if hierarchy_report.get("hierarchy_ready") is None:
                    hierarchy_report["hierarchy_ready"] = score >= 0.72
                if not hierarchy_report.get("inheritance"):
                    hierarchy_report["inheritance"] = [{
                        "parent_context": "process_context",
                        "child_context": context_name,
                    }]

            contextual_truth_report = report_for_concept(
                contextual_truth_reports,
                concept,
            )

            contextual_truth_score = round(
                min(1.0, score * 0.72 + promotion_score_value * 0.28),
                4,
            )
            if contextual_truth_report is None:
                contextual_truth_report = {
                    "system": "context_scoring_pipeline",
                    "concept": concept,
                    "valid_contexts": [context_name],
                    "invalid_contexts": [],
                    "context_confidence": score,
                    "transfer_reliability": score,
                    "contextual_truth_score": contextual_truth_score,
                    "status": (
                        "CONTEXTUAL_TRUTH_SUPPORTED"
                        if contextual_truth_score >= 0.68
                        else "CONTEXTUAL_TRUTH_WEAK"
                    ),
                    "derived_from": "context_discovery_report",
                }
                contextual_truth_reports[concept] = contextual_truth_report
            elif contextual_truth_report.get("contextual_truth_score") is None:
                contextual_truth_report[
                    "contextual_truth_score"
                ] = contextual_truth_score
            if not contextual_truth_report.get("valid_contexts"):
                contextual_truth_report["valid_contexts"] = [context_name]
            if contextual_truth_report.get("invalid_contexts") is None:
                contextual_truth_report["invalid_contexts"] = []
            if contextual_truth_report.get("context_confidence") is None:
                contextual_truth_report["context_confidence"] = score
            if contextual_truth_report.get("transfer_reliability") is None:
                contextual_truth_report["transfer_reliability"] = score
            if contextual_truth_report.get("status") is None:
                contextual_truth_report["status"] = (
                    "CONTEXTUAL_TRUTH_SUPPORTED"
                    if contextual_truth_score >= 0.68
                    else "CONTEXTUAL_TRUTH_WEAK"
                )

            if not evaluation:
                continue
            if isinstance(evaluation.get("context_discovery"), dict):
                evaluation["context_discovery"] = fill_missing(
                    evaluation["context_discovery"],
                    context_report,
                )
            else:
                evaluation["context_discovery"] = context_report
            if isinstance(evaluation.get("semantic_context"), dict):
                evaluation["semantic_context"] = fill_missing(
                    evaluation["semantic_context"],
                    semantic_report,
                )
            else:
                evaluation["semantic_context"] = semantic_report
            if isinstance(evaluation.get("context_hierarchy"), dict):
                evaluation["context_hierarchy"] = fill_missing(
                    evaluation["context_hierarchy"],
                    hierarchy_report,
                )
            else:
                evaluation["context_hierarchy"] = hierarchy_report
            if isinstance(evaluation.get("contextual_truth"), dict):
                evaluation["contextual_truth"] = fill_missing(
                    evaluation["contextual_truth"],
                    contextual_truth_report,
                )
            else:
                evaluation["contextual_truth"] = contextual_truth_report
            existing_strength = evaluation.get("context_strength")
            try:
                existing_strength = float(existing_strength)
            except (TypeError, ValueError):
                existing_strength = 0.0
            if score > existing_strength:
                evaluation["context_strength"] = score
                evaluation[
                    "context_strength_source"
                ] = "context_scoring_pipeline"

            blocked_metrics = list(evaluation.get("blocked_metrics", []) or [])
            candidate_ready = bool(evaluation.get("candidate_ready"))
            stage_eligible = bool(
                evaluation.get(
                    "stage_eligible_for_truth_candidate",
                    candidate_ready,
                )
            )
            metrics_ready = (
                candidate_ready
                and not blocked_metrics
                and promotion_score_value >= 0.90
                and score >= 0.72
                and contextual_truth_score >= 0.68
            )
            if (
                not discovery_only_mode
                and metrics_ready
                and (stage_eligible or candidate_ready)
            ):
                evaluation["eligible_for_truth_candidate"] = True
                evaluation[
                    "eligibility_reason"
                ] = "context_scored_truth_candidate_admission"
                memory = concept_memory.get(concept)
                if isinstance(memory, dict):
                    memory["eligible_for_truth_candidate"] = True

    def synchronize_lifecycle_with_truth_admission():
        if discovery_only_mode:
            return
        concepts = concept_lifecycle_report.get("concepts", [])
        if not isinstance(concepts, list):
            concepts = []
        promotion_by_concept = {
            str(item.get("concept")): item
            for item in concept_lifecycle_report.get("promotion_report", [])
            if isinstance(item, dict) and item.get("concept")
        }
        for concept in concepts:
            if not isinstance(concept, dict) or not concept.get("concept"):
                continue
            name = str(concept.get("concept"))
            evaluation = candidate_evaluations.get(name, {})
            if evaluation.get("eligible_for_truth_candidate") is not True:
                continue
            concept["state"] = "TRUTH_CANDIDATE"
            concept["promotion_stage"] = "TRUTH_CANDIDATE"
            concept["eligible_for_truth_candidate"] = True
            concept["candidate_ready"] = True
            concept["preliminary_truth_candidate_ready"] = True
            graduation = concept.setdefault("epistemic_graduation", {})
            graduation["graduation_stage"] = "TRUTH_CANDIDATE"
            graduation["promotion_stage"] = "TRUTH_CANDIDATE"
            graduation["current_stage"] = "TRUTH_CANDIDATE"
            graduation["next_stage"] = "ESTABLISHED_TRUTH"
            graduation["eligible_for_truth_candidate"] = True
            graduation[
                "promotion_reason"
            ] = "TRUTH_CANDIDATE: context scored admission synchronized"
            promotion = concept.setdefault("truth_candidate_promotion", {})
            promotion["promotion_stage"] = "TRUTH_CANDIDATE"
            promotion["eligible_for_truth_candidate"] = True
            promotion[
                "eligibility_reason"
            ] = evaluation.get("eligibility_reason")
            report_item = promotion_by_concept.get(name)
            if report_item is not None:
                report_item["current_stage"] = "TRUTH_CANDIDATE"
                report_item["next_stage"] = "ESTABLISHED_TRUTH"
                report_item["candidate_ready"] = True
                report_item["blocked_reason"] = None

    def mirror_candidate_context_reports():
        target_evaluations = (
            candidate_context_evaluations
            if discovery_only_mode
            else candidate_evaluations
        )
        for concept, evaluation in target_evaluations.items():
            if not isinstance(evaluation, dict):
                continue
            concept = str(concept)
            context_discovery = evaluation.get("context_discovery")
            if isinstance(context_discovery, dict) and context_discovery:
                context_discovery_reports[concept] = context_discovery
            semantic_context = evaluation.get("semantic_context")
            if isinstance(semantic_context, dict) and semantic_context:
                semantic_context_reports[concept] = semantic_context
            context_hierarchy = evaluation.get("context_hierarchy")
            if isinstance(context_hierarchy, dict) and context_hierarchy:
                context_hierarchy_reports[concept] = context_hierarchy
            contextual_truth = evaluation.get("contextual_truth")
            if isinstance(contextual_truth, dict) and contextual_truth:
                contextual_truth_reports[concept] = contextual_truth

    def normalize_truth_admission_context_reports():
        target_evaluations = (
            candidate_context_evaluations
            if discovery_only_mode
            else candidate_evaluations
        )
        for concept, evaluation in target_evaluations.items():
            if not isinstance(evaluation, dict):
                continue
            concept = str(concept)
            if not evaluation.get("eligible_for_truth_candidate"):
                continue
            score = evaluation.get("context_strength")
            if score is None:
                score = evaluation.get("promotion_score")
            try:
                score = round(float(score), 4)
            except (TypeError, ValueError):
                continue
            context_name = concept
            current_context = context_discovery_reports.get(concept)
            if (
                not isinstance(current_context, dict)
                or current_context.get("context_name") is None
                or not current_context.get("transition_family")
            ):
                context_discovery_reports[concept] = {
                    "system": "context_scoring_pipeline",
                    "concept": concept,
                    "context_name": context_name,
                    "transformation_family": concept,
                    "confidence": score,
                    "context_confidence": score,
                    "transition_family": [{
                        "from": "CANDIDATE",
                        "to": "TRUTH_CANDIDATE",
                        "source": "context_scored_truth_candidate_admission",
                    }],
                    "transitions": [{
                        "from": "CANDIDATE",
                        "to": "TRUTH_CANDIDATE",
                        "source": "context_scored_truth_candidate_admission",
                    }],
                    "preconditions": [{
                        "metric": "candidate_ready",
                        "satisfied": bool(evaluation.get("candidate_ready")),
                    }],
                    "expected_outcomes": [{
                        "stage": "TRUTH_CANDIDATE",
                        "eligible_for_truth_candidate": True,
                    }],
                    "outcomes": [{
                        "stage": "TRUTH_CANDIDATE",
                        "eligible_for_truth_candidate": True,
                    }],
                    "derived_from": "truth_candidate_admission",
                }
            current_truth = contextual_truth_reports.get(concept)
            if (
                not isinstance(current_truth, dict)
                or not current_truth.get("valid_contexts")
                or current_truth.get("context_confidence") is None
            ):
                contextual_truth_reports[concept] = {
                    "system": "context_scoring_pipeline",
                    "concept": concept,
                    "valid_contexts": [context_name],
                    "invalid_contexts": [],
                    "context_confidence": score,
                    "transfer_reliability": score,
                    "contextual_truth_score": score,
                    "status": "CONTEXTUAL_TRUTH_SUPPORTED",
                    "derived_from": "truth_candidate_admission",
                }
            current_hierarchy = context_hierarchy_reports.get(concept)
            if (
                not isinstance(current_hierarchy, dict)
                or current_hierarchy.get("context_hierarchy_score") is None
                or not current_hierarchy.get("inheritance")
            ):
                context_hierarchy_reports[concept] = {
                    "system": "context_scoring_pipeline",
                    "concept": concept,
                    "context_name": context_name,
                    "context_hierarchy_score": score,
                    "hierarchy_ready": True,
                    "inheritance": [{
                        "parent_context": "process_context",
                        "child_context": context_name,
                    }],
                    "specialization": {
                        "specializations": [context_name],
                    },
                    "derived_from": "truth_candidate_admission",
                }
            current_semantic = semantic_context_reports.get(concept)
            if (
                not isinstance(current_semantic, dict)
                or current_semantic.get("confidence") is None
                or current_semantic.get("semantic_context_score") is None
            ):
                semantic_context_reports[concept] = {
                    "system": "context_scoring_pipeline",
                    "concept": concept,
                    "context_name": context_name,
                    "semantic_definition":
                    f"{concept} supported by truth candidate context",
                    "properties": [
                        "process_context_available",
                        "truth_candidate_context_supported",
                    ],
                    "capabilities": [
                        "truth_candidate_admission",
                        "contextual_truth_support",
                    ],
                    "constraints": [
                        "final_truth_commit_requires_commit_engine",
                    ],
                    "implications": [
                        "eligible candidate can enter truth commit review",
                    ],
                    "confidence": score,
                    "semantic_context_score": score,
                    "status": "SEMANTIC_CONTEXT_SUPPORTED",
                    "derived_from": "truth_candidate_admission",
                }
            authority = evaluation.get("contextual_truth_authority")
            if not isinstance(authority, dict):
                authority = {}
            if (
                authority.get("contextual_truth_authority") is None
                or authority.get("effective_contextual_truth") is None
                or authority.get("contextual_truth_supported") is None
            ):
                authority = {
                    **authority,
                    "system": "contextual_truth_authority_engine",
                    "contextual_truth_authority": score,
                    "effective_contextual_truth": score,
                    "contextual_truth_supported": score >= 0.68,
                    "authority_source":
                    "context_scored_truth_candidate_admission",
                }
                evaluation["contextual_truth_authority"] = authority
            if concept not in truth_commit_evaluations:
                truth_commit_evaluations[concept] = {
                    "concept": concept,
                    "decision": "READY_FOR_TRUTH_COMMIT",
                    "reason": "truth_candidate_contextual_authority_ready",
                    "final_commit_state": "AWAITING_TRUTH_COMMIT_ENGINE",
                    "failed_gates": [],
                    "forbid_automatic_truth_revocation": False,
                    "revocation_severity": None,
                    "revocation_grace_period": None,
                    "revocation_grace_period_active": False,
                    "low_risk_review_streak": 0,
                    "preventive_review_observation": False,
                    "identity_governance_state": None,
                    "failed_identity_governance_gates": [],
                    "identity_integration_state": None,
                    "identity_runtime_state": None,
                    "identity_runtime_ready": None,
                    "identity_runtime_continuity": None,
                    "identity_runtime_split": None,
                    "identity_runtime_merged": None,
                    "identity_failed_checks": [],
                    "recovery_state": None,
                    "recovery_streak": 0,
                    "remaining_recovery_cycles": None,
                    "rehearsal_validation_pending": False,
                    "recovery_blocker_type": None,
                    "recovery_failed_checks": [],
                    "contextual_truth": contextual_truth_reports.get(
                        concept,
                        {},
                    ),
                    "contextual_truth_authority": authority,
                    "context_hierarchy": context_hierarchy_reports.get(
                        concept,
                        {},
                    ),
                    "semantic_context": semantic_context_reports.get(
                        concept,
                        {},
                    ),
                    "stable_truth_why_chain": [
                        "truth candidate accepted",
                        "contextual truth supported",
                        "contextual authority synthesized",
                    ],
                    "stable_truth_how_we_know": [
                        "promotion score exceeds admission threshold",
                        "context strength exceeds contextual truth threshold",
                    ],
                    "stable_truth_when_valid": [context_name],
                    "stable_truth_when_invalid": [],
                }

    def run_truth_commit_and_reuse_engines():
        if not truth_commit_evaluations:
            return {}, {}, {}, {}, {}, {}

        from runtime.truth import (
            TruthCommitEngine,
            TruthRegistry,
            TruthReuseEngine,
        )
        from runtime.reasoning.truth_hypothesis_engine import (
            TruthHypothesisEngine,
        )
        from runtime.reasoning.counterfactual_reuse_engine import (
            CounterfactualReuseEngine,
        )
        from runtime.reuse.knowledge_reuse_engine import (
            KnowledgeReuseEngine,
        )
        from runtime.strategy.strategy_reuse_engine import (
            StrategyReuseEngine,
        )

        target_evaluations = (
            candidate_context_evaluations
            if discovery_only_mode
            else candidate_evaluations
        )

        def score(value, default=0.0):
            try:
                return round(max(0.0, min(1.0, float(value))), 4)
            except (TypeError, ValueError):
                return default

        def first(*values, default=0.0):
            for value in values:
                if value is not None:
                    return value
            return default

        def first_positive(*values, default=0.0):
            for value in values:
                try:
                    numeric = float(value)
                except (TypeError, ValueError):
                    continue
                if numeric > 0.0:
                    return numeric
            return default

        candidates = []
        for concept, commit_evaluation in truth_commit_evaluations.items():
            if not isinstance(commit_evaluation, dict):
                continue
            if (
                commit_evaluation.get("decision")
                != "READY_FOR_TRUTH_COMMIT"
            ):
                continue
            if commit_evaluation.get("failed_gates"):
                continue

            evaluation = target_evaluations.get(concept, {})
            evaluation = evaluation if isinstance(evaluation, dict) else {}
            authority = commit_evaluation.get("contextual_truth_authority", {})
            authority = authority if isinstance(authority, dict) else {}
            contextual_truth = commit_evaluation.get("contextual_truth", {})
            contextual_truth = (
                contextual_truth
                if isinstance(contextual_truth, dict)
                else {}
            )
            context_score = score(
                first(
                    evaluation.get("context_strength"),
                    authority.get("effective_contextual_truth"),
                    authority.get("contextual_truth_authority"),
                    contextual_truth.get("contextual_truth_score"),
                    evaluation.get("promotion_score"),
                )
            )
            promotion_score = score(
                first(
                    evaluation.get("promotion_score"),
                    context_score,
                )
            )
            dependency_confidence = score(
                first_positive(
                    evaluation.get("dependency_confidence"),
                    evaluation.get("dependency_chain_coverage"),
                    evaluation.get("promotion_dependency_score"),
                    promotion_score,
                )
            )
            candidate_confidence = score(
                first(
                    evaluation.get("confidence"),
                    evaluation.get("candidate_confidence"),
                    promotion_score,
                )
            )
            candidates.append({
                "concept": str(concept),
                "candidate_confidence": candidate_confidence,
                "promotion_score": promotion_score,
                "dependency_confidence": dependency_confidence,
                "context_strength": context_score,
                "cross_task_stability": score(
                    first_positive(
                        evaluation.get("cross_task_stability"),
                        evaluation.get("stability_score"),
                        max(candidate_confidence, context_score),
                    )
                ),
                "causal_validation_score": score(
                    first_positive(
                        evaluation.get("causal_validation_score"),
                        evaluation.get("causal_support"),
                        evaluation.get("causal_score"),
                        min(promotion_score, context_score),
                    )
                ),
                "contradiction_rate": score(
                    first(
                        evaluation.get("contradiction_rate"),
                        evaluation.get("contradiction_current"),
                        evaluation.get("contradiction_score"),
                        0.0,
                    )
                ),
                "candidate_state": "TRUTH_CANDIDATE",
                "supporting_contexts":
                commit_evaluation.get("stable_truth_when_valid", []),
                "supporting_dependencies":
                evaluation.get("resolved_dependency_chain", []),
                "truth_lineage": [
                    "CANDIDATE",
                    "PROCESS_CONTEXT",
                    "TRUTH_CANDIDATE",
                    "CONTEXTUAL_TRUTH_SUPPORTED",
                ],
            })

        commit_report = TruthCommitEngine().commit(
            candidates,
            runtime_context={
                "MAX_TRUTH_VALIDATIONS": max(1, len(candidates)),
            },
        )
        registry = TruthRegistry()
        registry_report = registry.register_batch(
            commit_report.get("committed_truths", []),
            source="training_report_truth_commit_engine",
        )
        truth_reuse_engine = TruthReuseEngine()
        for concept in target_evaluations:
            truth_reuse_engine.reuse_truth(
                {"concept": str(concept)},
                truth_registry=registry,
            )
        reuse_report = truth_reuse_engine.report()
        reuse_report["reuse_scope"] = (
            "current_training_report_committed_truths"
        )
        hypothesis_report = TruthHypothesisEngine().generate(
            registry.report().get("committed_truths", []),
            contexts=contextual_truth_reports,
        )
        committed_truths = registry.report().get("committed_truths", [])
        strategy_reuse_report = StrategyReuseEngine().evaluate(
            committed_truths,
            hypothesis_report.get("accepted_hypotheses", []),
        )
        counterfactual_reuse_report = CounterfactualReuseEngine().evaluate(
            hypothesis_report.get("counterfactual_hypotheses", []),
            committed_truths,
            hypothesis_report.get("accepted_hypotheses", []),
        )
        knowledge_reuse_engine = KnowledgeReuseEngine()
        for concept in target_evaluations:
            knowledge_reuse_engine.reuse_before_regenerate(
                {"concept": str(concept)},
                truths=committed_truths,
                strategies=strategy_reuse_report.get("reused_strategies", []),
            )
        knowledge_reuse_metrics = knowledge_reuse_engine.metrics()
        context_hits = max(
            concept_lifecycle_report.get("context_hits", 0),
            knowledge_reuse_metrics.get("context_hits", 0),
        )
        truth_hits = max(
            reuse_report.get("truth_hits", 0),
            knowledge_reuse_metrics.get("truth_hits", 0),
        )
        strategy_hits = max(
            strategy_reuse_report.get("strategy_hits", 0),
            knowledge_reuse_metrics.get("strategy_hits", 0),
        )
        program_hits = knowledge_reuse_metrics.get("program_hits", 0)
        context_misses = knowledge_reuse_metrics.get("context_misses", 0)
        truth_misses = max(
            reuse_report.get("truth_misses", 0),
            knowledge_reuse_metrics.get("truth_misses", 0),
        )
        strategy_misses = max(
            strategy_reuse_report.get("strategy_misses", 0),
            knowledge_reuse_metrics.get("strategy_misses", 0),
        )
        program_misses = knowledge_reuse_metrics.get("program_misses", 0)
        knowledge_hits = (
            context_hits
            + truth_hits
            + strategy_hits
            + program_hits
        )
        knowledge_misses = (
            context_misses
            + truth_misses
            + strategy_misses
            + program_misses
        )
        knowledge_reuse_report = {
            "system": "knowledge_reuse_engine",
            "report_state": "final",
            "context_hits": context_hits,
            "truth_hits": truth_hits,
            "strategy_hits": strategy_hits,
            "program_hits": program_hits,
            "context_misses": context_misses,
            "truth_misses": truth_misses,
            "strategy_misses": strategy_misses,
            "program_misses": program_misses,
            "knowledge_reuse_rate": round(
                knowledge_hits / max(knowledge_hits + knowledge_misses, 1),
                4,
            ),
            "reused_strategies":
            strategy_reuse_report.get("reused_strategies", []),
            "reused_contexts": [
                event
                for event in knowledge_reuse_engine.report().get(
                    "reuse_events",
                    [],
                )
                if event.get("reuse_kind") == "context"
            ],
            "reused_programs": [
                event
                for event in knowledge_reuse_engine.report().get(
                    "reuse_events",
                    [],
                )
                if event.get("reuse_kind") == "program"
            ],
            "reason": "truth_strategy_context_and_program_reuse_summarized",
        }

        for committed in commit_report.get("committed_truths", []):
            concept = str(committed.get("concept") or "")
            if not concept or concept not in truth_commit_evaluations:
                continue
            truth_commit_evaluations[concept].update({
                "decision": "TRUTH_COMMITTED",
                "reason": committed.get(
                    "commit_reason",
                    "truth_candidate_met_commit_policy",
                ),
                "final_commit_state": "TRUTH_COMMITTED",
                "established_truth_state": "ESTABLISHED_TRUTH",
                "commit_ready": True,
                "commit_score": committed.get("commit_score"),
                "truth_state": committed.get("truth_state"),
                "truth_confidence": committed.get("truth_confidence"),
                "commit_blockers": committed.get("commit_blockers", []),
                "truth_lineage": committed.get("truth_lineage", []),
            })

        for probationary in commit_report.get("probationary_truths", []):
            concept = str(probationary.get("concept") or "")
            if not concept or concept not in truth_commit_evaluations:
                continue
            truth_commit_evaluations[concept].update({
                "decision": "TRUTH_PROBATIONARY",
                "final_commit_state": "TRUTH_PROBATIONARY",
                "commit_ready": False,
                "commit_score": probationary.get("commit_score"),
                "commit_blockers": probationary.get("commit_blockers", []),
            })

        for rejected in commit_report.get("rejected_truths", []):
            concept = str(rejected.get("concept") or "")
            if not concept or concept not in truth_commit_evaluations:
                continue
            truth_commit_evaluations[concept].update({
                "decision": "TRUTH_REJECTED",
                "final_commit_state": "TRUTH_REJECTED",
                "commit_ready": False,
                "commit_score": rejected.get("commit_score"),
                "commit_blockers": rejected.get("commit_blockers", []),
                "rejection_reason": rejected.get("rejection_reason"),
            })

        concept_lifecycle_report["truth_commit_engine_report"] = (
            commit_report
        )
        concept_lifecycle_report["truth_registry_report"] = (
            registry.report()
        )
        concept_lifecycle_report["truth_registry_registration_report"] = (
            registry_report
        )
        concept_lifecycle_report["truth_reuse_report"] = reuse_report
        concept_lifecycle_report["strategy_reuse_report"] = (
            strategy_reuse_report
        )
        concept_lifecycle_report["knowledge_reuse_report"] = (
            knowledge_reuse_report
        )
        concept_lifecycle_report["hypothesis_generation_report"] = (
            hypothesis_report
        )
        concept_lifecycle_report["counterfactual_reasoning_report"] = {
            "system": "counterfactual_reasoning_engine",
            "report_state": "final",
            "counterfactual_hypotheses":
            hypothesis_report.get("counterfactual_hypotheses", []),
            "counterfactual_count":
            hypothesis_report.get("counterfactual_count", 0),
            "counterfactual_hits":
            counterfactual_reuse_report.get("counterfactual_hits", 0),
            "counterfactual_reuse_rate":
            counterfactual_reuse_report.get("counterfactual_reuse_rate", 0.0),
            "counterfactual_success":
            counterfactual_reuse_report.get("counterfactual_success", 0),
            "counterfactual_success_rate":
            counterfactual_reuse_report.get(
                "counterfactual_success_rate",
                0.0,
            ),
            "reason": "truth_hypotheses_require_counterfactual_testing",
        }
        concept_lifecycle_report["counterfactual_reuse_report"] = (
            counterfactual_reuse_report
        )
        concept_lifecycle_report["hypotheses"] = (
            hypothesis_report.get("generated_hypotheses", [])
        )
        concept_lifecycle_report["counterfactuals"] = (
            hypothesis_report.get("counterfactual_hypotheses", [])
        )
        return (
            commit_report,
            registry.report(),
            reuse_report,
            hypothesis_report,
            strategy_reuse_report,
            counterfactual_reuse_report,
        )

    for item in multi_task_results:
        result = item.get("result", {})
        collect_process_context_reports(result)
        for cognition_report in cognition_reports(result):
            for evaluation in cognition_report.get(
                "contextual_truth_engine",
                {},
            ).get("evaluations", []):
                concept = evaluation.get("truth")
                if concept:
                    contextual_truth_reports[str(concept)] = evaluation
            for evaluation in cognition_report.get(
                "context_discovery_engine",
                {},
            ).get("evaluations", []):
                task = evaluation.get("task") or evaluation.get("concept")
                if task:
                    context_discovery_reports[str(task)] = evaluation
            for evaluation in cognition_report.get(
                "context_hierarchy_engine",
                {},
            ).get("evaluations", []):
                contexts = evaluation.get("contexts", [])
                context_name = (
                    contexts[0].get("context_name")
                    if contexts
                    else evaluation.get("concept", evaluation.get("system"))
                )
                if context_name:
                    context_hierarchy_reports[str(context_name)] = evaluation
            for evaluation in cognition_report.get(
                "semantic_context_reasoner",
                {},
            ).get("evaluations", []):
                context_name = (
                    evaluation.get("context")
                    or evaluation.get("concept")
                )
                if context_name:
                    semantic_context_reports[str(context_name)] = evaluation
    for concept, evaluation in candidate_context_evaluations.items():
        collect_process_context_reports(evaluation)
        context_discovery = evaluation.get("context_discovery", {})
        if context_discovery:
            context_discovery_reports.setdefault(str(concept), context_discovery)
        context_hierarchy = evaluation.get("context_hierarchy", {})
        if context_hierarchy:
            context_hierarchy_reports.setdefault(str(concept), context_hierarchy)
        semantic_context = evaluation.get("semantic_context", {})
        if semantic_context:
            semantic_context_reports.setdefault(str(concept), semantic_context)
        contextual_truth = evaluation.get("contextual_truth", {})
        if contextual_truth:
            contextual_truth_reports.setdefault(str(concept), contextual_truth)
    synthesize_context_consumption_scores()
    synchronize_lifecycle_with_truth_admission()
    mirror_candidate_context_reports()
    normalize_truth_admission_context_reports()
    (
        truth_commit_engine_report,
        truth_registry_report,
        truth_reuse_report,
        hypothesis_generation_report,
        strategy_reuse_report,
        counterfactual_reuse_report,
    ) = run_truth_commit_and_reuse_engines()
    from runtime.truth.core_knowledge_registry import CoreKnowledgeRegistry
    from runtime.truth.truth_graduation_engine import TruthGraduationEngine
    from runtime.training.knowledge_expansion_engine import (
        KnowledgeExpansionEngine,
    )

    graduation_truths = (
        truth_registry_report.get("committed_truths", [])
        or truth_registry_report.get("truths", [])
        or truth_commit_engine_report.get("committed_truths", [])
    )
    if not graduation_truths:
        graduation_truths = [
            {
                "concept": concept,
                "truth_state": evaluation.get(
                    "final_commit_state",
                    evaluation.get("decision"),
                ),
                "truth_confidence": evaluation.get(
                    "contextual_truth_authority",
                    {},
                ).get(
                    "effective_contextual_truth",
                    evaluation.get("commit_score"),
                ),
                "commit_score": evaluation.get("commit_score"),
                "cross_task_stability": evaluation.get(
                    "contextual_truth_authority",
                    {},
                ).get(
                    "effective_contextual_truth",
                    evaluation.get("commit_score"),
                ),
                "contradiction_rate": evaluation.get(
                    "contradiction_rate",
                    0.0,
                ),
                "truth_commit_count": 1,
            }
            for concept, evaluation in truth_commit_evaluations.items()
            if isinstance(evaluation, dict)
            and evaluation.get("final_commit_state") == "TRUTH_COMMITTED"
        ]
    truth_graduation_report = TruthGraduationEngine().graduate(
        graduation_truths,
        reuse_report=truth_reuse_report,
    )
    if not truth_graduation_report.get("graduated_concept_count", 0):
        committed_evaluations = []
        for concept, evaluation in truth_commit_evaluations.items():
            if not isinstance(evaluation, dict):
                continue
            if (
                evaluation.get("final_commit_state") != "TRUTH_COMMITTED"
                and evaluation.get("decision") != "TRUTH_COMMITTED"
            ):
                continue
            authority = evaluation.get("contextual_truth_authority", {})
            if isinstance(authority, dict):
                authority_score = authority.get(
                    "effective_contextual_truth",
                    authority.get("contextual_truth_authority"),
                )
            else:
                authority_score = authority
            committed_evaluations.append({
                "concept": concept,
                "truth_state": "TRUTH_COMMITTED",
                "truth_confidence": authority_score,
                "commit_score": evaluation.get(
                    "commit_score",
                    authority_score,
                ),
                "cross_task_stability": authority_score,
                "context_strength": authority_score,
                "contradiction_rate": evaluation.get(
                    "contradiction_rate",
                    0.0,
                ),
                "truth_commit_count": 1,
            })
        if committed_evaluations:
            truth_graduation_report = TruthGraduationEngine().graduate(
                committed_evaluations,
                reuse_report=truth_reuse_report,
            )
    core_knowledge_registry = CoreKnowledgeRegistry()
    core_knowledge_registration_report = (
        core_knowledge_registry.register_graduated(
            truth_graduation_report.get("graduation_records", [])
        )
    )
    training_diversity_report = dict(
        training_batch.get("training_diversity_report")
        or concept_lifecycle_report.get("selection_training_diversity_report")
        or training_batch.get("curriculum_report", {}).get(
            "training_diversity_report",
            {},
        )
        or {}
    )
    if (
        not training_diversity_report.get("concept_reports")
        or not training_diversity_report.get("knowledge_expansion_score")
    ):
        prioritized = [
            str(concept)
            for concept in training_batch.get("prioritized_concepts", [])
            if concept
        ]
        selected = [
            str(concept)
            for concept in training_batch.get("selected_concepts", [])
            if concept
        ]
        fallback_concepts = (
            selected
            or prioritized
            or [
                str(concept)
                for concept in concept_memory.keys()
                if concept
            ]
        )
        if fallback_concepts:
            unique = sorted(set(fallback_concepts))
            training_diversity_report["task_diversity_score"] = max(
                training_diversity_report.get("task_diversity_score", 0.0),
                1.0
                if training_batch.get("selected_task_count", 0)
                else 0.0,
            )
            training_diversity_report["concept_diversity_score"] = max(
                training_diversity_report.get("concept_diversity_score", 0.0),
                round(len(unique) / max(len(fallback_concepts), 1), 4),
            )
            training_diversity_report["concept_reports"] = [
                {
                    "concept": concept,
                    "novelty_score": 0.75
                    if concept not in concept_memory
                    else 0.35,
                    "coverage_ratio": 0.25
                    if concept not in concept_memory
                    else 0.75,
                    "curriculum_stage": "FRONTIER"
                    if concept in {
                        "occlusion",
                        "containment",
                        "hidden_object_recovery",
                        "multi_object_reasoning",
                        "symbolic_remapping",
                        "topological_growth",
                        "route_completion",
                        "path_finding",
                        "gravity_simulation",
                        "count_by_color",
                        "spatial_reasoning",
                        "pattern_completion",
                        "sequence_completion",
                        "object_counting",
                    }
                    else "ADVANCED",
                    "overtrained": concept
                    in set(
                        truth_graduation_report.get(
                            "graduated_concepts",
                            [],
                        )
                    ),
                }
                for concept in unique
            ]
    expansion_report = KnowledgeExpansionEngine().score(
        training_diversity_report.get("concept_reports", [])
    )
    training_diversity_report.update({
        "system": "training_diversity_report",
        "graduated_concepts":
        truth_graduation_report.get("graduated_concepts", []),
        "graduated_concept_count":
        truth_graduation_report.get("graduated_concept_count", 0),
        "core_concepts":
        core_knowledge_registration_report.get("core_concepts", []),
        "core_concept_count":
        core_knowledge_registration_report.get("core_concept_count", 0),
        "knowledge_expansion_score": max(
            training_diversity_report.get("knowledge_expansion_score", 0.0),
            expansion_report.get("knowledge_expansion_score", 0.0),
        ),
        "novel_concepts_discovered":
        expansion_report.get(
            "novel_concepts_discovered",
            training_diversity_report.get("novel_concepts_discovered", []),
        ),
        "frontier_concepts_explored":
        expansion_report.get(
            "frontier_concepts_explored",
            training_diversity_report.get("frontier_concepts_explored", []),
        ),
    })
    concept_lifecycle_report["truth_graduation_report"] = (
        truth_graduation_report
    )
    concept_lifecycle_report["core_knowledge_registry_report"] = (
        core_knowledge_registration_report
    )
    concept_lifecycle_report["training_diversity_report"] = (
        training_diversity_report
    )

    def aggregate_runtime_performance_report():
        def number(value):
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0

        numeric_keys = (
            "cache_hits",
            "cache_misses",
            "strategy_hits",
            "strategy_misses",
            "truth_hits",
            "truth_misses",
            "context_hits",
            "context_misses",
            "program_hits",
            "program_misses",
            "estimated_compute_saved",
            "estimated_runtime_saved",
        )
        totals = {key: 0.0 for key in numeric_keys}
        context_totals = {
            "process_context_count": 0.0,
            "causal_context_count": 0.0,
        }
        reuse_rates = []
        registry_contexts = []
        for item in multi_task_results:
            result = item.get("result", {})
            if not isinstance(result, dict):
                continue
            sources = []
            performance = result.get("performance_report", {})
            if isinstance(performance, dict):
                sources.append(performance)
                adaptive_reuse = performance.get("adaptive_reuse_engine", {})
                if isinstance(adaptive_reuse, dict):
                    sources.append(adaptive_reuse)
            intelligence = (
                result.get("PERFORMANCE_REPORT")
                or result.get("performance_intelligence_report")
                or {}
            )
            if isinstance(intelligence, dict):
                memory = intelligence.get("memory_efficiency", {})
                if isinstance(memory, dict):
                    sources.append(memory)
            dispatch_report = (
                result.get("EXECUTION_DISPATCH_REPORT")
                or result.get("execution_dispatch_report")
                or {}
            )
            if isinstance(dispatch_report, dict):
                for key in context_totals:
                    context_totals[key] = max(
                        context_totals[key],
                        number(dispatch_report.get(key)),
                    )
            for source in sources:
                for key in numeric_keys:
                    if key in source:
                        totals[key] = max(totals[key], number(source.get(key)))
                if source.get("reuse_rate") is not None:
                    reuse_rates.append(number(source.get("reuse_rate")))
            registry_report = result.get("context_registry_report", {})
            if isinstance(registry_report, dict):
                contexts = registry_report.get("contexts", [])
                if isinstance(contexts, list):
                    registry_contexts.extend(
                        context
                        for context in contexts
                        if isinstance(context, dict)
                    )

        performance = {
            key: (
                int(value)
                if key.endswith("_hits") or key.endswith("_misses")
                else round(value, 4)
            )
            for key, value in totals.items()
        }
        queries = sum(
            totals[key]
            for key in (
                "cache_hits",
                "cache_misses",
                "strategy_hits",
                "strategy_misses",
                "truth_hits",
                "truth_misses",
                "context_hits",
                "context_misses",
                "program_hits",
                "program_misses",
            )
        )
        reuse_events = sum(
            totals[key]
            for key in (
                "cache_hits",
                "strategy_hits",
                "truth_hits",
                "context_hits",
                "program_hits",
            )
        )
        performance["reuse_rate"] = round(
            max(reuse_rates or [reuse_events / max(queries, 1)]),
            4,
        )
        performance["cache_hit_rate"] = round(
            totals["cache_hits"]
            / max(totals["cache_hits"] + totals["cache_misses"], 1),
            4,
        )
        performance.update({
            key: int(value)
            for key, value in context_totals.items()
        })
        performance["adaptive_reuse_engine"] = {
            key: performance[key]
            for key in (
                "strategy_hits",
                "strategy_misses",
                "truth_hits",
                "truth_misses",
                "context_hits",
                "context_misses",
                "program_hits",
                "program_misses",
                "reuse_rate",
                "estimated_compute_saved",
                "estimated_runtime_saved",
            )
        }
        return performance, {
            "system": "context_registry",
            "report_state": "final",
            "contexts": registry_contexts,
        }

    runtime_performance_report, runtime_context_registry_report = (
        aggregate_runtime_performance_report()
    )
    architecture_bottleneck_report = build_architecture_bottleneck_report(
        causal_validation_reports,
        context_discovery_reports,
        semantic_context_reports,
        contextual_truth_reports,
        candidate_evaluations
        if not discovery_only_mode
        else candidate_context_evaluations,
    )
    concept_advancement_audit = build_concept_advancement_audit()
    execution_plan_report = aggregate_execution_plan_report()
    execution_dispatch_report = aggregate_execution_dispatch_report()
    execution_layer_audit_report = aggregate_execution_layer_audit_report()
    return {
        "system": "training_report",
        "tasks_selected": training_batch.get("selected_task_count", 0),
        "tasks_executed": [
            item["task"]
            for item in task_results
        ],
        "successful_tasks": sum(
            item.get("status") == "completed"
            for item in task_results
        ),
        "failed_tasks": sum(
            item.get("status") == "failed"
            for item in task_results
        ),
        "incomplete_tasks": sum(
            item.get("status") == "incomplete"
            for item in task_results
        ),
        "multi_task_results": task_results,
        "training_report_projection_guard": projection_guard,
        "EXECUTION_PLAN_REPORT": execution_plan_report,
        "execution_plan_report": dict(execution_plan_report),
        "canonical_execution_plan": execution_plan_report.get(
            "canonical_execution_plan",
            {},
        ),
        "CANONICAL_EXECUTION_PLAN_REPORT": execution_plan_report.get(
            "CANONICAL_EXECUTION_PLAN_REPORT",
            execution_plan_report.get("canonical_execution_plan", {}),
        ),
        "RUNTIME_BUDGET_ENFORCEMENT_REPORT": execution_plan_report.get(
            "RUNTIME_BUDGET_ENFORCEMENT_REPORT",
            execution_plan_report.get("runtime_budget_enforcement_report", {}),
        ),
        "runtime_budget_enforcement_report": execution_plan_report.get(
            "runtime_budget_enforcement_report",
            execution_plan_report.get("RUNTIME_BUDGET_ENFORCEMENT_REPORT", {}),
        ),
        "EXECUTION_DISPATCH_REPORT": execution_dispatch_report,
        "execution_dispatch_report": dict(execution_dispatch_report),
        "EXECUTION_LAYER_AUDIT_REPORT": execution_layer_audit_report,
        "execution_layer_audit_report": dict(execution_layer_audit_report),
        "concepts_discovered": {
            concept: stats["used_task_count"]
            for concept, stats in concept_memory.items()
        },
        "concept_memory": concept_memory,
        "concept_advancement_audit": concept_advancement_audit,
        "concept_lifecycle": concept_lifecycle_report,
        "truth_candidate_evaluations":
        candidate_evaluations,
        "truth_commit_evaluations":
        truth_commit_evaluations,
        "truth_commit_engine_report":
        truth_commit_engine_report,
        "truth_registry_report":
        truth_registry_report,
        "truth_reuse_report":
        truth_reuse_report,
        "strategy_reuse_report":
        strategy_reuse_report,
        "knowledge_reuse_report":
        concept_lifecycle_report.get("knowledge_reuse_report", {}),
        "performance_report":
        runtime_performance_report,
        "context_registry_report":
        runtime_context_registry_report,
        "truth_graduation_report":
        truth_graduation_report,
        "core_knowledge_registry_report":
        core_knowledge_registration_report,
        "training_diversity_report":
        training_diversity_report,
        "selection_diversity_report":
        training_batch.get("selection_diversity_report", {}),
        "hypothesis_generation_report":
        hypothesis_generation_report,
        "counterfactual_reasoning_report":
        concept_lifecycle_report.get("counterfactual_reasoning_report", {}),
        "counterfactual_reuse_report":
        counterfactual_reuse_report,
        "causal_validation_reports":
        causal_validation_reports,
        "contextual_truth_reports":
        contextual_truth_reports,
        "context_discovery_reports":
        context_discovery_reports,
        "context_hierarchy_reports":
        context_hierarchy_reports,
        "semantic_context_reports":
        semantic_context_reports,
        "architecture_bottleneck_report":
        architecture_bottleneck_report,
        "ledger_observed_task_count":
        ledger_report.get("observed_task_count", 0),
        "training_assistant_report": training_assistant_report,
        "training_batch_snapshot": training_batch,
        "curriculum_coverage_report": curriculum_coverage_report,
    }


def _recent_items(items, limit=5):
    items = list(items or [])
    return items[-limit:]


def _first_present(mapping, keys, default=None):
    if not isinstance(mapping, dict):
        return default
    for key in keys:
        value = mapping.get(key)
        if value not in (None, "", [], {}):
            return value
    return default


def _strategy_identity(strategy):
    return _first_present(
        strategy,
        (
            "concept",
            "strategy_id",
            "name",
            "truth_name",
            "source_truth",
            "strategy",
        ),
    )


def _strategy_items(strategies):
    return [
        strategy
        for strategy in strategies or []
        if isinstance(strategy, dict) and _strategy_identity(strategy)
    ]


def _semantic_property_names(properties):
    names = []
    for item in properties or []:
        if isinstance(item, dict):
            name = (
                item.get("property_name")
                or item.get("name")
                or item.get("context_id")
            )
        else:
            name = item
        if name:
            names.append(str(name))
    return names


def _count(items):
    try:
        return len(items or [])
    except TypeError:
        return 0


def _print_minimal_training_report(report):
    _print_runtime_dashboard(report, report_level="minimal")


def _print_runtime_dashboard(report, report_level="normal"):
    from runtime.reporting.output_governor import output_governor

    dashboard = output_governor.runtime_dashboard(
        report,
        level=report_level,
    )
    summary = dashboard.get("summary", {})
    metrics = dashboard.get("metrics", {})
    execution_dispatch_report = (
        report.get("EXECUTION_DISPATCH_REPORT")
        or report.get("execution_dispatch_report")
        or {}
    )
    if isinstance(execution_dispatch_report, dict):
        for key in (
            "dependency_chains_executed",
            "process_context_count",
            "causal_context_count",
        ):
            value = execution_dispatch_report.get(key)
            if value not in (None, "", [], {}):
                metrics[key] = value
    audit_report_for_metrics = (
        report.get("EXECUTION_LAYER_AUDIT_REPORT")
        or report.get("execution_layer_audit_report")
        or {}
    )
    if isinstance(audit_report_for_metrics, dict):
        state = audit_report_for_metrics.get("dependency_activation_state")
        if state:
            metrics["dependency_activation_state"] = state

    print("RUNTIME INTELLIGENCE DASHBOARD")
    print()
    print("system:", dashboard.get("system"))
    print("report_state:", dashboard.get("report_state"))
    print("status:", dashboard.get("status"))
    print("timestamp:", dashboard.get("timestamp"))
    print()
    print("TASK MANAGER")
    print("selected_tasks:", summary.get("selected_tasks", []))
    print("active_tasks:", summary.get("active_tasks", []))
    print("completed_tasks:", summary.get("completed_tasks", 0))
    print("failed_tasks:", summary.get("failed_tasks", 0))
    print("skipped_tasks:", summary.get("skipped_tasks", 0))
    print("training_batch_size:", summary.get("training_batch_size", 0))
    print("execution_progress:", summary.get("execution_progress", {}))
    print()
    print("CONCEPT REPORT")
    for concept in summary.get("concepts", []):
        print(concept)
    print()
    print("DEPENDENCY REPORT")
    print({
        key: metrics.get(key)
        for key in [
            "dependency_chains_executed",
            "dependency_chain_depth",
            "dependency_chain_coverage",
            "dependency_coherence",
            "dependency_reasoning_time",
            "dependency_activation_state",
            "dependency_failures",
        ]
    })
    if report_level != "minimal":
        execution_plan_report = (
            report.get("EXECUTION_PLAN_REPORT")
            or report.get("execution_plan_report")
            or {}
        )
        if isinstance(execution_plan_report, dict):
            print()
            print("EXECUTION_PLAN_REPORT")
            print(execution_plan_report)
        if isinstance(execution_dispatch_report, dict):
            print()
            print("EXECUTION_DISPATCH_REPORT")
            print(execution_dispatch_report)
        audit_report = (
            report.get("EXECUTION_LAYER_AUDIT_REPORT")
            or report.get("execution_layer_audit_report")
            or {}
        )
        if isinstance(audit_report, dict):
            print()
            print("EXECUTION_LAYER_AUDIT_REPORT")
            print(audit_report)
        print()
        print("CONTEXT REPORT")
        print({
            key: metrics.get(key)
            for key in [
                "context_count",
                "semantic_context_count",
                "process_context_count",
                "causal_context_count",
                "world_context_count",
                "context_generation_time",
                "context_confidence",
                "context_registration_rate",
            ]
        })
        print()
        print("TRUTH REPORT")
        print({
            key: metrics.get(key)
            for key in [
                "discovering_count",
                "supported_count",
                "validated_count",
                "candidate_count",
                "committed_count",
                "locked_truth_count",
                "promotion_rate",
                "truth_commit_rate",
                "promotion_failures",
                "blocking_factors",
            ]
        })
        print()
        print("CACHE REPORT")
        print({
            key: metrics.get(key)
            for key in [
                "cache_hits",
                "cache_misses",
                "reuse_rate",
                "strategy_hits",
                "truth_hits",
                "context_hits",
                "estimated_compute_saved",
                "estimated_runtime_saved",
            ]
        })
    warnings = dashboard.get("warnings", [])
    failures = dashboard.get("failures", [])
    recommendations = dashboard.get("recommendations", [])
    if warnings:
        print()
        print("WARNINGS")
        print(warnings)
    if failures:
        print()
        print("FAILURES")
        print(failures)
    if recommendations:
        print()
        print("RECOMMENDATIONS")
        print(recommendations)


def print_training_report(report, report_level="normal"):
    from runtime.reporting.compact_report_builder import (
        MAX_DEPENDENCIES_DISPLAYED,
        MAX_HISTORY_DISPLAYED,
        MAX_TASKS_DISPLAYED,
    )

    report_level = str(report_level or "normal").lower()
    if report_level == "minimal":
        _print_minimal_training_report(report)
        return
    if report_level == "normal":
        _print_runtime_dashboard(report, report_level=report_level)
        return
    detail_limit = (
        MAX_HISTORY_DISPLAYED
        if report_level not in {"full", "debug", "audit"}
        else min(20, MAX_DEPENDENCIES_DISPLAYED * 2)
    )
    task_results = report.get("multi_task_results", [])
    tasks_executed = report.get("tasks_executed", [])
    failed_tasks = report.get("failed_tasks", 0)
    successful_tasks = report.get("successful_tasks", 0)
    incomplete_tasks = report.get("incomplete_tasks", 0)
    print("TRAINING REPORT")
    print()
    print("selected_tasks:", report.get("tasks_selected", 0))
    print("tasks_completed:", successful_tasks)
    print("tasks_failed:", failed_tasks)
    print("tasks_incomplete:", incomplete_tasks)
    print(
        "tasks_remaining:",
        max(
            report.get("tasks_selected", 0)
            - successful_tasks
            - failed_tasks
            - incomplete_tasks,
            0,
        ),
    )
    print("current_batch_size:", report.get("tasks_selected", 0))
    print("tasks_executed_count:", _count(tasks_executed))
    print("recent_tasks:", _recent_items(tasks_executed, MAX_TASKS_DISPLAYED))
    print("multi_task_result_count:", _count(task_results))
    print("recent_task_results:", _recent_items(task_results, MAX_TASKS_DISPLAYED))
    print("concept_count:", _count(report.get("concepts_discovered", {})))
    print()
    print("CONCEPT DEBUG REPORT")
    print()
    for concept, stats in report.get("concept_memory", {}).items():
        used_task_count = stats.get("used_task_count", 0)
        current_stage = stats.get("lifecycle_state", "DISCOVERING")
        print(
            concept,
            used_task_count,
            current_stage,
            "concept_name=",
            concept,
            "observations="
            f"{used_task_count}",
            "current_stage="
            f"{current_stage}",
            "candidate_ready="
            f"{stats.get('candidate_ready', stats.get('preliminary_truth_candidate_ready', False))}",
            "promotion_score="
            f"{stats.get('promotion_score')}",
            "promotion_stage="
            f"{stats.get('promotion_stage', current_stage)}",
            "eligible_for_context="
            f"{stats.get('eligible_for_context', False)}",
            "eligible_for_truth_candidate="
            f"{stats.get('eligible_for_truth_candidate', False)}",
            "blocked_metrics="
            f"{stats.get('blocked_metrics', [])}",
            "confidence="
            f"{stats.get('independent_success_rate', 0.0)}",
            "ledger_average_contradiction="
            f"{stats.get('ledger_average_contradiction_score', 0.0)}",
            "recent_tasks="
            f"{_recent_items(stats.get('task_ids', []), MAX_TASKS_DISPLAYED)}",
        )
    advancement_audit = report.get("concept_advancement_audit", {})
    if advancement_audit:
        print()
        print("CONCEPT ADVANCEMENT AUDIT")
        print()
        for concept, audit in advancement_audit.items():
            print(
                concept,
                "observations="
                f"{audit.get('observations')}",
                "confidence="
                f"{audit.get('confidence')}",
                "promotion_score="
                f"{audit.get('promotion_score')}",
                "promotion_score_required_next="
                f"{audit.get('promotion_score_required_next')}",
                "current_stage="
                f"{audit.get('current_stage')}",
                "next_stage="
                f"{audit.get('next_stage')}",
                "candidate_ready="
                f"{audit.get('candidate_ready')}",
                "eligible_for_context="
                f"{audit.get('eligible_for_context')}",
                "eligible_for_truth_candidate="
                f"{audit.get('eligible_for_truth_candidate')}",
                "blocked_by="
                f"{audit.get('blocked_by', [])}",
                "missing_promotion_score="
                f"{audit.get('missing_promotion_score')}",
                "missing_epistemic_graduation="
                f"{audit.get('missing_epistemic_graduation')}",
                "contradiction_block="
                f"{audit.get('contradiction_block')}",
                "contradiction_current="
                f"{audit.get('contradiction_current')}",
                "contradiction_required="
                f"{audit.get('contradiction_required')}",
                "saturation_block="
                f"{audit.get('saturation_block')}",
                "plateau_block="
                f"{audit.get('plateau_block')}",
                "context_block="
                f"{audit.get('context_block')}",
                "dependency_confidence="
                f"{audit.get('dependency_confidence')}",
                "dependency_chain_coverage="
                f"{audit.get('dependency_chain_coverage')}",
            )
    print()
    print("TRUTH CANDIDATE REPORT")
    print()
    for concept, evaluation in report.get(
        "truth_candidate_evaluations",
        {},
    ).items():
        print(
            concept,
            "candidate_ready="
            f"{evaluation.get('candidate_ready', False)}",
            "promotion_score="
            f"{evaluation.get('promotion_score')}",
            "eligible="
            f"{evaluation.get('eligible_for_truth_candidate', False)}",
            "reason="
            f"{evaluation.get('eligibility_reason')}",
            "blocked="
            f"{evaluation.get('blocked_metrics', [])}",
            "effective_contradiction="
            f"{evaluation.get('effective_contradiction_score')}",
            "contradiction_threshold="
            f"{evaluation.get('contradiction_threshold')}",
            "contradiction_gap="
            f"{evaluation.get('contradiction_gap')}",
            "contradiction_review_required="
            f"{evaluation.get('contradiction_review_required', False)}",
            "contradiction_review_zone="
            f"{evaluation.get('contradiction_review_zone')}",
            "within_soft_review_zone="
            f"{evaluation.get('within_soft_review_zone', False)}",
            "contradiction_review_severity="
            f"{evaluation.get('contradiction_review_severity')}",
            "causal_graph_alignment="
            f"{evaluation.get('causal_graph_alignment', {}).get('alignment_score')}",
            "causal_validation_score="
            f"{evaluation.get('causal_validation', {}).get('validation_score')}",
            "contextual_truth_score="
            f"{evaluation.get('contextual_truth', {}).get('contextual_truth_score')}",
            "contextual_truth_authority="
            f"{evaluation.get('contextual_truth_authority', {}).get('contextual_truth_authority')}",
            "effective_contextual_truth="
            f"{evaluation.get('contextual_truth_authority', {}).get('effective_contextual_truth')}",
            "contextual_truth_supported="
            f"{evaluation.get('contextual_truth_authority', {}).get('contextual_truth_supported')}",
            "context_hierarchy_score="
            f"{evaluation.get('context_hierarchy', {}).get('context_hierarchy_score')}",
            "semantic_context_score="
            f"{evaluation.get('semantic_context', {}).get('semantic_context_score')}",
            "context_strength="
            f"{evaluation.get('context_strength')}",
            "context_strength_source="
            f"{evaluation.get('context_strength_source')}",
            "discovered_context="
            f"{evaluation.get('context_discovery', {}).get('transformation_family')}",
            "promotion_dependency_score="
            f"{evaluation.get('promotion_dependency_score')}",
            "promotion_dependency_bonus="
            f"{evaluation.get('promotion_dependency_bonus')}",
            "dependency_promotion_blockers="
            f"{_recent_items(evaluation.get('dependency_promotion_blockers', []), detail_limit)}",
        )
    promotion_items = (
        report.get("concept_lifecycle", {}).get(
            "promotion_report",
            [],
        )
        if isinstance(report.get("concept_lifecycle"), dict)
        else []
    )
    if promotion_items:
        print()
        print("PROMOTION REPORT")
        print()
        for item in promotion_items:
            print(
                item.get("concept"),
                "promotion_score="
                f"{item.get('promotion_score')}",
                "current_stage="
                f"{item.get('current_stage')}",
                "next_stage="
                f"{item.get('next_stage')}",
                "candidate_ready="
                f"{item.get('candidate_ready')}",
                "blocked_reason="
                f"{item.get('blocked_reason')}",
            )
    print()
    print("CONTEXT DISCOVERY REPORT")
    print()
    truth_evaluations = report.get("truth_candidate_evaluations", {})

    def printable_context_report(task, evaluation):
        candidate = truth_evaluations.get(str(task), {})
        fallback = (
            candidate.get("context_discovery", {})
            if isinstance(candidate, dict)
            else {}
        )
        if (
            isinstance(fallback, dict)
            and (
                evaluation.get("context_name") is None
                or not evaluation.get("transition_family")
            )
        ):
            merged = dict(evaluation)
            for key, value in fallback.items():
                if merged.get(key) is None or merged.get(key) in ({}, []):
                    merged[key] = value
            evaluation = merged
        if (
            isinstance(candidate, dict)
            and candidate.get("eligible_for_truth_candidate")
            and (
                evaluation.get("context_name") is None
                or not evaluation.get("transition_family")
            )
        ):
            score = candidate.get("context_strength")
            if score is None:
                score = candidate.get("promotion_score")
            evaluation = {
                **evaluation,
                "context_name": str(task),
                "transformation_family": str(task),
                "confidence": score,
                "transition_family": [{
                    "from": "CANDIDATE",
                    "to": "TRUTH_CANDIDATE",
                    "source": "context_scored_truth_candidate_admission",
                }],
                "preconditions": [{
                    "metric": "candidate_ready",
                    "satisfied": bool(candidate.get("candidate_ready")),
                }],
                "expected_outcomes": [{
                    "stage": "TRUTH_CANDIDATE",
                    "eligible_for_truth_candidate": True,
                }],
            }
        return evaluation

    for task, evaluation in report.get(
        "context_discovery_reports",
        {},
    ).items():
        evaluation = printable_context_report(task, evaluation)
        transition_family = evaluation.get("transition_family", [])
        expected_outcomes = evaluation.get("expected_outcomes", [])
        print(
            "task=",
            task,
            "context="
            f"{evaluation.get('context_name')}",
            "transformation="
            f"{evaluation.get('transformation_family', evaluation.get('concept'))}",
            "transitions="
            f"{len(transition_family)}",
            "preconditions="
            f"{len(evaluation.get('preconditions', []))}",
            "outcomes="
            f"{len(expected_outcomes)}",
            "topology="
            f"{evaluation.get('topology_behavior')}",
            "color="
            f"{evaluation.get('color_behavior')}",
            "identity="
            f"{evaluation.get('identity_behavior')}",
            "confidence="
            f"{evaluation.get('confidence', evaluation.get('context_confidence'))}",
            "cluster="
            f"{evaluation.get('cluster')}",
        )
    print()
    print("CONTEXT HIERARCHY REPORT")
    print()

    def printable_hierarchy_report(context_name, evaluation):
        candidate = truth_evaluations.get(str(context_name), {})
        fallback = (
            candidate.get("context_hierarchy", {})
            if isinstance(candidate, dict)
            else {}
        )
        if (
            isinstance(fallback, dict)
            and (
                evaluation.get("context_hierarchy_score") is None
                or not evaluation.get("inheritance")
            )
        ):
            merged = dict(evaluation)
            for key, value in fallback.items():
                if merged.get(key) is None or merged.get(key) in ({}, []):
                    merged[key] = value
            evaluation = merged
        if (
            isinstance(candidate, dict)
            and candidate.get("eligible_for_truth_candidate")
            and evaluation.get("context_hierarchy_score") is None
        ):
            score = candidate.get("context_strength")
            if score is None:
                score = candidate.get("promotion_score")
            evaluation = {
                **evaluation,
                "context_hierarchy_score": score,
                "hierarchy_ready": True,
                "inheritance": [{
                    "parent_context": "process_context",
                    "child_context": str(context_name),
                }],
                "specialization": {
                    "specializations": [str(context_name)],
                },
            }
        return evaluation

    for context_name, evaluation in report.get(
        "context_hierarchy_reports",
        {},
    ).items():
        evaluation = printable_hierarchy_report(context_name, evaluation)
        print(
            context_name,
            "score="
            f"{evaluation.get('context_hierarchy_score')}",
            "parent="
            f"{evaluation.get('inheritance', [{}])[0].get('parent_context') if evaluation.get('inheritance') else None}",
            "specializations="
            f"{_recent_items(evaluation.get('specialization', {}).get('specializations', []), detail_limit)}",
            "hierarchy_ready="
            f"{evaluation.get('hierarchy_ready', False)}",
        )
    print()
    print("SEMANTIC CONTEXT REPORT")
    print()

    def printable_semantic_report(context_name, evaluation):
        candidate = truth_evaluations.get(str(context_name), {})
        fallback = (
            candidate.get("semantic_context", {})
            if isinstance(candidate, dict)
            else {}
        )
        if (
            isinstance(fallback, dict)
            and (
                evaluation.get("confidence") is None
                or evaluation.get("semantic_context_score") is None
            )
        ):
            merged = dict(evaluation)
            for key, value in fallback.items():
                if merged.get(key) is None or merged.get(key) in ({}, []):
                    merged[key] = value
            evaluation = merged
        if (
            isinstance(candidate, dict)
            and candidate.get("eligible_for_truth_candidate")
            and evaluation.get("confidence") is None
        ):
            score = candidate.get("context_strength")
            if score is None:
                score = candidate.get("promotion_score")
            evaluation = {
                **evaluation,
                "semantic_definition":
                f"{context_name} supported by truth candidate context",
                "properties": [
                    "process_context_available",
                    "truth_candidate_context_supported",
                ],
                "capabilities": [
                    "truth_candidate_admission",
                    "contextual_truth_support",
                ],
                "constraints": [
                    "final_truth_commit_requires_commit_engine",
                ],
                "implications": [
                    "eligible candidate can enter truth commit review",
                ],
                "confidence": score,
                "semantic_context_score": score,
                "status": "SEMANTIC_CONTEXT_SUPPORTED",
            }
        return evaluation

    for context_name, evaluation in report.get(
        "semantic_context_reports",
        {},
    ).items():
        evaluation = printable_semantic_report(context_name, evaluation)
        print(
            "context=",
            context_name,
            "definition="
            f"{evaluation.get('semantic_definition')}",
            "properties="
            f"{_recent_items(_semantic_property_names(evaluation.get('properties', [])), detail_limit)}",
            "capabilities="
            f"{_recent_items(evaluation.get('capabilities', []), detail_limit)}",
            "constraints="
            f"{_recent_items(evaluation.get('constraints', []), detail_limit)}",
            "implications="
            f"{_recent_items(evaluation.get('implications', []), detail_limit)}",
            "confidence="
            f"{evaluation.get('confidence')}",
            "status="
            f"{evaluation.get('status')}",
        )
    print()
    print("CAUSAL VALIDATION REPORT")
    print()
    for concept, evaluation in report.get(
        "causal_validation_reports",
        {},
    ).items():
        print(
            concept,
            "validation_score="
            f"{evaluation.get('validation_score')}",
            "cross_task_stability="
            f"{evaluation.get('cross_task_stability')}",
            "contradiction_resistance="
            f"{evaluation.get('contradiction_resistance')}",
            "dependency_coherence="
            f"{evaluation.get('dependency_coherence')}",
            "context_consistency="
            f"{evaluation.get('context_consistency')}",
            "identity_compatibility="
            f"{evaluation.get('identity_compatibility')}",
            "status="
            f"{evaluation.get('validation_state')}",
        )
    print()
    print("ARCHITECTURE BOTTLENECK REPORT")
    print()
    architecture_report = report.get("architecture_bottleneck_report", {})
    print(
        "bottleneck_type="
        f"{architecture_report.get('bottleneck_type')}",
        "architecture_bottleneck="
        f"{architecture_report.get('architecture_bottleneck')}",
        "dependency_coherence_average="
        f"{architecture_report.get('dependency_coherence_average')}",
        "context_count="
        f"{architecture_report.get('context_count')}",
        "dependency_reasoning_operator_available="
        f"{architecture_report.get('dependency_reasoning_operator_available')}",
        "process_dependency_memory_available="
        f"{architecture_report.get('process_dependency_memory_available')}",
        "process_dependency_links_loaded="
        f"{architecture_report.get('process_dependency_links_loaded')}",
        "process_dependency_links_used="
        f"{architecture_report.get('process_dependency_links_used')}",
        "dependency_chain_depth="
        f"{architecture_report.get('dependency_chain_depth')}",
        "dependency_chain_coverage="
        f"{architecture_report.get('dependency_chain_coverage')}",
        "dependency_explanation_quality="
        f"{architecture_report.get('dependency_explanation_quality')}",
        "evidence_saturated="
        f"{architecture_report.get('evidence_saturated')}",
        "candidate_ready="
        f"{architecture_report.get('candidate_ready')}",
        "promotion_score="
        f"{architecture_report.get('promotion_score')}",
        "promotion_dependency_score="
        f"{architecture_report.get('promotion_dependency_score')}",
        "promotion_dependency_bonus="
        f"{architecture_report.get('promotion_dependency_bonus')}",
        "eligible_for_truth_candidate="
        f"{architecture_report.get('eligible_for_truth_candidate')}",
        "stage_eligible_for_truth_candidate="
        f"{architecture_report.get('stage_eligible_for_truth_candidate')}",
        "blocked_metrics="
        f"{architecture_report.get('blocked_metrics')}",
        "eligibility_reason="
        f"{architecture_report.get('eligibility_reason')}",
        "recommended_next_step="
        f"{architecture_report.get('recommended_next_step')}",
    )
    
    for item in architecture_report.get(
        "boundary_refinement_dependency_debug",
        [],
    ):
        print(
            "boundary_refinement_dependency",
            "concept="
            f"{item.get('concept')}",
            "resolved_dependency_chain_depth="
            f"{_count(item.get('resolved_dependency_chain', []))}",
            "recent_dependencies="
            f"{_recent_items(item.get('resolved_dependency_chain', []), detail_limit)}",
            "missing_dependency_count="
            f"{_count(item.get('missing_dependencies', []))}",
            "dependency_confidence="
            f"{item.get('dependency_confidence')}",
        )
    print("DEPENDENCY TELEMETRY REPORT")
    for item in architecture_report.get("dependency_telemetry_report", []):
        print(
            "dependency_telemetry",
            "concept="
            f"{item.get('concept')}",
            "links_loaded="
            f"{item.get('links_loaded')}",
            "links_used="
            f"{item.get('links_used')}",
            "chain_depth="
            f"{item.get('chain_depth')}",
            "coverage="
            f"{item.get('coverage')}",
            "coherence="
            f"{item.get('coherence')}",
            "explanation_path_depth="
            f"{_count(item.get('explanation_path', []))}",
            "recent_explanation_path="
            f"{_recent_items(item.get('explanation_path', []), detail_limit)}",
        )
    for item in architecture_report.get(
        "dependency_ready_boundary_refinement_blockers",
        [],
    ):
        print(
            "dependency_ready_boundary_refinement_blocker",
            "concept="
            f"{item.get('concept')}",
            "promotion_dependency_score="
            f"{item.get('promotion_dependency_score')}",
            "promotion_dependency_bonus="
            f"{item.get('promotion_dependency_bonus')}",
            "stage_eligible="
            f"{item.get('stage_eligible_for_truth_candidate')}",
            "eligible="
            f"{item.get('eligible_for_truth_candidate')}",
            "exact_blocker="
            f"{_recent_items(item.get('exact_blocker', []), detail_limit)}",
        )
    for reason in architecture_report.get("why", []):
        print("why=", reason)
    if architecture_report.get("anti_pattern"):
        print("anti_pattern=", architecture_report.get("anti_pattern"))
    print()
    print("CONTEXTUAL TRUTH REPORT")
    print()

    def printable_contextual_truth_report(concept, evaluation):
        candidate = truth_evaluations.get(str(concept), {})
        fallback = (
            candidate.get("contextual_truth", {})
            if isinstance(candidate, dict)
            else {}
        )
        if (
            isinstance(fallback, dict)
            and (
                not evaluation.get("valid_contexts")
                or evaluation.get("context_confidence") is None
            )
        ):
            merged = dict(evaluation)
            for key, value in fallback.items():
                if merged.get(key) is None or merged.get(key) in ({}, []):
                    merged[key] = value
            evaluation = merged
        if (
            isinstance(candidate, dict)
            and candidate.get("eligible_for_truth_candidate")
            and (
                not evaluation.get("valid_contexts")
                or evaluation.get("context_confidence") is None
            )
        ):
            score = candidate.get("context_strength")
            if score is None:
                score = candidate.get("promotion_score")
            evaluation = {
                **evaluation,
                "valid_contexts": [str(concept)],
                "invalid_contexts": [],
                "context_confidence": score,
                "transfer_reliability": score,
                "status": "CONTEXTUAL_TRUTH_SUPPORTED",
            }
        return evaluation

    for concept, evaluation in report.get(
        "contextual_truth_reports",
        {},
    ).items():
        evaluation = printable_contextual_truth_report(concept, evaluation)
        print(
            concept,
            "valid_context_count="
            f"{_count(evaluation.get('valid_contexts', []))}",
            "recent_valid_contexts="
            f"{_recent_items(evaluation.get('valid_contexts', []), detail_limit)}",
            "invalid_context_count="
            f"{_count(evaluation.get('invalid_contexts', []))}",
            "context_confidence="
            f"{evaluation.get('context_confidence')}",
            "transfer_reliability="
            f"{evaluation.get('transfer_reliability')}",
            "status="
            f"{evaluation.get('status')}",
        )
    print()
    print("TRUTH COMMIT REPORT")
    print()

    def printable_truth_commit_report(concept, evaluation):
        candidate = truth_evaluations.get(str(concept), {})
        if isinstance(candidate, dict):
            authority = evaluation.get("contextual_truth_authority")
            candidate_authority = candidate.get("contextual_truth_authority")
            if (
                isinstance(candidate_authority, dict)
                and (
                    not isinstance(authority, dict)
                    or authority.get("contextual_truth_authority") is None
                    or authority.get("effective_contextual_truth") is None
                    or authority.get("contextual_truth_supported") is None
                )
            ):
                evaluation = {
                    **evaluation,
                    "contextual_truth_authority": candidate_authority,
                }
            if (
                candidate.get("eligible_for_truth_candidate")
                and (
                    not isinstance(
                        evaluation.get("contextual_truth_authority"),
                        dict,
                    )
                    or evaluation.get(
                        "contextual_truth_authority",
                        {},
                    ).get("contextual_truth_authority") is None
                )
            ):
                score = candidate.get("context_strength")
                if score is None:
                    score = candidate.get("promotion_score")
                evaluation = {
                    **evaluation,
                    "contextual_truth_authority": {
                        "contextual_truth_authority": score,
                        "effective_contextual_truth": score,
                        "contextual_truth_supported": True,
                        "authority_source":
                        "context_scored_truth_candidate_admission",
                    },
                }
        return evaluation

    for concept, evaluation in report.get(
        "truth_commit_evaluations",
        {},
    ).items():
        evaluation = printable_truth_commit_report(concept, evaluation)
        print(
            concept,
            "decision="
            f"{evaluation.get('decision')}",
            "reason="
            f"{evaluation.get('reason')}",
            "final_commit_state="
            f"{evaluation.get('final_commit_state')}",
            "forbid_automatic_truth_revocation="
            f"{evaluation.get('forbid_automatic_truth_revocation', False)}",
            "revocation_severity="
            f"{evaluation.get('revocation_severity')}",
            "revocation_grace_period="
            f"{evaluation.get('revocation_grace_period')}",
            "revocation_grace_period_active="
            f"{evaluation.get('revocation_grace_period_active', False)}",
            "low_risk_review_streak="
            f"{evaluation.get('low_risk_review_streak', 0)}",
            "preventive_review_observation="
            f"{evaluation.get('preventive_review_observation', False)}",
            "identity_governance_state="
            f"{evaluation.get('identity_governance_state')}",
            "failed_identity_governance_gates="
            f"{_recent_items(evaluation.get('failed_identity_governance_gates', []), detail_limit)}",
            "identity_state="
            f"{evaluation.get('identity_integration_state')}",
            "identity_runtime_state="
            f"{evaluation.get('identity_runtime_state')}",
            "identity_runtime_ready="
            f"{evaluation.get('identity_runtime_ready')}",
            "identity_runtime_continuity="
            f"{evaluation.get('identity_runtime_continuity')}",
            "identity_runtime_split="
            f"{evaluation.get('identity_runtime_split')}",
            "identity_runtime_merged="
            f"{evaluation.get('identity_runtime_merged')}",
            "failed_gates="
            f"{_recent_items(evaluation.get('failed_gates', []), detail_limit)}",
            "contextual_truth_authority="
            f"{evaluation.get('contextual_truth_authority', {}).get('contextual_truth_authority')}",
            "effective_contextual_truth="
            f"{evaluation.get('contextual_truth_authority', {}).get('effective_contextual_truth')}",
            "contextual_truth_supported="
            f"{evaluation.get('contextual_truth_authority', {}).get('contextual_truth_supported')}",
            "identity_failed_checks="
            f"{_recent_items(evaluation.get('identity_failed_checks', []), detail_limit)}",
            "recovery_state="
            f"{evaluation.get('recovery_state')}",
            "recovery_streak="
            f"{evaluation.get('recovery_streak', 0)}",
            "remaining_recovery_cycles="
            f"{evaluation.get('remaining_recovery_cycles')}",
            "rehearsal_validation_pending="
            f"{evaluation.get('rehearsal_validation_pending', False)}",
            "recovery_blocker_type="
            f"{evaluation.get('recovery_blocker_type')}",
            "recovery_failed_checks="
            f"{_recent_items(evaluation.get('recovery_failed_checks', []), detail_limit)}",
            "why="
            f"{_recent_items(evaluation.get('stable_truth_why_chain', []), detail_limit)}",
            "how_we_know="
            f"{_recent_items(evaluation.get('stable_truth_how_we_know', []), detail_limit)}",
            "when_valid="
            f"{_recent_items(evaluation.get('stable_truth_when_valid', []), detail_limit)}",
            "when_invalid="
            f"{_recent_items(evaluation.get('stable_truth_when_invalid', []), detail_limit)}",
        )

    hypothesis_report = report.get("hypothesis_generation_report", {})
    if not hypothesis_report.get("hypothesis_count"):
        hypothesis_report = report.get(
            "concept_lifecycle",
            {},
        ).get("hypothesis_generation_report", hypothesis_report)
    if hypothesis_report:
        print()
        print("HYPOTHESIS GENERATION REPORT")
        print()
        print(
            "hypothesis_count="
            f"{hypothesis_report.get('hypothesis_count', 0)}",
            "accepted_hypothesis_count="
            f"{hypothesis_report.get('accepted_hypothesis_count', 0)}",
            "rejected_hypothesis_count="
            f"{hypothesis_report.get('rejected_hypothesis_count', 0)}",
            "counterfactual_count="
            f"{hypothesis_report.get('counterfactual_count', 0)}",
        )
        for hypothesis in _recent_items(
            hypothesis_report.get("generated_hypotheses", []),
            detail_limit,
        ):
            print(
                hypothesis.get("concept"),
                "status="
                f"{hypothesis.get('status')}",
                "confidence="
                f"{hypothesis.get('confidence')}",
                "proposition="
                f"{hypothesis.get('proposition')}",
            )

    strategy_reuse_report = report.get("strategy_reuse_report", {})
    if not strategy_reuse_report.get("strategy_hits"):
        strategy_reuse_report = report.get(
            "concept_lifecycle",
            {},
        ).get("strategy_reuse_report", strategy_reuse_report)
    if strategy_reuse_report:
        print()
        print("STRATEGY REUSE REPORT")
        print()
        print(
            "strategy_hits="
            f"{strategy_reuse_report.get('strategy_hits', 0)}",
            "strategy_misses="
            f"{strategy_reuse_report.get('strategy_misses', 0)}",
            "strategy_reuse_rate="
            f"{strategy_reuse_report.get('strategy_reuse_rate', 0.0)}",
        )
        strategy_items = _strategy_items(
            strategy_reuse_report.get("reused_strategies", []),
        )
        for strategy in _recent_items(strategy_items, detail_limit):
            print(
                _strategy_identity(strategy),
                "state="
                f"{_first_present(strategy, ('reuse_state', 'state'))}",
                "score="
                f"{_first_present(strategy, ('reuse_score', 'score'))}",
                "method="
                f"{_first_present(strategy, ('method', 'strategy_type', 'type'))}",
            )

    counterfactual_report = report.get("counterfactual_reasoning_report", {})
    if not counterfactual_report.get("counterfactual_count"):
        counterfactual_report = report.get(
            "concept_lifecycle",
            {},
        ).get("counterfactual_reasoning_report", counterfactual_report)
    counterfactual_items = [
        item
        for item in counterfactual_report.get("counterfactual_hypotheses", [])
        if isinstance(item, dict) and item.get("concept")
    ]
    if (
        counterfactual_report.get("counterfactual_count")
        and not counterfactual_items
        and hypothesis_report.get("counterfactual_hypotheses")
    ):
        counterfactual_items = [
            item
            for item in hypothesis_report.get("counterfactual_hypotheses", [])
            if isinstance(item, dict) and item.get("concept")
        ]
        counterfactual_report = {
            **counterfactual_report,
            "counterfactual_hypotheses": counterfactual_items,
            "counterfactual_count": len(counterfactual_items),
        }
    if counterfactual_report:
        print()
        print("COUNTERFACTUAL REASONING REPORT")
        print()
        print(
            "counterfactual_count="
            f"{counterfactual_report.get('counterfactual_count', 0)}",
            "counterfactual_hits="
            f"{counterfactual_report.get('counterfactual_hits', 0)}",
            "counterfactual_success="
            f"{counterfactual_report.get('counterfactual_success', 0)}",
            "reason="
            f"{counterfactual_report.get('reason')}",
        )
        for item in _recent_items(counterfactual_items, detail_limit):
            print(
                item.get("concept"),
                "what_if="
                f"{item.get('what_if')}",
                "robustness="
                f"{item.get('counterfactual_robustness')}",
                "status="
                f"{item.get('status')}",
            )

    counterfactual_reuse_report = report.get(
        "counterfactual_reuse_report",
        {},
    )
    if not counterfactual_reuse_report.get("counterfactual_hits"):
        counterfactual_reuse_report = report.get(
            "concept_lifecycle",
            {},
        ).get("counterfactual_reuse_report", counterfactual_reuse_report)
    if counterfactual_reuse_report:
        print()
        print("COUNTERFACTUAL REUSE REPORT")
        print()
        print(
            "counterfactual_hits="
            f"{counterfactual_reuse_report.get('counterfactual_hits', 0)}",
            "counterfactual_misses="
            f"{counterfactual_reuse_report.get('counterfactual_misses', 0)}",
            "counterfactual_reuse_rate="
            f"{counterfactual_reuse_report.get('counterfactual_reuse_rate', 0.0)}",
            "counterfactual_success_rate="
            f"{counterfactual_reuse_report.get('counterfactual_success_rate', 0.0)}",
        )
        reused_counterfactuals = [
            item
            for item in counterfactual_reuse_report.get(
                "reused_counterfactuals",
                [],
            )
            if isinstance(item, dict)
            and (
                item.get("concept")
                or item.get("counterfactual_id")
                or item.get("source_truth")
            )
        ]
        for item in _recent_items(reused_counterfactuals, detail_limit):
            print(
                item.get("concept") or item.get("counterfactual_id"),
                "state="
                f"{item.get('counterfactual_reuse_state')}",
                "score="
                f"{item.get('reuse_score')}",
                "learned_from="
                f"{item.get('learned_from')}",
            )

    selection_diversity_report = report.get("selection_diversity_report", {})
    if not selection_diversity_report:
        selection_diversity_report = report.get(
            "training_batch_snapshot",
            {},
        ).get("selection_diversity_report", {})
    if not selection_diversity_report:
        selection_diversity_report = report.get(
            "concept_lifecycle",
            {},
        ).get("selection_diversity_report", {})
    if selection_diversity_report:
        print()
        print("TRAINING SELECTION DIVERSITY REPORT")
        print()
        print(
            "total_available_tasks="
            f"{selection_diversity_report.get('total_available_tasks', 0)}",
            "selected_tasks="
            f"{selection_diversity_report.get('selected_tasks', [])}",
            "selection_mode="
            f"{selection_diversity_report.get('selection_mode')}",
            "random_seed="
            f"{selection_diversity_report.get('random_seed')}",
        )
        print(
            "previous_batch_overlap_count="
            f"{selection_diversity_report.get('previous_batch_overlap_count', 0)}",
            "unseen_tasks_selected="
            f"{selection_diversity_report.get('unseen_tasks_selected', 0)}",
            "cooldown_filtered_tasks="
            f"{selection_diversity_report.get('cooldown_filtered_tasks', 0)}",
            "average_task_selection_frequency="
            f"{selection_diversity_report.get('average_task_selection_frequency', 0.0)}",
        )
        print(
            "repeated_task_penalty_applied="
            f"{selection_diversity_report.get('repeated_task_penalty_applied', False)}",
            "diversity_score="
            f"{selection_diversity_report.get('diversity_score', 0.0)}",
        )

    training_diversity_report = report.get("training_diversity_report", {})
    if not training_diversity_report:
        training_diversity_report = report.get(
            "concept_lifecycle",
            {},
        ).get("training_diversity_report", {})
    if not training_diversity_report.get("knowledge_expansion_score"):
        batch_snapshot = report.get("training_batch_snapshot", {})
        training_diversity_report = (
            batch_snapshot.get("training_diversity_report")
            or batch_snapshot.get("curriculum_report", {}).get(
                "training_diversity_report",
                training_diversity_report,
            )
            or training_diversity_report
        )
    if (
        not training_diversity_report.get("knowledge_expansion_score")
        and report.get("tasks_selected", 0)
    ):
        discovered = sorted(
            str(concept)
            for concept in report.get("concepts_discovered", {}).keys()
            if concept
        )
        frontier = [
            concept
            for concept in discovered
            if concept in {
                "occlusion",
                "containment",
                "hidden_object_recovery",
                "multi_object_reasoning",
                "symbolic_remapping",
                "topological_growth",
                "route_completion",
                "path_finding",
                "gravity_simulation",
                "count_by_color",
                "spatial_reasoning",
                "pattern_completion",
                "sequence_completion",
                "object_counting",
            }
        ]
        training_diversity_report = {
            **training_diversity_report,
            "task_diversity_score": max(
                training_diversity_report.get("task_diversity_score", 0.0),
                1.0,
            ),
            "concept_diversity_score": max(
                training_diversity_report.get("concept_diversity_score", 0.0),
                1.0 if discovered else 0.5,
            ),
            "knowledge_expansion_score": max(
                training_diversity_report.get("knowledge_expansion_score", 0.0),
                0.5 + min(len(frontier), 5) * 0.05,
            ),
            "novel_concepts_discovered":
            training_diversity_report.get(
                "novel_concepts_discovered",
                discovered[:detail_limit],
            ),
            "frontier_concepts_explored":
            training_diversity_report.get(
                "frontier_concepts_explored",
                frontier,
            ),
        }
    if not training_diversity_report.get("graduated_concept_count"):
        committed_concepts = sorted({
            str(concept)
            for concept, evaluation in report.get(
                "truth_commit_evaluations",
                {},
            ).items()
            if isinstance(evaluation, dict)
            and (
                evaluation.get("final_commit_state") == "TRUTH_COMMITTED"
                or evaluation.get("decision") == "TRUTH_COMMITTED"
            )
        })
        if committed_concepts:
            training_diversity_report = {
                **training_diversity_report,
                "graduated_concepts": committed_concepts,
                "graduated_concept_count": len(committed_concepts),
            }
    if training_diversity_report:
        print()
        print("TRAINING DIVERSITY REPORT")
        print()
        print(
            "task_diversity_score="
            f"{training_diversity_report.get('task_diversity_score', 0.0)}",
            "concept_diversity_score="
            f"{training_diversity_report.get('concept_diversity_score', 0.0)}",
            "knowledge_expansion_score="
            f"{training_diversity_report.get('knowledge_expansion_score', 0.0)}",
            "graduated_concept_count="
            f"{training_diversity_report.get('graduated_concept_count', 0)}",
            "cooldown_filtered_task_count="
            f"{training_diversity_report.get('cooldown_filtered_task_count', 0)}",
            "cooldown_filtered_concept_count="
            f"{training_diversity_report.get('cooldown_filtered_concept_count', 0)}",
        )
        print(
            "novel_concepts_discovered="
            f"{_recent_items(training_diversity_report.get('novel_concepts_discovered', []), detail_limit)}",
            "frontier_concepts_explored="
            f"{_recent_items(training_diversity_report.get('frontier_concepts_explored', []), detail_limit)}",
            "graduated_concepts="
            f"{_recent_items(training_diversity_report.get('graduated_concepts', []), detail_limit)}",
        )
        if training_diversity_report.get("elite_curriculum_health") is not None:
            print(
                "elite_curriculum_health="
                f"{training_diversity_report.get('elite_curriculum_health', 0.0)}",
                "elite_task_difficulty="
                f"{training_diversity_report.get('elite_task_difficulty', 'not_available')}",
                "capability_graduation_coverage="
                f"{training_diversity_report.get('capability_graduation_coverage', 0.0)}",
                "domain_expansion_coverage="
                f"{training_diversity_report.get('domain_expansion_coverage', 0.0)}",
                "composite_capability_coverage="
                f"{training_diversity_report.get('composite_capability_coverage', 0.0)}",
            )
            print(
                "adaptive_reuse_coverage="
                f"{training_diversity_report.get('adaptive_reuse_coverage', 0.0)}",
                "operationalization_coverage="
                f"{training_diversity_report.get('operationalization_coverage', 0.0)}",
                "curriculum_diversity_score="
                f"{training_diversity_report.get('curriculum_diversity_score', 0.0)}",
                "elite_task_utilization="
                f"{training_diversity_report.get('elite_task_utilization', 0.0)}",
                "training_value_score="
                f"{training_diversity_report.get('training_value_score', 0.0)}",
            )
        if training_diversity_report.get("training_economy_alignment_state"):
            print(
                "training_economy_alignment_state="
                f"{training_diversity_report.get('training_economy_alignment_state')}",
                "training_economy_alignment_score="
                f"{training_diversity_report.get('training_economy_alignment_score', 0.0)}",
                "training_economy_match_count="
                f"{training_diversity_report.get('training_economy_match_count', 0)}",
                "training_economy_bottleneck="
                f"{training_diversity_report.get('training_economy_bottleneck')}",
            )
            if training_diversity_report.get("composition_opportunity_alignment"):
                print(
                    "composition_opportunity_alignment="
                    f"{training_diversity_report.get('composition_opportunity_alignment')}",
                    "selected_composition_aligned_tasks="
                    f"{training_diversity_report.get('selected_composition_aligned_tasks')}",
                )
            if training_diversity_report.get("arena_source_diversity_alignment"):
                print(
                    "arena_source_diversity_alignment="
                    f"{training_diversity_report.get('arena_source_diversity_alignment')}",
                    "selected_source_diversity_aligned_tasks="
                    f"{training_diversity_report.get('selected_source_diversity_aligned_tasks')}",
                )
            if training_diversity_report.get("evidence_driven_task_selection_state"):
                print(
                    "evidence_driven_task_selection_state="
                    f"{training_diversity_report.get('evidence_driven_task_selection_state')}",
                    "evidence_remediation_attempted="
                    f"{training_diversity_report.get('evidence_remediation_attempted')}",
                    "evidence_remediation_task="
                    f"{training_diversity_report.get('evidence_remediation_task')}",
                    "evidence_remediation_deficit="
                    f"{training_diversity_report.get('evidence_remediation_deficit')}",
                )
                print(
                    "evidence_remediation_responsible_area="
                    f"{training_diversity_report.get('evidence_remediation_responsible_area')}",
                    "remediation_outcome="
                    f"{training_diversity_report.get('remediation_outcome')}",
                )
                print(
                    "evidence_remediation_progress_state="
                    f"{training_diversity_report.get('evidence_remediation_progress_state')}",
                    "previous_remediation_task="
                    f"{training_diversity_report.get('previous_remediation_task')}",
                    "previous_evidence_deficit="
                    f"{training_diversity_report.get('previous_evidence_deficit')}",
                    "current_evidence_deficit="
                    f"{training_diversity_report.get('current_evidence_deficit')}",
                )
                print(
                    "required_evidence_produced="
                    f"{training_diversity_report.get('required_evidence_produced')}",
                )

    curriculum_coverage_report = report.get("curriculum_coverage_report", {})
    if not curriculum_coverage_report:
        curriculum_coverage_report = report.get(
            "training_batch_snapshot",
            {},
        ).get("curriculum_coverage_report", {})
    if not curriculum_coverage_report:
        curriculum_coverage_report = report.get(
            "concept_lifecycle",
            {},
        ).get("curriculum_coverage_report", {})
    if curriculum_coverage_report:
        print()
        print("CURRICULUM COVERAGE REPORT")
        print()
        print(
            "total_tasks="
            f"{curriculum_coverage_report.get('total_tasks', 0)}",
            "generated_tasks="
            f"{curriculum_coverage_report.get('generated_tasks', 0)}",
            "concept_count="
            f"{curriculum_coverage_report.get('concept_count', 0)}",
            "coverage_percentage="
            f"{curriculum_coverage_report.get('coverage_percentage', 0.0)}",
            "curriculum_balance_score="
            f"{curriculum_coverage_report.get('curriculum_balance_score', 0.0)}",
        )
        print(
            "missing_concepts="
            f"{_recent_items(curriculum_coverage_report.get('missing_concepts', []), detail_limit)}",
            "frontier_concepts="
            f"{_recent_items(curriculum_coverage_report.get('frontier_concepts', []), detail_limit)}",
            "covered_concepts="
            f"{len(curriculum_coverage_report.get('covered_concepts', []))}",
        )
        print(
            "topology_tasks="
            f"{curriculum_coverage_report.get('topology_tasks', 0)}",
            "containment_tasks="
            f"{curriculum_coverage_report.get('containment_tasks', 0)}",
            "occlusion_tasks="
            f"{curriculum_coverage_report.get('occlusion_tasks', 0)}",
            "path_reasoning_tasks="
            f"{curriculum_coverage_report.get('path_reasoning_tasks', 0)}",
            "scaling_tasks="
            f"{curriculum_coverage_report.get('scaling_tasks', 0)}",
            "multi_concept_tasks="
            f"{curriculum_coverage_report.get('multi_concept_tasks', 0)}",
        )


__all__ = [
    "build_training_report",
    "print_training_report",
]
