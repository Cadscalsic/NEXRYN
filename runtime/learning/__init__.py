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
