# ============================================
# NEXRYN PATTERN & RULE STAGE
# ============================================

from datetime import datetime

from runtime.utils import (
    normalize_value
)

from core.patterns import (
    ARCPatternEngine
)

from core.rules import (
    ARCRuleEngine
)


# ============================================
# SAFE REPORT EXECUTION
# ============================================

def safe_print_report(

    engine
):

    try:

        engine.print_report()

    except Exception as error:

        print(
            f"REPORT ERROR :: {error}"
        )


# ============================================
# BUILD PATTERN METRICS
# ============================================

def build_pattern_metrics(

    patterns
):

    return {

        "pattern_count":
        len(patterns),

        "symmetry_patterns":

        len([

            pattern

            for pattern in patterns

            if "symmetry"

            in

            str(pattern).lower()
        ]),

        "density_patterns":

        len([

            pattern

            for pattern in patterns

            if "density"

            in

            str(pattern).lower()
        ])
    }


# ============================================
# BUILD RULE METRICS
# ============================================

def build_rule_metrics(

    rules
):

    return {

        "rule_count":
        len(rules),

        "transformation_rules":

        len([

            rule

            for rule in rules

            if "transform"

            in

            str(rule).lower()
        ]),

        "mapping_rules":

        len([

            rule

            for rule in rules

            if "mapping"

            in

            str(rule).lower()
        ])
    }


# ============================================
# PATTERN & RULE STAGE
# ============================================

def pattern_rule_stage(context):

    print(
        "\n=================================================="
    )

    print(
        "NEXRYN :: PATTERN & RULE STAGE"
    )

    print(
        "==================================================\n"
    )

    # ========================================
    # STAGE REPORT
    # ========================================

    stage_report = {

        "stage":
        "pattern_rule",

        "status":
        "running",

        "runtime_health":
        "stable",

        "timestamp":
        str(
            datetime.utcnow()
        )
    }

    # ========================================
    # VALIDATE CONTEXT
    # ========================================

    if "input_grid" not in context:

        raise ValueError(
            "Missing input_grid"
        )

    if "output_grid" not in context:

        raise ValueError(
            "Missing output_grid"
        )

    # ========================================
    # LOAD CONTEXT
    # ========================================

    input_grid = context[
        "input_grid"
    ]

    output_grid = context[
        "output_grid"
    ]

    # ========================================
    # PATTERN ENGINE
    # ========================================

    pattern_engine = ARCPatternEngine(

        input_grid=input_grid,

        output_grid=output_grid
    )

    # ========================================
    # ANALYZE PATTERNS
    # ========================================

    pattern_engine.analyze_patterns()

    normalized_patterns = normalize_value(

        pattern_engine.patterns
    )

    pattern_engine.patterns = (
        normalized_patterns
    )

    # ========================================
    # PATTERN REPORT
    # ========================================

    print(
        "\nPATTERN ANALYSIS:\n"
    )

    safe_print_report(
        pattern_engine
    )

    # ========================================
    # RULE ENGINE
    # ========================================

    rule_engine = ARCRuleEngine(

        input_grid=input_grid,

        output_grid=output_grid
    )

    # ========================================
    # ANALYZE RULES
    # ========================================

    rule_engine.analyze()

    normalized_rules = normalize_value(

        rule_engine.rules
    )

    rule_engine.rules = (
        normalized_rules
    )

    # ========================================
    # RULE REPORT
    # ========================================

    print(
        "\nRULE ANALYSIS:\n"
    )

    safe_print_report(
        rule_engine
    )

    # ========================================
    # PATTERN METRICS
    # ========================================

    pattern_metrics = (

        build_pattern_metrics(
            normalized_patterns
        )
    )

    # ========================================
    # RULE METRICS
    # ========================================

    rule_metrics = (

        build_rule_metrics(
            normalized_rules
        )
    )

    # ========================================
    # PATTERN COMPLEXITY
    # ========================================

    pattern_complexity = "low"

    total_patterns = len(
        normalized_patterns
    )

    if total_patterns > 10:

        pattern_complexity = "high"

    elif total_patterns > 5:

        pattern_complexity = "medium"

    # ========================================
    # RULE COMPLEXITY
    # ========================================

    rule_complexity = "low"

    total_rules = len(
        normalized_rules
    )

    if total_rules > 10:

        rule_complexity = "high"

    elif total_rules > 5:

        rule_complexity = "medium"

    # ========================================
    # COGNITIVE SIGNALS
    # ========================================

    cognitive_signals = {

        "pattern_density":
        total_patterns,

        "rule_density":
        total_rules,

        "requires_symbolic_reasoning":

        total_rules > 3,

        "requires_recursive_reasoning":

        total_patterns > 5
    }

    # ========================================
    # STAGE METADATA
    # ========================================

    stage_metadata = {

        "patterns_detected":
        total_patterns,

        "rules_detected":
        total_rules,

        "pattern_complexity":
        pattern_complexity,

        "rule_complexity":
        rule_complexity,

        "analysis_success":
        True
    }

    # ========================================
    # ANALYSIS SUMMARY
    # ========================================

    analysis_summary = {

        "pattern_metrics":
        pattern_metrics,

        "rule_metrics":
        rule_metrics,

        "cognitive_signals":
        cognitive_signals
    }

    # ========================================
    # UPDATE STAGE REPORT
    # ========================================

    stage_report.update({

        "status":
        "completed",

        "pattern_count":
        total_patterns,

        "rule_count":
        total_rules,

        "pattern_complexity":
        pattern_complexity,

        "rule_complexity":
        rule_complexity
    })

    # ========================================
    # SAVE TO CONTEXT
    # ========================================

    context[
        "pattern_engine"
    ] = pattern_engine

    context[
        "rule_engine"
    ] = rule_engine

    context[
        "patterns"
    ] = normalized_patterns

    context[
        "rules"
    ] = normalized_rules

    context[
        "pattern_metrics"
    ] = pattern_metrics

    context[
        "rule_metrics"
    ] = rule_metrics

    context[
        "pattern_rule_metadata"
    ] = stage_metadata

    context[
        "pattern_rule_summary"
    ] = analysis_summary

    context[
        "cognitive_signals"
    ] = cognitive_signals

    context[
        "pattern_rule_stage_report"
    ] = stage_report

    context[
        "pattern_rule_complete"
    ] = True

    # ========================================
    # RETURN CONTEXT
    # ========================================

    return context