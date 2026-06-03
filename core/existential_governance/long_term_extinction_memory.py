class LongTermExtinctionMemory:

    def remember(self, context):

        graveyard = context.get("evolutionary_graveyard_report", {})
        extinction = context.get("extinction_engine_report", {})

        extinct_count = extinction.get("extinct_count", 0)
        toxic_lineages = graveyard.get("toxic_lineages", {})
        causes = graveyard.get("top_causes", {})

        memory_items = []

        if extinct_count:

            memory_items.append("record_extinction_wave")

        if toxic_lineages:

            memory_items.append("preserve_toxic_lineage_warning")

        if causes:

            memory_items.append("index_failure_causes_for_future_governance")

        return {
            "system": "long_term_extinction_memory",
            "extinct_count": extinct_count,
            "toxic_lineage_count": len(toxic_lineages),
            "recorded_failure_causes": len(causes),
            "memory_actions": memory_items,
            "memory_state": (
                "long_term_extinction_memory_active"
                if memory_items
                else "long_term_extinction_memory_standby"
            ),
        }
