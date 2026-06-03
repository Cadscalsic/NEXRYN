# ============================================
# NEXRYN EVALUATION ENGINE TEST
# ============================================

import sys
import os

# ============================================
# PROJECT ROOT PATH
# ============================================

PROJECT_ROOT = os.path.abspath(

    os.path.join(

        os.path.dirname(__file__),

        "..",

        ".."
    )
)

sys.path.append(
    PROJECT_ROOT
)

import numpy as np

from runtime.evaluation.evaluation_engine import (
    EvaluationEngine
)


# ============================================
# TEST EVALUATION ENGINE
# ============================================

def test_evaluation_engine():

    print("\n==================================================")
    print("TEST :: EVALUATION ENGINE")
    print("==================================================\n")

    # ========================================
    # INITIALIZE ENGINE
    # ========================================

    engine = EvaluationEngine()

    # ========================================
    # TEST ARRAYS
    # ========================================

    predicted = np.array([

        [1, 1, 1],

        [1, 2, 1],

        [1, 1, 1]
    ])

    target = np.array([

        [1, 1, 1],

        [1, 2, 1],

        [1, 1, 1]
    ])

    # ========================================
    # RUN EVALUATION
    # ========================================

    result = engine.evaluate(

        predicted,

        target
    )

    # ========================================
    # DISPLAY RESULT
    # ========================================

    print("EVALUATION RESULT:\n")

    print(result)

    # ========================================
    # ASSERTIONS
    # ========================================

    assert result["accuracy"] == 1.0

    assert result["difference_count"] == 0

    assert result["success"] is True

    # ========================================
    # SUCCESS MESSAGE
    # ========================================

    print("\nTEST PASSED\n")


def test_evaluation_engine_classifies_near_match_as_partial_success():
    engine = EvaluationEngine()
    predicted = np.zeros((5, 5), dtype=int)
    target = np.zeros((5, 5), dtype=int)
    target[0, 0] = 1

    result = engine.evaluate(predicted, target)

    assert result["accuracy"] == 0.96
    assert result["difference_count"] == 1
    assert result["success"] is False
    assert result["exact_success"] is False
    assert result["partial_success"] is True
    assert result["success_state"] == "PARTIAL_SUCCESS"


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":

    test_evaluation_engine()
