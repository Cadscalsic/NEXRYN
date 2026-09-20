"""Transformation language for converting concept tokens into grammar statements."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping


class TransformationLanguageEngine:
    """Assign transformation-token syntax and build transformation statements."""

    system_name = "transformation_language_engine"

    TOKEN_ROLES = {
        "gravity": ("action_schema", "MOVE"),
        "gravity_simulation": ("action_schema", "MOVE"),
        "falling": ("action", "MOVE_DOWNWARD"),
        "downward_motion": ("direction", "DOWNWARD"),
        "collision": ("termination", "UNTIL_COLLISION"),
        "support": ("postcondition", "ESTABLISH_SUPPORT"),
        "rest_state": ("postcondition", "STOP_MOVEMENT"),
        "component_merging": ("effect", "MERGE_COMPONENTS"),
        "connectivity_change": ("dependency", "UPDATE_CONNECTIVITY"),
        "topology_change": ("dependency", "UPDATE_TOPOLOGY"),
        "object_creation": ("action", "CREATE"),
        "density_increase": ("constraint", "INCREASE_DENSITY"),
        "symmetry_creation": ("relation", "SYMMETRIC_RELATION"),
        "symmetry_break": ("relation", "SYMMETRY_CHANGE"),
        "relative_position": ("spatial_relation", "RELATIVE_POSITION"),
        "spatial_relation": ("spatial_relation", "SPATIAL_RELATION"),
        "symbolic_remapping": ("action", "REMAP"),
        "color_mapping": ("object", "COLOR_CLASS"),
        "color_elimination": ("action", "ELIMINATE_COLOR"),
        "object_removal": ("action", "REMOVE"),
        "object_counting": ("action_schema", "COUNT"),
        "cardinality": ("object", "CARDINALITY"),
        "quantity_transformation": ("action", "APPLY_QUANTITY_RULE"),
        "quantity_preservation": ("constraint", "PRESERVE_QUANTITY"),
        "rotation": ("action", "ROTATE"),
        "reflection": ("action", "REFLECT"),
        "rotation_reflection": ("action_schema", "ORIENT"),
        "orientation_change": ("effect", "CHANGE_ORIENTATION"),
        "pattern_completion": ("action", "FILL"),
        "shape_preservation": ("constraint", "PRESERVE_SHAPE"),
        "object_identity_preservation": ("constraint", "PRESERVE_OBJECT_IDENTITY"),
        "transformation_sequence": ("composition", "COMPOSE"),
    }

    def parse(
        self,
        concepts: list[str] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        concepts = list(dict.fromkeys(str(item) for item in concepts or []))
        tokens = [self._token(concept) for concept in concepts]
        known = [token for token in tokens if token["known"]]
        statements = self._statements(known)
        roles = {}
        for token in known:
            roles.setdefault(token["role"], []).append(token["concept"])
        return {
            "system": self.system_name,
            "TRANSFORMATION_LANGUAGE_REPORT": True,
            "input_concepts": concepts,
            "tokens": tokens,
            "known_token_count": len(known),
            "grammar_roles": roles,
            "transformation_statements": statements,
            "statement_count": len(statements),
            "primary_statement": statements[0] if statements else None,
            "syntax_ready": bool(statements),
            "grammar_coverage": round(len(known) / max(len(concepts), 1), 4),
            "timestamp": str(datetime.utcnow()),
        }

    def _token(self, concept):
        role, lexeme = self.TOKEN_ROLES.get(concept, ("unknown", concept.upper()))
        return {
            "concept": concept,
            "role": role,
            "lexeme": lexeme,
            "known": role != "unknown",
        }

    def _statements(self, tokens):
        concepts = {token["concept"] for token in tokens}
        if {"gravity", "falling"} & concepts or {"gravity_simulation"} & concepts:
            return [self._statement(
                "gravity_motion_statement",
                subject="object",
                action="MOVE",
                direction="DOWNWARD",
                condition="IF_UNSUPPORTED",
                termination="UNTIL_COLLISION_OR_SUPPORT",
                postconditions=["ESTABLISH_SUPPORT", "STOP_MOVEMENT"],
                constraints=["UPDATE_TOPOLOGY"] if "topology_change" in concepts else [],
                dependencies=["support", "collision", "spatial_relation"],
            )]
        if {"object_creation", "density_increase", "symmetry_creation"} & concepts:
            return [self._statement(
                "symmetric_creation_statement",
                subject="new_object",
                action="CREATE",
                relation="SYMMETRIC_RELATION" if "symmetry_creation" in concepts else "RELATIVE_POSITION",
                condition=None,
                constraints=[
                    item for item in ["INCREASE_DENSITY", "PRESERVE_COLOR", "UPDATE_TOPOLOGY"]
                    if item != "INCREASE_DENSITY" or "density_increase" in concepts
                ],
                dependencies=["relative_position", "spatial_relation"],
            )]
        if {"symbolic_remapping", "color_mapping", "color_elimination", "object_removal"} & concepts:
            actions = []
            if "symbolic_remapping" in concepts or "color_mapping" in concepts:
                actions.append("REMAP")
            if "color_elimination" in concepts:
                actions.append("ELIMINATE_COLOR")
            if "object_removal" in concepts:
                actions.append("REMOVE_OBJECT")
            return [self._statement(
                "symbolic_color_statement",
                subject="object_or_color_class",
                action="+".join(actions) if actions else "REMAP",
                condition="IF_MATCHES_SYMBOLIC_CLASS",
                constraints=["PRESERVE_RELATIVE_POSITION"] if "relative_position" in concepts else [],
                dependencies=["color_mapping", "object_identity"],
            )]
        if {"pattern_completion"} & concepts:
            return [self._statement(
                "pattern_completion_statement",
                subject="missing_pattern",
                action="FILL",
                condition="IF_PATTERN_GAP_DETECTED",
                constraints=["PRESERVE_COLOR", "PRESERVE_SHAPE"],
                dependencies=["symmetry", "adjacency"],
            )]
        if {"rotation", "reflection", "rotation_reflection", "orientation_change"} & concepts:
            return [self._statement(
                "orientation_statement",
                subject="object_or_grid",
                action="ROTATE_OR_REFLECT",
                condition="IF_ORIENTATION_CHANGE",
                constraints=["PRESERVE_COLORS", "PRESERVE_TOPOLOGY"],
                dependencies=["rotation_center", "reference_frame"],
            )]
        if {"object_counting", "cardinality", "quantity_transformation"} & concepts:
            return [self._statement(
                "quantity_statement",
                subject="object_group",
                action="APPLY_QUANTITY_RULE",
                condition="IF_CARDINALITY_EXTRACTED",
                constraints=["COUNT_DOMAIN_REQUIRED"],
                dependencies=["object_grouping", "set_membership"],
            )]
        return []

    def _statement(
        self,
        statement_id,
        *,
        subject,
        action,
        condition=None,
        direction=None,
        relation=None,
        termination=None,
        postconditions=None,
        constraints=None,
        dependencies=None,
    ):
        return {
            "statement_id": statement_id,
            "subject": subject,
            "action": action,
            "condition": condition,
            "direction": direction,
            "relation": relation,
            "termination": termination,
            "postconditions": list(postconditions or []),
            "constraints": list(constraints or []),
            "dependencies": list(dependencies or []),
            "grammar": {
                "has_subject": bool(subject),
                "has_action": bool(action),
                "has_condition": bool(condition),
                "has_termination": bool(termination),
                "has_constraints": bool(constraints),
                "has_dependencies": bool(dependencies),
            },
            "executable": bool(subject and action),
        }


transformation_language_engine = TransformationLanguageEngine()


__all__ = [
    "TransformationLanguageEngine",
    "transformation_language_engine",
]
