# ============================================
# NEXRYN LEARNING PACKAGE
# ============================================

"""
Adaptive learning systems for:

- confidence updating
- reinforcement learning
- experience adaptation
- reasoning optimization
- cognitive self-improvement
"""

# ============================================
# PACKAGE VERSION
# ============================================

__version__ = "0.1.0"

# ============================================
# PACKAGE NAME
# ============================================

PACKAGE_NAME = (
    "NEXRYN Learning Systems"
)

_EXPORTS = {
    "ConfidenceUpdater": (
        "runtime.learning.confidence_updater",
        "ConfidenceUpdater",
    ),
    "OperatorRewardEngine": (
        "runtime.learning.operator_reward_engine",
        "OperatorRewardEngine",
    ),
    "operator_reward_engine": (
        "runtime.learning.operator_reward_engine",
        "operator_reward_engine",
    ),
    "TrainingAssistant": (
        "runtime.learning.training_assistant",
        "TrainingAssistant",
    ),
    "build_training_report": (
        "runtime.learning.training_report",
        "build_training_report",
    ),
    "print_training_report": (
        "runtime.learning.training_report",
        "print_training_report",
    ),
    "LearningSaturationDetector": (
        "runtime.learning.saturation_detector",
        "LearningSaturationDetector",
    ),
    "saturation_detector": (
        "runtime.learning.saturation_detector",
        "saturation_detector",
    ),
    "LearningSaturationController": (
        "runtime.learning.saturation_controller",
        "LearningSaturationController",
    ),
    "learning_saturation_controller": (
        "runtime.learning.saturation_controller",
        "learning_saturation_controller",
    ),
}


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attr_name = _EXPORTS[name]
    from importlib import import_module

    value = getattr(import_module(module_name), attr_name)
    globals()[name] = value
    return value


__all__ = [
    "ConfidenceUpdater",
    "OperatorRewardEngine",
    "operator_reward_engine",
    "TrainingAssistant",
    "build_training_report",
    "print_training_report",
    "LearningSaturationDetector",
    "saturation_detector",
    "LearningSaturationController",
    "learning_saturation_controller",
]
