import json
from pathlib import Path


TRAINING_DIRECTORY = Path("data/training")
FIRST_TASK_NUMBER = 7
TARGETED_BATCH_FIRST_TASK_NUMBER = 37
SCARCITY_BATCH_FIRST_TASK_NUMBER = 87


def grid(*rows):
    return [list(row) for row in rows]


def recolor(source, mapping):
    return [
        [mapping.get(value, value) for value in row]
        for row in source
    ]


def recolor_nonzero(source, target_color):
    return [
        [target_color if value else 0 for value in row]
        for row in source
    ]


def increment_colors(source, amount):
    return [
        [value + amount if value else 0 for value in row]
        for row in source
    ]


def shift(source, row_delta, column_delta):
    height = len(source)
    width = len(source[0])
    target = [[0 for _ in range(width)] for _ in range(height)]
    for row_index, row in enumerate(source):
        for column_index, value in enumerate(row):
            if not value:
                continue
            target_row = row_index + row_delta
            target_column = column_index + column_delta
            if 0 <= target_row < height and 0 <= target_column < width:
                target[target_row][target_column] = value
    return target


def rotate_clockwise(source):
    return [
        list(row)
        for row in zip(*source[::-1])
    ]


def mirror_horizontal(source):
    return [
        list(reversed(row))
        for row in source
    ]


def replicate(source, row_delta, column_delta):
    target = [list(row) for row in source]
    height = len(source)
    width = len(source[0])
    for row_index, row in enumerate(source):
        for column_index, value in enumerate(row):
            if not value:
                continue
            target_row = row_index + row_delta
            target_column = column_index + column_delta
            if 0 <= target_row < height and 0 <= target_column < width:
                target[target_row][target_column] = value
    return target


def grow(source, row_delta, column_delta):
    return replicate(source, row_delta, column_delta)


def spread(source, offsets):
    target = [list(row) for row in source]
    for row_delta, column_delta in offsets:
        target = replicate(target, row_delta, column_delta)
    return target


def compose(*transforms):
    def apply(source):
        result = source
        for transform in transforms:
            result = transform(result)
        return result

    return apply


SHAPES = {
    "dot": grid(
        (0, 0, 0, 0, 0),
        (0, 0, 1, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
    ),
    "pair": grid(
        (0, 0, 0, 0, 0),
        (0, 1, 1, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
    ),
    "vertical_pair": grid(
        (0, 0, 0, 0, 0),
        (0, 1, 0, 0, 0),
        (0, 1, 0, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
    ),
    "elbow": grid(
        (0, 0, 0, 0, 0),
        (0, 1, 1, 0, 0),
        (0, 1, 0, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
    ),
    "tee": grid(
        (0, 0, 0, 0, 0),
        (0, 1, 1, 1, 0),
        (0, 0, 1, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
    ),
    "edge_pair": grid(
        (0, 0, 0, 0, 0),
        (0, 0, 0, 1, 1),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
    ),
    "two_colors": grid(
        (0, 0, 0, 0, 0),
        (0, 1, 2, 0, 0),
        (0, 2, 1, 0, 0),
        (0, 0, 0, 0, 0),
        (0, 0, 0, 0, 0),
    ),
}


def transform(function, *args):
    return lambda source: function(source, *args)


CASES = [
    ("density", ["density_preservation"], "direct", "elbow",
     transform(shift, 1, 1)),
    ("density", ["density_preservation"], "direct", "tee",
     transform(shift, 1, 0)),
    ("density", ["density_preservation"], "direct", "tee",
     rotate_clockwise),
    ("density", ["density_preservation"], "direct", "elbow",
     mirror_horizontal),
    ("density", ["density_preservation"], "matched_boundary", "edge_pair",
     transform(shift, 0, 1)),
    ("density", ["density_preservation"], "matched_boundary", "vertical_pair",
     transform(shift, -1, 0)),
    ("symbolic_remapping", ["symbolic_remapping"], "direct", "elbow",
     transform(recolor_nonzero, 3)),
    ("symbolic_remapping", ["symbolic_remapping"], "direct", "tee",
     transform(recolor_nonzero, 4)),
    ("symbolic_remapping", ["symbolic_remapping"], "direct", "pair",
     transform(recolor_nonzero, 5)),
    ("symbolic_remapping", ["symbolic_remapping"], "direct", "vertical_pair",
     transform(recolor_nonzero, 6)),
    ("symbolic_remapping", ["symbolic_remapping"], "matched_boundary",
     "two_colors", transform(increment_colors, 1)),
    ("symbolic_remapping", ["symbolic_remapping"], "matched_boundary",
     "two_colors", transform(recolor_nonzero, 7)),
    ("replication", ["replication"], "direct", "dot",
     transform(replicate, 0, 2)),
    ("replication", ["replication"], "direct", "pair",
     transform(replicate, 2, 0)),
    ("replication", ["replication"], "matched_boundary", "vertical_pair",
     transform(replicate, 0, 2)),
    ("replication", ["replication"], "matched_boundary", "edge_pair",
     transform(replicate, 1, 0)),
    ("growth", ["growth", "topological_growth"], "direct", "pair",
     transform(grow, 1, 0)),
    ("growth", ["growth", "topological_growth"], "direct", "vertical_pair",
     transform(grow, 0, 1)),
    ("growth", ["growth", "topological_growth"], "matched_boundary", "elbow",
     transform(grow, 1, 0)),
    ("growth", ["growth", "topological_growth"], "matched_boundary", "tee",
     transform(grow, 0, 1)),
    ("topology", ["topology_preservation"], "direct", "vertical_pair",
     rotate_clockwise),
    ("topology", ["topology_preservation"], "direct", "pair",
     mirror_horizontal),
    ("shape_transform", ["shape_transform"], "direct", "elbow",
     rotate_clockwise),
    ("shape_transform", ["shape_transform"], "matched_boundary", "pair",
     mirror_horizontal),
    ("shape_change", ["shape_change"], "matched_boundary", "vertical_pair",
     transform(replicate, 0, 1)),
    ("shape_change", ["shape_change"], "direct", "pair",
     transform(shift, 1, 1)),
    ("color_transform", ["color_transform"], "direct", "two_colors",
     lambda source: recolor(source, {1: 5, 2: 6})),
    ("color_change", ["color_change"], "matched_boundary", "two_colors",
     lambda source: recolor(source, {1: 7, 2: 8})),
    ("topology", ["topology_preservation"], "matched_boundary", "tee",
     transform(shift, 1, 1)),
    ("topology", ["topology_preservation"], "matched_boundary", "tee",
     compose(rotate_clockwise, transform(recolor_nonzero, 3))),
    ("mixed", ["symbolic_remapping", "topology_preservation"], "composite",
     "elbow",
     compose(transform(shift, 1, 1), transform(recolor_nonzero, 3))),
    ("mixed", ["symbolic_remapping", "density_preservation"], "composite",
     "elbow", compose(mirror_horizontal, transform(recolor_nonzero, 4))),
    ("mixed", ["replication", "symbolic_remapping"], "composite", "dot",
     compose(transform(replicate, 0, 2), transform(recolor_nonzero, 5))),
    ("mixed", ["growth", "symbolic_remapping"], "composite", "pair",
     compose(transform(grow, 1, 0), transform(recolor_nonzero, 6))),
    ("mixed", ["topology_preservation", "density_preservation"], "composite",
     "elbow", compose(rotate_clockwise, transform(shift, 1, 1))),
    ("mixed", ["density_preservation", "symbolic_remapping"], "composite",
     "edge_pair",
     compose(transform(shift, 0, 1), transform(recolor_nonzero, 7))),
]


TARGETED_CASES = [
    *[
        (
            "replication",
            ["replication"],
            "targeted_direct",
            shape_name,
            transform(replicate, row_delta, column_delta),
        )
        for shape_name, row_delta, column_delta in [
            ("dot", 0, 1),
            ("dot", 1, 0),
            ("dot", 1, 1),
            ("pair", 0, 2),
            ("pair", 1, 0),
            ("vertical_pair", 0, 1),
            ("vertical_pair", 2, 2),
            ("elbow", 0, 2),
            ("elbow", 2, 0),
            ("tee", 2, 0),
        ]
    ],
    *[
        (
            "topology_exploration",
            ["topological_reasoning", "topological_change"],
            "targeted_topology",
            shape_name,
            transform(replicate, row_delta, column_delta),
        )
        for shape_name, row_delta, column_delta in [
            ("dot", 0, 2),
            ("dot", 2, 0),
            ("dot", 2, 2),
            ("pair", 2, 0),
            ("pair", 2, 1),
            ("vertical_pair", 0, 2),
            ("vertical_pair", 1, 2),
            ("elbow", 0, 3),
            ("elbow", 3, 0),
            ("edge_pair", 2, -1),
        ]
    ],
    *[
        (
            "density_modulation",
            ["density_modulation", "propagation"],
            "targeted_density",
            shape_name,
            transform(spread, offsets),
        )
        for shape_name, offsets in [
            ("dot", [(0, 1), (1, 0)]),
            ("dot", [(1, 0), (1, 1)]),
            ("dot", [(1, 1), (0, 1)]),
            ("pair", [(1, 0), (0, 1)]),
            ("pair", [(1, 1), (0, 1)]),
            ("vertical_pair", [(0, 1), (1, 0)]),
            ("vertical_pair", [(1, 1), (0, 1)]),
            ("elbow", [(1, 0), (0, 1)]),
            ("elbow", [(1, 1), (0, 1)]),
            ("tee", [(1, 0), (0, 1)]),
        ]
    ],
    *[
        (
            "complex_symbolic_remapping",
            ["symbolic_remapping"],
            "targeted_composite",
            shape_name,
            compose(spatial_transform, transform(recolor_nonzero, color)),
        )
        for shape_name, spatial_transform, color in [
            ("dot", transform(shift, 0, 1), 3),
            ("dot", transform(shift, 1, 0), 4),
            ("pair", transform(shift, 1, 0), 5),
            ("pair", mirror_horizontal, 6),
            ("vertical_pair", transform(shift, 0, 1), 7),
            ("vertical_pair", rotate_clockwise, 3),
            ("elbow", transform(shift, 1, 1), 4),
            ("elbow", mirror_horizontal, 5),
            ("tee", transform(shift, 1, 0), 6),
            ("two_colors", rotate_clockwise, 7),
        ]
    ],
    *[
        (
            "shape_transform",
            ["shape_transform"],
            "targeted_shape",
            "elbow",
            rotate_clockwise,
        ),
        (
            "color_transform",
            ["color_transform"],
            "targeted_color",
            "two_colors",
            lambda source: recolor(source, {1: 8, 2: 9}),
        ),
        (
            "topological_growth",
            ["topological_growth"],
            "targeted_growth",
            "pair",
            transform(grow, 1, 0),
        ),
    ],
    *[
        (
            "causal_sequence",
            concepts,
            "causal_sequence",
            shape_name,
            compose(*operations),
        )
        for concepts, shape_name, operations in [
            (
                ["replication", "symbolic_remapping"],
                "dot",
                [transform(replicate, 0, 2), transform(recolor_nonzero, 3)],
            ),
            (
                ["replication", "symbolic_remapping"],
                "dot",
                [transform(replicate, 2, 0), transform(recolor_nonzero, 4)],
            ),
            (
                ["density_modulation", "symbolic_remapping"],
                "pair",
                [transform(grow, 1, 0), transform(recolor_nonzero, 5)],
            ),
            (
                ["density_modulation", "symbolic_remapping"],
                "vertical_pair",
                [transform(grow, 0, 1), transform(recolor_nonzero, 6)],
            ),
            (
                ["topological_reasoning", "symbolic_remapping"],
                "dot",
                [transform(replicate, 2, 2), transform(recolor_nonzero, 7)],
            ),
            (
                ["topological_reasoning", "density_modulation"],
                "pair",
                [transform(replicate, 2, 0), transform(grow, 0, 1)],
            ),
            (
                ["propagation", "symbolic_remapping"],
                "elbow",
                [transform(grow, 1, 0), transform(recolor_nonzero, 3)],
            ),
            (
                ["propagation", "symbolic_remapping"],
                "tee",
                [transform(grow, 1, 0), transform(recolor_nonzero, 4)],
            ),
            (
                ["topological_change", "symbolic_remapping"],
                "vertical_pair",
                [transform(replicate, 1, 2), transform(recolor_nonzero, 5)],
            ),
            (
                ["replication", "density_modulation"],
                "elbow",
                [transform(replicate, 0, 2), transform(grow, 1, 0)],
            ),
        ]
    ],
]

SCARCITY_CASES = [
    *[
        (
            "topology_scarcity",
            ["topological_reasoning", "topological_change"],
            "scarcity_topology",
            shape_name,
            compose(*operations),
        )
        for shape_name, operations in [
            ("pair", [transform(replicate, 1, 2), transform(grow, 1, 0)]),
            ("pair", [transform(replicate, 2, 1), transform(grow, 0, 1)]),
            ("vertical_pair", [transform(replicate, 2, 1), transform(grow, 0, 1)]),
            ("vertical_pair", [transform(replicate, 1, 2), transform(grow, 1, 0)]),
            ("elbow", [transform(replicate, 0, 3), transform(grow, 1, 0)]),
            ("elbow", [transform(replicate, 3, 0), transform(grow, 0, 1)]),
            ("tee", [transform(replicate, 2, 0), transform(grow, 0, 1)]),
            ("tee", [transform(replicate, 0, 1), transform(grow, 1, 0)]),
            ("edge_pair", [transform(replicate, 2, -1), transform(grow, 1, 0)]),
        ]
    ],
    *[
        (
            "shape_transform_scarcity",
            ["shape_transform", "shape_change"],
            "scarcity_shape",
            "pair",
            mirror_horizontal,
        ),
        (
            "color_transform_scarcity",
            ["color_transform", "color_change"],
            "scarcity_color",
            "two_colors",
            lambda source: recolor(source, {1: 9, 2: 10}),
        ),
    ],
    *[
        (
            "density_scarcity",
            ["density_modulation", "propagation"],
            "scarcity_density",
            shape_name,
            transform(spread, offsets),
        )
        for shape_name, offsets in [
            ("dot", [(0, 2), (2, 0)]),
            ("dot", [(1, 2), (2, 1)]),
            ("pair", [(0, 1), (2, 0)]),
            ("vertical_pair", [(1, 0), (0, 2)]),
            ("elbow", [(0, 1), (2, 0)]),
            ("tee", [(1, 0), (0, 1), (1, 1)]),
        ]
    ],
]


def recolored(source, color):
    return recolor(source, {1: color, 2: color + 1})


def build_task(sequence, case, curriculum="phase_7_prelude_batch_01"):
    group, concepts, probe_kind, shape_name, operation = case
    first_input = SHAPES[shape_name]
    second_input = recolored(first_input, 2)
    test_input = recolored(first_input, 4)
    return {
        "nexryn_metadata": {
            "curriculum": curriculum,
            "sequence": sequence,
            "group": group,
            "target_concepts": concepts,
            "probe_kind": probe_kind,
        },
        "train": [
            {
                "input": first_input,
                "output": operation(first_input),
            },
            {
                "input": second_input,
                "output": operation(second_input),
            },
        ],
        "test": [
            {
                "input": test_input,
            },
        ],
    }


def main():
    TRAINING_DIRECTORY.mkdir(parents=True, exist_ok=True)
    written = []
    for offset, case in enumerate(CASES):
        sequence = FIRST_TASK_NUMBER + offset
        path = TRAINING_DIRECTORY / f"task_{sequence:03d}.json"
        path.write_text(
            json.dumps(build_task(sequence, case), indent=2) + "\n",
            encoding="utf-8",
        )
        written.append(str(path))
    for offset, case in enumerate(TARGETED_CASES):
        sequence = TARGETED_BATCH_FIRST_TASK_NUMBER + offset
        path = TRAINING_DIRECTORY / f"task_{sequence:03d}.json"
        path.write_text(
            json.dumps(
                build_task(
                    sequence,
                    case,
                    curriculum="phase_7_targeted_batch_02",
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        written.append(str(path))
    for offset, case in enumerate(SCARCITY_CASES):
        sequence = SCARCITY_BATCH_FIRST_TASK_NUMBER + offset
        path = TRAINING_DIRECTORY / f"task_{sequence:03d}.json"
        path.write_text(
            json.dumps(
                build_task(
                    sequence,
                    case,
                    curriculum="phase_7_scarcity_batch_03",
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        written.append(str(path))
    print(f"generated={len(written)}")
    print(f"first={written[0]}")
    print(f"last={written[-1]}")


if __name__ == "__main__":
    main()
