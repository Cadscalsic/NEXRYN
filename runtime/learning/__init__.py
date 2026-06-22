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

from runtime.learning.confidence_updater import (
    ConfidenceUpdater
)

from runtime.learning.operator_reward_engine import (
    OperatorRewardEngine,
    operator_reward_engine
)

from runtime.learning.training_assistant import (
    TrainingAssistant
)

from runtime.learning.training_report import (
    build_training_report,
    print_training_report
)

from runtime.learning.saturation_detector import (
    LearningSaturationDetector,
    saturation_detector
)

from runtime.learning.saturation_controller import (
    LearningSaturationController,
    learning_saturation_controller
)

# ============================================
# PACKAGE VERSION
# ============================================

__version__ = "0.1.0"

# ============================================
# PACKAGE NAME
# ============================================

PACKAGE_NAME = (
    "NEXRYN-AMIS Learning Systems"
)


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
