from core.causal import CausalGraph, CausalInheritance


def test_causal_inheritance_learns_and_applies_reusable_templates():
    inheritance = CausalInheritance(inheritance_threshold=0.7)
    inheritance.learn_template(
        "duplication",
        "object_count_increase",
        "causes",
        confidence=0.75,
    )

    graph = CausalGraph()
    applied = inheritance.apply_expectations(
        graph,
        "duplication",
        context={"transformation_family": "duplication"},
    )

    assert applied
    assert applied[0]["target"] == "object_count_increase"
    assert graph.find_path("duplication", "object_count_increase")
