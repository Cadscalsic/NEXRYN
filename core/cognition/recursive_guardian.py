# ============================================
# NEXRYN RECURSIVE GUARDIAN
# ============================================

from datetime import datetime


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


class RecursiveGuardian:

    def __init__(self, max_depth=16, recursion_budget=256):

        self.max_depth = max_depth
        self.recursion_budget = recursion_budget
        self.ancestry_cache = {}
        self.guardian_history = []

    def _graph(self, records):

        graph = {}

        for record in records:

            concept_id = record.get(
                "concept_id",
            )

            if concept_id is None:

                continue

            graph[
                concept_id
            ] = list(
                record.get(
                    "parents",
                    [],
                )
            )

        return graph

    def detect_cycle(self, records):

        graph = self._graph(
            records,
        )

        cycles = []
        visiting = set()
        visited = set()

        def visit(node, path):

            if node in visiting:

                if node in path:

                    index = path.index(
                        node,
                    )
                    cycles.append(
                        path[index:]
                        +
                        [
                            node,
                        ]
                    )

                return

            if node in visited:

                return

            visiting.add(
                node,
            )

            for parent in graph.get(
                node,
                [],
            ):

                visit(
                    parent,
                    path
                    +
                    [
                        node,
                    ],
                )

            visiting.remove(
                node,
            )
            visited.add(
                node,
            )

        for node in graph:

            visit(
                node,
                [],
            )

        return {
            "cycles":
            cycles,

            "cycle_count":
            len(
                cycles,
            ),

            "cycle_state":
            (
                "cyclic_cognitive_ancestry"
                if cycles
                else "acyclic_lineage"
            ),
        }

    def prevent_self_reference_loop(self, concept_id, parents):

        filtered = [
            parent
            for parent in parents
            if parent
            and parent != concept_id
        ]

        return {
            "concept_id":
            concept_id,

            "parents":
            filtered,

            "self_reference_removed":
            len(
                filtered,
            )
            !=
            len(
                parents,
            ),
        }

    def lineage_depth_control(self, graph, concept_id, depth=0, visited=None):

        if visited is None:

            visited = set()

        if concept_id in visited:

            return {
                "depth":
                depth,

                "depth_state":
                "cycle_depth_cutoff",
            }

        if depth >= self.max_depth:

            return {
                "depth":
                depth,

                "depth_state":
                "max_depth_reached",
            }

        visited.add(
            concept_id,
        )

        parent_depths = [
            self.lineage_depth_control(
                graph,
                parent,
                depth + 1,
                set(
                    visited,
                ),
            ).get(
                "depth",
                depth,
            )
            for parent in graph.get(
                concept_id,
                [],
            )
        ]

        return {
            "depth":
            max(
                parent_depths
                or [
                    depth,
                ]
            ),

            "depth_state":
            "depth_controlled",
        }

    def recursion_budget_manager(self, visited_count):

        remaining = max(
            self.recursion_budget
            -
            visited_count,
            0,
        )

        return {
            "recursion_budget":
            self.recursion_budget,

            "visited_count":
            visited_count,

            "remaining_budget":
            remaining,

            "budget_state":
            (
                "recursion_budget_exhausted"
                if remaining <= 0
                else "recursion_budget_low"
                if remaining < self.recursion_budget * 0.20
                else "recursion_budget_available"
            ),
        }

    def ancestry_cache_guard(self, concept_id, ancestry=None):

        if ancestry is None:

            return self.ancestry_cache.get(
                concept_id,
            )

        self.ancestry_cache[
            concept_id
        ] = ancestry

        if len(
            self.ancestry_cache,
        ) > 512:

            keys = list(
                self.ancestry_cache.keys()
            )
            for key in keys[
                :128
            ]:

                self.ancestry_cache.pop(
                    key,
                    None,
                )

        return ancestry

    def topology_loop_detector(self, records):

        cycle_report = self.detect_cycle(
            records,
        )

        graph = self._graph(
            records,
        )

        max_depth = 0

        for node in graph:

            max_depth = max(
                max_depth,
                self.lineage_depth_control(
                    graph,
                    node,
                ).get(
                    "depth",
                    0,
                ),
            )

        return {
            "cycle_report":
            cycle_report,

            "max_lineage_depth":
            max_depth,

            "topology_state":
            (
                "topology_loop_detected"
                if cycle_report.get(
                    "cycle_count",
                    0,
                )
                else "lineage_depth_excessive"
                if max_depth >= self.max_depth
                else "topology_safe"
            ),
        }

    def semantic_recursion_firewall(self, topology_report):

        block = topology_report.get(
            "topology_state",
        ) in [
            "topology_loop_detected",
            "lineage_depth_excessive",
        ]

        return {
            "block_recursive_expansion":
            block,

            "firewall_policy":
            (
                "block_recursive_lineage_expansion"
                if block
                else "allow_guarded_lineage_expansion"
            ),
        }

    def _path_exists(self, graph, start, target, visited=None):

        if visited is None:

            visited = set()

        if start == target:

            return True

        if start in visited:

            return False

        visited.add(
            start,
        )

        for parent in graph.get(
            start,
            [],
        ):

            if self._path_exists(
                graph,
                parent,
                target,
                visited,
            ):

                return True

        return False

    def graph_cycle_breaker(self, record, existing_records):

        concept_id = record.get(
            "concept_id",
        )

        parents = record.get(
            "parents",
            [],
        )

        self_ref = self.prevent_self_reference_loop(
            concept_id,
            parents,
        )

        graph = self._graph(
            existing_records,
        )

        safe_parents = []
        removed_edges = []

        for parent in self_ref.get(
            "parents",
            [],
        ):

            if self._path_exists(
                graph,
                parent,
                concept_id,
            ):

                removed_edges.append({
                    "source":
                    concept_id,

                    "target":
                    parent,

                    "reason":
                    "cycle_would_form",
                })

            else:

                safe_parents.append(
                    parent,
                )

        cleaned = dict(
            record,
        )
        cleaned[
            "parents"
        ] = safe_parents

        return {
            "record":
            cleaned,

            "removed_edges":
            removed_edges,

            "cycle_break_state":
            (
                "cycle_edges_removed"
                if removed_edges
                or self_ref.get(
                    "self_reference_removed",
                    False,
                )
                else "record_acyclic"
            ),
        }

    def identity_recursion_limiter(self, ancestry_report):

        depth = ancestry_report.get(
            "depth",
            0,
        )

        return {
            "identity_recursion_limited":
            depth >= self.max_depth,

            "max_depth":
            self.max_depth,

            "observed_depth":
            depth,
        }

    def self_reference_safety(self, records):

        topology = self.topology_loop_detector(
            records,
        )
        firewall = self.semantic_recursion_firewall(
            topology,
        )
        budget = self.recursion_budget_manager(
            len(
                records,
            )
        )

        return {
            "topology_loop_detector":
            topology,

            "semantic_recursion_firewall":
            firewall,

            "recursion_budget":
            budget,

            "self_reference_state":
            (
                "recursive_safety_intervention"
                if firewall.get(
                    "block_recursive_expansion",
                    False,
                )
                else "self_reference_safe"
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        records = context.get(
            "concept_lineage_report",
            {},
        ).get(
            "lineage_records",
            context.get(
                "lineage_records",
                [],
            ),
        )

        safety = self.self_reference_safety(
            records,
        )

        report = {
            "system":
            "recursive_guardian",

            "guardian_mode":
            "directed_acyclic_cognitive_graph_guard",

            "self_reference_safety":
            safety,

            "cycle_report":
            safety.get(
                "topology_loop_detector",
                {},
            ).get(
                "cycle_report",
                {},
            ),

            "recursive_guardian_state":
            safety.get(
                "self_reference_state",
                "self_reference_safe",
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.guardian_history.append(
            report,
        )

        self.guardian_history = (
            self.guardian_history[-128:]
        )

        return report


recursive_guardian = RecursiveGuardian()
