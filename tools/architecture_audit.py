# ============================================
# NEXRYN ARCHITECTURE AUDIT TOOL
# ============================================

import json
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ACTIVE_STAGE_FILE = ROOT / "runtime" / "stages" / "__init__.py"

LEGACY_DUPLICATION_GROUPS = {
    "stage_registry": [
        "runtime/stage_registry.py",
        "runtime/stages/registry.py"
    ],
    "program_synthesis": [
        "core/synthesis.py",
        "runtime/engines/program_synthesis.py",
        "runtime/synthesis/program_synthesis_engine.py"
    ],
    "execution_runtime": [
        "runtime/transforms/primitive_executor.py",
        "runtime/execution/execution_engine.py",
        "runtime/synthesis/adaptive_execution_engine.py",
        "runtime/engines/transformation_engine.py"
    ],
    "kernel_runtime": [
        "runtime/kernel/cognitive_kernel.py",
        "runtime/cognitive_kernel/cognitive_kernel.py"
    ],
    "runtime_state": [
        "runtime/runtime_state.py",
        "runtime/state/runtime_state.py"
    ],
    "runtime_scheduler": [
        "runtime/scheduler.py",
        "runtime/scheduler/runtime_scheduler.py"
    ]
}


def relative(path):

    return str(
        path.relative_to(ROOT)
    ).replace(
        "\\",
        "/"
    )


def list_python_files():

    ignored_parts = {
        ".venv",
        "__pycache__"
    }

    files = []

    for path in ROOT.rglob("*.py"):

        parts = set(
            path.parts
        )

        if parts.intersection(
            ignored_parts
        ):

            continue

        files.append(
            path
        )

    return sorted(
        files
    )


def find_python_inside_pycache():

    return sorted([
        relative(path)
        for path in ROOT.rglob("*.py")
        if "__pycache__" in path.parts
    ])


def find_project_python_inside_pycache():

    return sorted([
        relative(path)
        for path in ROOT.rglob("*.py")
        if "__pycache__" in path.parts
        and ".venv" not in path.parts
    ])


def find_pycache_virtualenv_sources():

    return sorted([
        relative(path)
        for path in ROOT.rglob("*.py")
        if "__pycache__" in path.parts
        and ".venv" in path.parts
    ])


def count_pycache_dirs():

    return len([
        path
        for path in ROOT.rglob("__pycache__")
        if path.is_dir()
    ])


def find_duplicate_exports():

    duplicates = []

    for path in list_python_files():

        text = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        count = text.count(
            "__all__ ="
        )

        if count > 1:

            duplicates.append({
                "file":
                relative(path),

                "count":
                count
            })

    return duplicates


def file_exists(path):

    return (
        ROOT
        /
        path
    ).exists()


def build_duplication_report():

    report = {}

    for group, paths in LEGACY_DUPLICATION_GROUPS.items():

        status = (
            "duplicate_active_surface"
            if sum(
                1
                for path in paths
                if file_exists(path)
            ) > 1
            else "single_surface"
        )

        if group == "stage_registry":

            wrapper_path = ROOT / "runtime" / "stage_registry.py"

            if (
                wrapper_path.exists()
                and
                "compatibility wrapper" in wrapper_path.read_text(
                    encoding="utf-8",
                    errors="ignore"
                ).lower()
            ):

                status = "compatibility_wrapper"

        if group == "runtime_state":

            wrapper_path = ROOT / "runtime" / "runtime_state.py"

            if (
                wrapper_path.exists()
                and
                "compatibility wrapper" in wrapper_path.read_text(
                    encoding="utf-8",
                    errors="ignore"
                ).lower()
            ):

                status = "compatibility_wrapper"

        report[group] = {
            "paths":
            paths,

            "existing":
            [
                path
                for path in paths
                if file_exists(path)
            ],

            "status":
            status
        }

    return report


def find_shadowed_root_modules():

    shadowed = []

    runtime_root = ROOT / "runtime"

    if not runtime_root.exists():

        return shadowed

    for path in runtime_root.glob("*.py"):

        sibling_package = runtime_root / path.stem

        if sibling_package.is_dir() and (
            sibling_package / "__init__.py"
        ).exists():

            shadowed.append({
                "module_file":
                relative(path),

                "package":
                relative(sibling_package),

                "risk":
                "module_package_name_collision"
            })

    return shadowed


def find_missing_package_initializers():

    missing = []

    ignored_parts = {
        ".venv",
        "__pycache__"
    }

    for path in ROOT.rglob("*"):

        if not path.is_dir():

            continue

        if set(path.parts).intersection(
            ignored_parts
        ):

            continue

        has_python = any(
            child.suffix == ".py"
            for child in path.iterdir()
            if child.is_file()
        )

        if has_python and not (
            path / "__init__.py"
        ).exists():

            missing.append(
                relative(path)
            )

    return sorted(
        missing
    )


def read_active_stage_path():

    if not ACTIVE_STAGE_FILE.exists():

        return {
            "status":
            "missing",

            "file":
            relative(ACTIVE_STAGE_FILE)
        }

    text = ACTIVE_STAGE_FILE.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    stage_names = []

    tree = ast.parse(
        text
    )

    for node in tree.body:

        if not isinstance(
            node,
            ast.Assign
        ):

            continue

        target_names = [
            target.id
            for target in node.targets
            if isinstance(
                target,
                ast.Name
            )
        ]

        if "NEXRYN_STAGE_SEQUENCE" not in target_names:

            continue

        if not isinstance(
            node.value,
            ast.List
        ):

            continue

        for element in node.value.elts:

            if isinstance(
                element,
                ast.Name
            ):

                stage_names.append(
                    element.id
                )

    return {
        "status":
        "present",

        "file":
        relative(ACTIVE_STAGE_FILE),

        "stage_count":
        len(stage_names),

        "stages":
        stage_names
    }


def build_audit_report():

    python_files = list_python_files()

    pycache_python_files = find_python_inside_pycache()

    project_pycache_sources = find_project_python_inside_pycache()

    pycache_venv_sources = find_pycache_virtualenv_sources()

    return {
        "project_root":
        str(ROOT),

        "python_file_count":
        len(python_files),

        "pycache_directory_count":
        count_pycache_dirs(),

        "python_files_inside_pycache":
        pycache_python_files[:50],

        "python_files_inside_pycache_count":
        len(pycache_python_files),

        "project_python_files_inside_pycache":
        project_pycache_sources,

        "project_python_files_inside_pycache_count":
        len(project_pycache_sources),

        "pycache_virtualenv_python_files_count":
        len(pycache_venv_sources),

        "duplicate_exports":
        find_duplicate_exports(),

        "shadowed_root_modules":
        find_shadowed_root_modules(),

        "missing_package_initializers":
        find_missing_package_initializers(),

        "active_stage_path":
        read_active_stage_path(),

        "duplication_report":
        build_duplication_report(),

        "recommendations":
        [
            "Keep runtime/stages/__init__.py as the canonical active stage path.",
            "Treat core/* as legacy unless explicitly imported by main.py or runtime.pipeline.",
            "Route new ARC execution through runtime/transforms/primitive_executor.py first.",
            "Avoid broad compileall over the repository root because it can traverse generated environments.",
            "Keep Python source files out of __pycache__ directories."
        ]
    }


def main():

    print(
        json.dumps(
            build_audit_report(),
            indent=2,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":

    main()
