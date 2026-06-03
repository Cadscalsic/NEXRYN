import unittest

from runtime.meta_cognition.meta_cognitive_diversity_engine import (
    MetaCognitiveDiversityEngine,
)
from runtime.meta_cognition.meta_cognitive_supervisor import (
    MetaCognitiveSupervisor,
)


class MetaCognitiveDiversityTests(unittest.TestCase):

    def test_meta_cognitive_diversity_detects_adaptive_lock_in(self):

        context = {
            "abstraction_profiles": [
                "symbolic",
                "symbolic",
                "symbolic",
                "symbolic",
            ],
            "topology_profiles": [
                "grid",
                "grid",
                "grid",
            ],
            "perception_pattern_history": [
                "pattern_A",
                "pattern_A",
                "pattern_B",
            ],
            "strategy_usage_history": [
                "search",
                "search",
                "search",
                "search",
            ],
        }

        report = MetaCognitiveDiversityEngine().assess(
            context,
        )

        self.assertEqual(
            report["diversity_state"],
            "locked_in",
        )
        self.assertGreater(
            report["lock_in_risk"],
            0.5,
        )
        self.assertIn(
            "introduce_abstraction_variants",
            report["recommended_actions"],
        )

    def test_meta_cognitive_supervisor_includes_diversity_report(self):

        context = {
            "abstraction_profiles": [
                "symbolic",
                "symbolic",
                "symbolic",
            ],
            "topology_profiles": [
                "grid",
                "grid",
                "lattice",
            ],
            "perception_pattern_history": [
                "pattern_A",
                "pattern_A",
            ],
            "strategy_usage_history": [
                "search",
                "search",
            ],
        }

        report = MetaCognitiveSupervisor().run_meta_cycle(
            context,
        )

        self.assertIn(
            "diversity_report",
            report,
        )
        self.assertEqual(
            report["diversity_report"]["diversity_state"],
            "locked_in",
        )
        self.assertEqual(
            report["meta_summary"]["diversity_state"],
            "locked_in",
        )


if __name__ == "__main__":
    unittest.main()
