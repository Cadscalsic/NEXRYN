from core.epistemic_models import clamp


class DependencyChainAlignmentEngine:
    """
    Aligns runtime-discovered dependency chains with typed process memory.

    This engine does NOT promote truths.
    It only produces an alignment report and optional memory-ready links.
    """

    MINIMUM_ALIGNMENT_CONFIDENCE = 0.84
    MINIMUM_RUNTIME_CONFIDENCE = 0.80
    MINIMUM_CHAIN_COVERAGE = 0.70

    PROCESS_CONCEPTS = {
        "growth",
        "propagation",
        "replication",
        "topological_growth",
        "directional_motion",
        "object_identity_preservation",
        "duplication",
    }

    def _safe_dict(self, value):
        return value if isinstance(value, dict) else {}

    def _nodes_from_runtime(self, runtime_chain):
        runtime_chain = self._safe_dict(runtime_chain)

        for key in [
            "resolved_dependency_chain",
            "dependency_chain",
            "runtime_dependency_chain",
            "observed_dependency_chain",
        ]:
            value = runtime_chain.get(key)
            if isinstance(value, list):
                return [str(item) for item in value if item]

            if isinstance(value, dict):
                nodes = value.get("nodes")
                if isinstance(nodes, list):
                    return [str(item) for item in nodes if item]

        return []

    def _nodes_from_memory(self, memory_chain):
        memory_chain = self._safe_dict(memory_chain)

        value = memory_chain.get("resolved_dependency_chain")
        if isinstance(value, list):
            return [str(item) for item in value if item]

        value = memory_chain.get("dependency_chain")
        if isinstance(value, dict):
            nodes = value.get("nodes")
            if isinstance(nodes, list):
                return [str(item) for item in nodes if item]

        if isinstance(value, list):
            return [str(item) for item in value if item]

        return []

    def _overlap_score(self, runtime_nodes, memory_nodes):
        if not runtime_nodes or not memory_nodes:
            return 0.0

        runtime_set = set(runtime_nodes)
        memory_set = set(memory_nodes)
        overlap = runtime_set & memory_set

        return clamp(
            len(overlap)
            / max(len(runtime_set | memory_set), 1)
        )

    def _ordered_score(self, runtime_nodes, memory_nodes):
        if not runtime_nodes or not memory_nodes:
            return 0.0

        memory_positions = {
            node: index
            for index, node in enumerate(memory_nodes)
        }

        ordered_hits = []
        for node in runtime_nodes:
            if node in memory_positions:
                ordered_hits.append(memory_positions[node])

        if len(ordered_hits) <= 1:
            return clamp(len(ordered_hits) / max(len(runtime_nodes), 1))

        monotonic = all(
            left <= right
            for left, right in zip(ordered_hits, ordered_hits[1:])
        )

        base = len(ordered_hits) / max(len(runtime_nodes), 1)
        return clamp(base if monotonic else base * 0.65)

    def _bridge_nodes(self, runtime_nodes, memory_nodes):
        runtime_set = set(runtime_nodes)
        memory_set = set(memory_nodes)

        return {
            "runtime_only_nodes": [
                node for node in runtime_nodes
                if node not in memory_set
            ],
            "memory_only_nodes": [
                node for node in memory_nodes
                if node not in runtime_set
            ],
            "shared_nodes": [
                node for node in runtime_nodes
                if node in memory_set
            ],
        }

    def _memory_ready_links(self, concept, runtime_nodes, confidence):
        links = []

        if len(runtime_nodes) < 2:
            return links

        for source, target in zip(runtime_nodes, runtime_nodes[1:]):
            links.append({
                "process": concept,
                "source": source,
                "relation": "supports",
                "target": target,
                "confidence": confidence,
                "metadata": {
                    "source": "dependency_chain_alignment_engine",
                    "runtime_chain_aligned": True,
                    "persistent_write_requires_governance": True,
                },
            })

        return links

    def evaluate(
        self,
        concept,
        runtime_dependency_chain=None,
        process_dependency_memory=None,
        context=None,
    ):
        context = self._safe_dict(context)
        concept = str(concept or "").strip()

        runtime_dependency_chain = self._safe_dict(
            runtime_dependency_chain
            or context.get("runtime_dependency_chain")
            or context.get("dependency_reasoning")
            or context.get("dependency_reasoning_report")
            or context.get("process_dependency_memory")
        )

        process_dependency_memory = self._safe_dict(
            process_dependency_memory
            or context.get("process_dependency_memory")
        )

        runtime_nodes = self._nodes_from_runtime(runtime_dependency_chain)
        memory_nodes = self._nodes_from_memory(process_dependency_memory)

        runtime_confidence = clamp(
            runtime_dependency_chain.get(
                "dependency_confidence",
                runtime_dependency_chain.get(
                    "confidence",
                    runtime_dependency_chain.get(
                        "promotion_dependency_score",
                        0.0,
                    ),
                ),
            )
        )

        memory_confidence = clamp(
            process_dependency_memory.get(
                "dependency_confidence",
                0.0,
            )
        )

        runtime_coverage = clamp(
            runtime_dependency_chain.get(
                "dependency_chain_coverage",
                0.0,
            )
        )

        memory_coverage = clamp(
            process_dependency_memory.get(
                "dependency_chain_coverage",
                0.0,
            )
        )

        overlap_score = self._overlap_score(runtime_nodes, memory_nodes)
        ordered_score = self._ordered_score(runtime_nodes, memory_nodes)

        alignment_confidence = clamp(
            overlap_score * 0.34
            + ordered_score * 0.26
            + max(runtime_confidence, memory_confidence) * 0.24
            + max(runtime_coverage, memory_coverage) * 0.16
        )

        bridge = self._bridge_nodes(runtime_nodes, memory_nodes)

        applicable = concept in self.PROCESS_CONCEPTS

        alignment_ready = (
            applicable
            and alignment_confidence >= self.MINIMUM_ALIGNMENT_CONFIDENCE
            and max(runtime_confidence, memory_confidence)
            >= self.MINIMUM_RUNTIME_CONFIDENCE
            and max(runtime_coverage, memory_coverage)
            >= self.MINIMUM_CHAIN_COVERAGE
            and len(runtime_nodes) >= 2
        )

        memory_ready_links = (
            self._memory_ready_links(
                concept,
                runtime_nodes,
                alignment_confidence,
            )
            if alignment_ready
            else []
        )

        missing_alignment_requirements = []
        if not applicable:
            missing_alignment_requirements.append(
                "concept_not_process_dependency_applicable"
            )
        if alignment_confidence < self.MINIMUM_ALIGNMENT_CONFIDENCE:
            missing_alignment_requirements.append(
                "alignment_confidence_below_limit"
            )
        if max(runtime_confidence, memory_confidence) < self.MINIMUM_RUNTIME_CONFIDENCE:
            missing_alignment_requirements.append(
                "runtime_dependency_confidence_below_limit"
            )
        if max(runtime_coverage, memory_coverage) < self.MINIMUM_CHAIN_COVERAGE:
            missing_alignment_requirements.append(
                "dependency_chain_coverage_below_limit"
            )
        if len(runtime_nodes) < 2:
            missing_alignment_requirements.append(
                "runtime_chain_too_short"
            )

        return {
            "system": "dependency_chain_alignment_engine",
            "phase": "6.97",
            "concept": concept,
            "alignment_ready": alignment_ready,
            "alignment_confidence": alignment_confidence,
            "runtime_dependency_nodes": runtime_nodes,
            "memory_dependency_nodes": memory_nodes,
            "runtime_confidence": runtime_confidence,
            "memory_confidence": memory_confidence,
            "runtime_chain_coverage": runtime_coverage,
            "memory_chain_coverage": memory_coverage,
            "overlap_score": overlap_score,
            "ordered_score": ordered_score,
            "bridge": bridge,
            "memory_ready_links": memory_ready_links,
            "memory_ready_link_count": len(memory_ready_links),
            "missing_alignment_requirements":
            missing_alignment_requirements,
            "automatic_truth_promotion_forbidden": True,
            "automatic_memory_persistence_forbidden": True,
            "persistent_write_requires_governance": True,
            "recommended_action": (
                "QUEUE_PROCESS_DEPENDENCY_MEMORY_ALIGNMENT"
                if alignment_ready
                else "COLLECT_RUNTIME_DEPENDENCY_ALIGNMENT_EVIDENCE"
            ),
        }


__all__ = [
    "DependencyChainAlignmentEngine",
]