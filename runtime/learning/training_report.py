def build_training_report(
    training_batch=None,
    training_assistant_report=None,
    multi_task_results=None,
    ledger_report=None,
    concept_lifecycle_report=None,
):
    training_batch = training_batch or {}
    training_assistant_report = training_assistant_report or {}
    multi_task_results = list(multi_task_results or [])
    ledger_report = ledger_report or {}
    concept_lifecycle_report = concept_lifecycle_report or {}

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

    concept_memory = {}
    for concept in ledger_report.get("concepts", []):
        concept_name = concept.get("concept")
        if not concept_name:
            continue
        ledger_average_contradiction = lifecycle_by_concept.get(
            str(concept_name),
            {},
        ).get("average_contradiction_score", 1.0)
        concept_memory[str(concept_name)] = {
            "used_task_count": concept.get("used_task_count", 0),
            "task_ids": list(concept.get("used_task_ids", [])),
            "independent_success_rate":
            concept.get("independent_success_rate", 0.0),
            "lifecycle_state":
            lifecycle_by_concept.get(
                str(concept_name),
                {},
            ).get("state", "DISCOVERING"),
            "preliminary_truth_candidate_ready":
            lifecycle_by_concept.get(
                str(concept_name),
                {},
            ).get("preliminary_truth_candidate_ready", False),
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
    candidate_evaluations = {}
    truth_commit_evaluations = {}

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
        cognition_report = result.get("epistemic_cognition_report", {})
        return [
            result.get("truth_candidate_report", {}),
            cognition_report.get("truth_candidate_engine", {}),
        ]

    def record_candidate_evaluation(evaluation, source):
        concept = evaluation.get("concept")
        if not concept:
            return
        contradiction_metric = candidate_metric(
            evaluation,
            "contradiction_score",
        )
        context_strength = context_strength_for_evaluation(evaluation)
        candidate_evaluations[str(concept)] = {
            "concept": str(concept),
            "candidate_state": evaluation.get("candidate_state"),
            "eligible_for_truth_candidate":
            evaluation.get("eligible_for_truth_candidate", False),
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

    for item in multi_task_results:
        result = item.get("result", {})
        for report_index, report in enumerate(candidate_report_sources(result)):
            source = (
                "truth_candidate_report"
                if report_index == 0
                else "epistemic_cognition_report.truth_candidate_engine"
            )
            for evaluation in report.get("evaluations", []):
                record_candidate_evaluation(evaluation, source)
        for evaluation in result.get(
            "epistemic_cognition_report",
            {},
        ).get("evaluations", []):
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
    causal_validation_reports = {}
    for item in multi_task_results:
        result = item.get("result", {})
        for evaluation in result.get(
            "epistemic_cognition_report",
            {},
        ).get(
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
    for item in multi_task_results:
        result = item.get("result", {})
        for evaluation in result.get(
            "epistemic_cognition_report",
            {},
        ).get(
            "contextual_truth_engine",
            {},
        ).get("evaluations", []):
            concept = evaluation.get("truth")
            if concept:
                contextual_truth_reports[str(concept)] = evaluation
        for evaluation in result.get(
            "epistemic_cognition_report",
            {},
        ).get(
            "context_discovery_engine",
            {},
        ).get("evaluations", []):
            task = evaluation.get("task")
            if task:
                context_discovery_reports[str(task)] = evaluation
        for evaluation in result.get(
            "epistemic_cognition_report",
            {},
        ).get(
            "context_hierarchy_engine",
            {},
        ).get("evaluations", []):
            contexts = evaluation.get("contexts", [])
            context_name = (
                contexts[0].get("context_name")
                if contexts
                else evaluation.get("system")
            )
            if context_name:
                context_hierarchy_reports[str(context_name)] = evaluation
        for evaluation in result.get(
            "epistemic_cognition_report",
            {},
        ).get(
            "semantic_context_reasoner",
            {},
        ).get("evaluations", []):
            context_name = evaluation.get("context")
            if context_name:
                semantic_context_reports[str(context_name)] = evaluation
    for concept, evaluation in candidate_evaluations.items():
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
    architecture_bottleneck_report = build_architecture_bottleneck_report(
        causal_validation_reports,
        context_discovery_reports,
        semantic_context_reports,
        contextual_truth_reports,
        candidate_evaluations,
    )
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
        "multi_task_results": task_results,
        "concepts_discovered": {
            concept: stats["used_task_count"]
            for concept, stats in concept_memory.items()
        },
        "concept_memory": concept_memory,
        "concept_lifecycle": concept_lifecycle_report,
        "truth_candidate_evaluations":
        candidate_evaluations,
        "truth_commit_evaluations":
        truth_commit_evaluations,
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
    }


def print_training_report(report):
    print("TRAINING REPORT")
    print()
    print("tasks_selected:", report.get("tasks_selected", 0))
    print("tasks_executed:", report.get("tasks_executed", []))
    print("successful_tasks:", report.get("successful_tasks", 0))
    print("failed_tasks:", report.get("failed_tasks", 0))
    print("multi_task_results:", report.get("multi_task_results", []))
    print("concepts_discovered:", report.get("concepts_discovered", {}))
    print()
    print("CONCEPT DEBUG REPORT")
    print()
    for concept, stats in report.get("concept_memory", {}).items():
        print(
            concept,
            stats.get("used_task_count", 0),
            stats.get("lifecycle_state", "DISCOVERING"),
            "candidate_ready="
            f"{stats.get('preliminary_truth_candidate_ready', False)}",
            "ledger_average_contradiction="
            f"{stats.get('ledger_average_contradiction_score', 1.0)}",
            stats.get("task_ids", []),
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
            f"{evaluation.get('dependency_promotion_blockers', [])}",
        )
    print()
    print("CONTEXT DISCOVERY REPORT")
    print()
    for task, evaluation in report.get(
        "context_discovery_reports",
        {},
    ).items():
        print(
            "task=",
            task,
            "transformation="
            f"{evaluation.get('transformation_family')}",
            "topology="
            f"{evaluation.get('topology_behavior')}",
            "color="
            f"{evaluation.get('color_behavior')}",
            "identity="
            f"{evaluation.get('identity_behavior')}",
            "confidence="
            f"{evaluation.get('confidence')}",
            "cluster="
            f"{evaluation.get('cluster')}",
        )
    print()
    print("CONTEXT HIERARCHY REPORT")
    print()
    for context_name, evaluation in report.get(
        "context_hierarchy_reports",
        {},
    ).items():
        print(
            context_name,
            "score="
            f"{evaluation.get('context_hierarchy_score')}",
            "parent="
            f"{evaluation.get('inheritance', [{}])[0].get('parent_context') if evaluation.get('inheritance') else None}",
            "specializations="
            f"{evaluation.get('specialization', {}).get('specializations', [])}",
            "hierarchy_ready="
            f"{evaluation.get('hierarchy_ready', False)}",
        )
    print()
    print("SEMANTIC CONTEXT REPORT")
    print()
    for context_name, evaluation in report.get(
        "semantic_context_reports",
        {},
    ).items():
        print(
            "context=",
            context_name,
            "definition="
            f"{evaluation.get('semantic_definition')}",
            "properties="
            f"{[item.get('property_name') for item in evaluation.get('properties', [])]}",
            "capabilities="
            f"{evaluation.get('capabilities', [])}",
            "constraints="
            f"{evaluation.get('constraints', [])}",
            "implications="
            f"{evaluation.get('implications', [])}",
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
            "resolved_dependency_chain="
            f"{item.get('resolved_dependency_chain', [])}",
            "missing_dependencies="
            f"{item.get('missing_dependencies', [])}",
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
            "explanation_path="
            f"{item.get('explanation_path')}",
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
            f"{item.get('exact_blocker', [])}",
        )
    for reason in architecture_report.get("why", []):
        print("why=", reason)
    if architecture_report.get("anti_pattern"):
        print("anti_pattern=", architecture_report.get("anti_pattern"))
    print()
    print("CONTEXTUAL TRUTH REPORT")
    print()
    for concept, evaluation in report.get(
        "contextual_truth_reports",
        {},
    ).items():
        print(
            concept,
            "valid_contexts="
            f"{evaluation.get('valid_contexts', [])}",
            "invalid_contexts="
            f"{evaluation.get('invalid_contexts', [])}",
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
    for concept, evaluation in report.get(
        "truth_commit_evaluations",
        {},
    ).items():
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
            f"{evaluation.get('failed_identity_governance_gates', [])}",
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
            f"{evaluation.get('failed_gates', [])}",
            "contextual_truth_authority="
            f"{evaluation.get('contextual_truth_authority', {}).get('contextual_truth_authority')}",
            "effective_contextual_truth="
            f"{evaluation.get('contextual_truth_authority', {}).get('effective_contextual_truth')}",
            "contextual_truth_supported="
            f"{evaluation.get('contextual_truth_authority', {}).get('contextual_truth_supported')}",
            "identity_failed_checks="
            f"{evaluation.get('identity_failed_checks', [])}",
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
            f"{evaluation.get('recovery_failed_checks', [])}",
            "why="
            f"{evaluation.get('stable_truth_why_chain', [])}",
            "how_we_know="
            f"{evaluation.get('stable_truth_how_we_know', [])}",
            "when_valid="
            f"{evaluation.get('stable_truth_when_valid', [])}",
            "when_invalid="
            f"{evaluation.get('stable_truth_when_invalid', [])}",
        )


__all__ = [
    "build_training_report",
    "print_training_report",
]
