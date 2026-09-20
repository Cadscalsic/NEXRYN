# ============================================
# NEXRYN MOTIVATION SYSTEM
# ============================================

from datetime import datetime

from runtime.motivation.cognitive_candy_manager import CognitiveCandyManager
from runtime.motivation.curiosity_balance_engine import CuriosityBalanceEngine
from runtime.motivation.candy_allocator import candy_allocator
from runtime.motivation.candy_budget_adapter import candy_budget_adapter
from runtime.motivation.candy_types import CONSTITUTIONAL_CONSTRAINTS
from runtime.motivation.motivation_state import MotivationState, clamp
from runtime.motivation.motivation_policy import motivation_policy
from runtime.motivation.penalty_engine import PenaltyEngine
from runtime.motivation.reward_hacking_detector import reward_hacking_detector
from runtime.motivation.reward_engine import RewardEngine


class MotivationSystem:

    def __init__(self):

        self.reward_engine = RewardEngine()
        self.penalty_engine = PenaltyEngine()
        self.candy_manager = CognitiveCandyManager()
        self.curiosity_balance_engine = CuriosityBalanceEngine()
        self.state = MotivationState()
        self.history = []

    def evaluate(self, runtime_context=None):

        context = runtime_context if isinstance(runtime_context, dict) else {}
        reward_report = self.reward_engine.evaluate(context)
        penalty_report = self.penalty_engine.evaluate(context)
        outcome_class = self.penalty_engine.classify_outcome(
            context,
            reward_report,
            penalty_report,
        )
        self.state.adapt(
            reward_score=reward_report["reward_score"],
            penalty_score=penalty_report["penalty_score"],
            outcome_class=outcome_class,
        )
        curiosity_report = self.curiosity_balance_engine.evaluate(
            self.state,
            reward_report,
            penalty_report,
        )
        hacking_report = reward_hacking_detector.detect(context)
        allocation_report = candy_allocator.allocate(
            context,
            reward_report.get("reward_assets", {}),
        )
        reward_assets = allocation_report.get(
            "reward_assets",
            reward_report.get("reward_assets", {}),
        )
        safety_multiplier = clamp(
            (1.0 - penalty_report.get("penalty_score", 0.0) * 0.6)
            * hacking_report.get("safety_multiplier", 1.0)
        )
        candy_report = self.candy_manager.allocate(
            reward_assets,
            penalty_report.get("penalty_score", 0.0),
            safety_multiplier=safety_multiplier,
            task_id=context.get("task_id"),
            reward_hacking_risk=hacking_report.get(
                "reward_hacking_risk",
                0.0,
            ),
            reuse_bonus=allocation_report.get("reuse_bonus", 0.0),
        )
        policy_report = motivation_policy.recommend(
            self.candy_manager.balances
        )
        budget_adapter_report = candy_budget_adapter.adapt(
            self._budget_context(context),
            policy_report,
        )
        candy_report = self.candy_manager.report(
            reward_hacking_risk=hacking_report.get(
                "reward_hacking_risk",
                0.0,
            ),
            reuse_bonus=allocation_report.get("reuse_bonus", 0.0),
            budget_adjustments=policy_report.get(
                "budget_adjustments",
                {},
            ),
        )
        history_patterns = self.candy_manager.history.hacking_patterns()
        self.state.synchronize_candy_state(
            balances=self.candy_manager.balances,
            trends=self.candy_manager.history.trends(),
            reward_hacking_risk=hacking_report.get("reward_hacking_risk", 0.0),
            reward_instability=history_patterns.get("reward_instability", 0.0),
        )
        truth_alignment = self._truth_alignment(context)
        governance_integrity = self._governance_integrity(context)
        final_decision_score = clamp(
            reward_report["reward_score"]
            * truth_alignment
            * governance_integrity
        )
        net_motivation = clamp(
            final_decision_score - penalty_report["penalty_score"],
            minimum=-1.0,
            maximum=1.0,
        )

        motivation_report = {
            "system": "MOTIVATION_REPORT",
            "outcome_class": outcome_class,
            "reward_score": reward_report["reward_score"],
            "penalty_score": penalty_report["penalty_score"],
            "net_motivation": round(net_motivation, 4),
            "final_decision_score": round(final_decision_score, 4),
            "truth_alignment": truth_alignment,
            "governance_integrity": governance_integrity,
            "curiosity_balance": curiosity_report["curiosity_balance"],
            "exploration_drive": self.state.report()["exploration_drive"],
            "failure_tolerance": self.state.report()["failure_tolerance"],
            "reward_distribution": reward_report["reward_distribution"],
            "penalty_distribution": penalty_report["penalty_distribution"],
            "reward_hacking_report": hacking_report,
            "motivation_policy": policy_report,
            "candy_budget_adapter": budget_adapter_report,
            "reward_allocation": allocation_report,
            "reward_safety": {
                "truth_governance_bypass_allowed": False,
                "identity_governance_bypass_allowed": False,
                "execution_integrity_bypass_allowed": False,
                "constitutional_identity_modification_allowed": False,
                "locked_truth_influence_allowed": False,
                "direct_execution_control_allowed": False,
                "final_decision_equation":
                "reward_score * truth_alignment * governance_integrity",
                "constitutional_constraints":
                CONSTITUTIONAL_CONSTRAINTS,
            },
            "curiosity_report": curiosity_report,
            "state": self.state.report(),
            "timestamp": str(datetime.utcnow()),
        }
        audit_report = self.build_audit_report()
        result = {
            "motivation_report": motivation_report,
            "MOTIVATION_REPORT": motivation_report,
            "cognitive_candy_report": candy_report,
            "COGNITIVE_CANDY_REPORT": candy_report,
            "motivation_policy": policy_report,
            "candy_budget_adapter": budget_adapter_report,
            "reward_hacking_report": hacking_report,
            "motivation_audit_report": audit_report,
            "MOTIVATION_AUDIT_REPORT": audit_report,
        }
        self.history.append({
            "outcome_class": outcome_class,
            "reward_score": reward_report["reward_score"],
            "penalty_score": penalty_report["penalty_score"],
            "timestamp": str(datetime.utcnow()),
        })
        self.history = self.history[-100:]
        return result

    def _budget_context(self, context):

        budget = context.get("current_reasoning_budget")
        if budget is not None:
            return {
                "max_reasoning_depth": getattr(
                    budget,
                    "max_reasoning_depth",
                    context.get("max_reasoning_depth"),
                ),
                "max_active_routes": getattr(
                    budget,
                    "max_active_routes",
                    context.get("max_active_routes"),
                ),
                "max_hypotheses": getattr(
                    budget,
                    "max_hypotheses",
                    context.get("max_hypotheses"),
                ),
            }
        return {
            "max_reasoning_depth": context.get("max_reasoning_depth"),
            "max_active_routes": context.get("max_active_routes"),
            "max_hypotheses": context.get("max_hypotheses"),
        }

    def build_audit_report(self):

        mechanisms = [
            {
                "file_location": "runtime/learning/operator_reward_engine.py",
                "trigger_conditions": [
                    "primitive execution completed",
                    "predicted_output compared to target_output",
                ],
                "reward_types": ["operator_accuracy_reward"],
                "penalty_types": ["operator_accuracy_penalty"],
                "severity_level": "binary_legacy",
                "affected_modules": ["runtime.learning", "runtime.transforms"],
                "exploration_impact": "can suppress operators after partial failure",
            },
            {
                "file_location": "runtime/memory/reinforcement_memory.py",
                "trigger_conditions": ["self_improvement_stage hypothesis update"],
                "reward_types": ["successful_experience_recall"],
                "penalty_types": ["failed_experience_retained"],
                "severity_level": "low_legacy",
                "affected_modules": ["runtime.learning", "runtime.stages.self_improvement"],
                "exploration_impact": "success-biased recall; partial progress was underrepresented",
            },
            {
                "file_location": "runtime/learning/strategy_scoring.py",
                "trigger_conditions": ["strategy outcome update"],
                "reward_types": ["success_count", "average_score", "stability_score"],
                "penalty_types": ["failure_count"],
                "severity_level": "moderate_legacy",
                "affected_modules": ["runtime.learning", "runtime.evolution"],
                "exploration_impact": "binary failure count can discourage recoverable exploration",
            },
            {
                "file_location": "runtime/memory/cognitive_failure_memory.py",
                "trigger_conditions": ["merge rejection", "semantic contradiction"],
                "reward_types": [],
                "penalty_types": ["ontology_damage", "failure_weight"],
                "severity_level": "major",
                "affected_modules": ["runtime.memory", "runtime.identity"],
                "exploration_impact": "protective; should remain cause-based",
            },
            {
                "file_location": "runtime/meta/meta_controller.py",
                "trigger_conditions": ["meta decision cycle"],
                "reward_types": ["efficiency_reward_signal", "curiosity_balance_signal"],
                "penalty_types": ["governance_escalation_signal"],
                "severity_level": "graduated",
                "affected_modules": ["runtime.meta", "runtime.pipeline"],
                "exploration_impact": "balances bounded exploration with governance locks",
            },
            {
                "file_location": "runtime/motivation/*",
                "trigger_conditions": ["runtime motivation cycle"],
                "reward_types": [
                    "truth",
                    "discovery",
                    "localization",
                    "generalization",
                    "efficiency",
                    "recovery",
                ],
                "penalty_types": [
                    "minor",
                    "moderate",
                    "major",
                    "critical",
                ],
                "severity_level": "graduated",
                "affected_modules": [
                    "runtime.meta",
                    "runtime.planning",
                    "runtime.learning",
                    "runtime.governance",
                ],
                "exploration_impact": "encourages trustworthy progress without bypassing governance",
            },
        ]
        return {
            "system": "MOTIVATION_AUDIT_REPORT",
            "mechanisms": mechanisms,
            "summary": {
                "legacy_binary_mechanisms": 3,
                "graduated_mechanisms": 2,
                "governance_preserved": True,
            },
            "timestamp": str(datetime.utcnow()),
        }

    def _truth_alignment(self, context):

        if context.get("truth_corruption_detected") is True:
            return 0.0
        if context.get("contradiction_detected") is True:
            return 0.35
        return round(clamp(
            context.get(
                "truth_alignment",
                context.get("causal_consistency", 1.0),
            )
        ), 4)

    def _governance_integrity(self, context):

        if context.get("unsafe_self_modification") is True:
            return 0.0
        if context.get("identity_governance_state") in {
            "TEMPORARY_RECOVERY_HOLD",
            "IDENTITY_GOVERNANCE_UNSTABLE",
        }:
            return 0.30
        return 1.0


motivation_system = MotivationSystem()
