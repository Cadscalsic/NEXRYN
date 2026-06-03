import importlib.util
from pathlib import Path


def load_curriculum_generator():
    path = Path(__file__).resolve().parents[1] / "tools" / "generate_training_curriculum.py"
    spec = importlib.util.spec_from_file_location(
        "generate_training_curriculum",
        path,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generate_training_curriculum_includes_transform_heavy_base_cases():
    module = load_curriculum_generator()
    transform_concepts = {
        "shape_transform",
        "color_transform",
        "shape_change",
        "color_change",
        "topological_growth",
        "grow_topology",
    }
    base_targets = [concept for _, concepts, *_ in module.CASES for concept in concepts]

    assert any(concept in transform_concepts for concept in base_targets), (
        "Base curriculum should include transform-heavy concepts"
    )


def test_generate_training_curriculum_includes_new_targeted_transform_cases():
    module = load_curriculum_generator()
    targeted_targets = [concept for _, concepts, *_ in module.TARGETED_CASES for concept in concepts]

    assert "shape_transform" in targeted_targets
    assert "color_transform" in targeted_targets
    assert "topological_growth" in targeted_targets


def test_generate_training_curriculum_includes_transform_scarcity_cases():
    module = load_curriculum_generator()
    scarcity_targets = [concept for _, concepts, *_ in module.SCARCITY_CASES for concept in concepts]

    assert "shape_transform" in scarcity_targets
    assert "color_transform" in scarcity_targets
