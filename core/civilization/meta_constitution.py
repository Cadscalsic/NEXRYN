# ============================================
# NEXRYN META-CONSTITUTION
# ============================================


AUTHORITY_HIERARCHY = [
    "meta_constitution",
    "constitutional_runtime",
    "semantic_court",
    "cognitive_immune_engine",
    "constitutional_rehearsal",
    "adaptive_permissioning",
]


class MetaConstitution:

    def authority_hierarchy(self):

        return {
            "authority_hierarchy":
            AUTHORITY_HIERARCHY,

            "supreme_authority":
            AUTHORITY_HIERARCHY[0],

            "resolution_rule":
            "constitutional_and_identity_safety_override_permission",
        }

    def constitutional_conflict_resolver(self, context):

        constitutional = context.get(
            "constitutional_runtime_report",
            {},
        )
        court = context.get(
            "semantic_court_report",
            {},
        )
        rehearsal = context.get(
            "constitutional_rehearsal_report",
            {},
        )
        immune = context.get(
            "cognitive_immune_engine_report",
            {},
        )
        permission = context.get(
            "adaptive_permissioning_report",
            {},
        )

        court_blocks_merge = (
            court.get(
                "merge_legality",
                {},
            ).get(
                "merge_allowed",
                False,
            )
            is False
        )

        runtime_blocks_merge = (
            constitutional.get(
                "semantic_judiciary",
                {},
            ).get(
                "verdicts",
                {},
            ).get(
                "merge_legality",
                "illegal_or_deferred",
            )
            != "legal"
        )

        rehearsal_allows_merge = (
            rehearsal.get(
                "constitutional_verification",
                {},
            ).get(
                "direct_core_merge_allowed",
                False,
            )
            or (
                rehearsal.get(
                    "constitutional_verification",
                    {},
                ).get(
                    "verified",
                    False,
                )
                and context.get(
                    "requested_action",
                    "governed_runtime_cycle",
                )
                != "direct_core_merge"
            )
        )

        immune_blocks = (
            immune.get(
                "semantic_quarantine",
                {},
            ).get(
                "quarantine_active",
                False,
            )
            or immune.get(
                "immune_state",
            )
            == "immune_emergency"
        )

        permission_allows = (
            permission.get(
                "commit_probability",
                0.0,
            )
            >= 0.5
        )

        conflicts = []

        if (
            court_blocks_merge
            or runtime_blocks_merge
        ) and rehearsal_allows_merge:

            conflicts.append(
                "judiciary_rehearsal_merge_conflict",
            )

        if immune_blocks and permission_allows:

            conflicts.append(
                "immune_permission_conflict",
            )

        if runtime_blocks_merge and permission_allows:

            conflicts.append(
                "runtime_permission_conflict",
            )

        return {
            "conflicts":
            conflicts,

            "court_blocks_merge":
            court_blocks_merge,

            "runtime_blocks_merge":
            runtime_blocks_merge,

            "rehearsal_allows_merge":
            rehearsal_allows_merge,

            "immune_blocks":
            immune_blocks,

            "permission_allows":
            permission_allows,

            "conflict_state":
            (
                "constitutional_conflict_detected"
                if conflicts
                else "no_constitutional_conflict"
            ),
        }

    def contradiction_reconciliation(self, conflict_report):

        conflicts = conflict_report.get(
            "conflicts",
            [],
        )

        if not conflicts:

            decision = "no_reconciliation_required"
            action = "preserve_existing_governance"

        elif "judiciary_rehearsal_merge_conflict" in conflicts:

            decision = "judiciary_precedence"
            action = "defer_merge_and_require_meta_review"

        elif "immune_permission_conflict" in conflicts:

            decision = "immune_precedence"
            action = "quarantine_overrides_permission"

        else:

            decision = "constitutional_runtime_precedence"
            action = "constitutional_hold_overrides_permission"

        return {
            "reconciliation_decision":
            decision,

            "reconciliation_action":
            action,

            "paradox_resolved":
            bool(
                conflicts,
            ),
        }

    def constitutional_consensus(self, context, conflict_report):

        votes = {
            "constitutional_runtime":
            "block"
            if conflict_report.get(
                "runtime_blocks_merge",
                False,
            )
            else "allow",

            "semantic_court":
            "block"
            if conflict_report.get(
                "court_blocks_merge",
                False,
            )
            else "allow",

            "cognitive_immune_engine":
            "block"
            if conflict_report.get(
                "immune_blocks",
                False,
            )
            else "allow",

            "constitutional_rehearsal":
            "allow"
            if conflict_report.get(
                "rehearsal_allows_merge",
                False,
            )
            else "defer",

            "adaptive_permissioning":
            "allow"
            if conflict_report.get(
                "permission_allows",
                False,
            )
            else "defer",
        }

        block_count = len([
            vote
            for vote in votes.values()
            if vote == "block"
        ])

        allow_count = len([
            vote
            for vote in votes.values()
            if vote == "allow"
        ])

        requested_action = context.get(
            "requested_action",
            "governed_runtime_cycle",
        )

        direct_core_merge = (
            requested_action == "direct_core_merge"
        )

        final_merge_authority = (
            "block_direct_core_merge"
            if direct_core_merge
            else "block_merge"
            if block_count
            else "allow_governed_merge"
            if allow_count >= 2
            else "defer_merge"
        )

        return {
            "governance_votes":
            votes,

            "block_count":
            block_count,

            "allow_count":
            allow_count,

            "final_merge_authority":
            final_merge_authority,

            "consensus_state":
            (
                "distributed_governance_block"
                if final_merge_authority.startswith(
                    "block",
                )
                else "distributed_governance_agreement"
                if final_merge_authority == "allow_governed_merge"
                else "distributed_governance_deferred"
            ),
        }

    def run_cycle(self, context):

        hierarchy = self.authority_hierarchy()
        conflict = self.constitutional_conflict_resolver(
            context,
        )
        reconciliation = self.contradiction_reconciliation(
            conflict,
        )
        consensus = self.constitutional_consensus(
            context,
            conflict,
        )

        return {
            "system":
            "meta_constitution",

            "authority":
            hierarchy,

            "constitutional_conflict_resolver":
            conflict,

            "contradiction_reconciliation":
            reconciliation,

            "constitutional_consensus":
            consensus,

            "meta_constitution_state":
            (
                "meta_constitution_intervention"
                if conflict.get(
                    "conflicts",
                    [],
                )
                else "meta_constitution_stable"
            ),
        }


meta_constitution = MetaConstitution()
