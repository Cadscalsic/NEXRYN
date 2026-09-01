import importlib
import importlib.util
import sys
import types

from tools.architecture_audit import build_audit_report


def test_runtime_pipeline_import_resolves_to_canonical_package():
    spec = importlib.util.find_spec("runtime.pipeline")

    assert spec is not None
    assert spec.origin.replace("\\", "/").endswith("runtime/pipeline/__init__.py")
    assert spec.submodule_search_locations

    pipeline_module = importlib.import_module("runtime.pipeline")

    assert pipeline_module.__file__.replace("\\", "/").endswith(
        "runtime/pipeline/__init__.py"
    )
    assert pipeline_module.CANONICAL_PRODUCTION_PIPELINE == (
        "runtime.pipeline.legacy_pipeline.AdaptiveCognitivePipeline"
    )
    assert pipeline_module.CANONICAL_ENTRY_SYMBOL == "pipeline"
    assert pipeline_module.PIPELINE_NAMESPACE_STATE == "PACKAGE_OWNS_NAMESPACE"


def test_pipeline_compatibility_proxy_delegates_to_canonical_owner(monkeypatch):
    pipeline_module = importlib.import_module("runtime.pipeline")

    class CanonicalPipeline:
        def run(self, *args, **kwargs):
            return {"args": args, "kwargs": kwargs, "owner": "canonical"}

    class CanonicalPipelineClass:
        pass

    fake_legacy = types.SimpleNamespace(
        pipeline=CanonicalPipeline(),
        AdaptiveCognitivePipeline=CanonicalPipelineClass,
    )
    monkeypatch.setitem(
        sys.modules,
        "runtime.pipeline.legacy_pipeline",
        fake_legacy,
    )

    assert pipeline_module.pipeline.run("task", mode="adaptive") == {
        "args": ("task",),
        "kwargs": {"mode": "adaptive"},
        "owner": "canonical",
    }
    assert pipeline_module.AdaptiveCognitivePipeline is CanonicalPipelineClass


def test_architecture_audit_classifies_pipeline_file_as_intentional_compatibility():
    report = build_audit_report()

    assert "runtime/pipeline.py" not in {
        item["module_file"] for item in report["shadowed_root_modules"]
    }
    assert {
        "module_file": "runtime/pipeline.py",
        "package": "runtime/pipeline",
        "resolution": "runtime/pipeline/__init__.py",
        "status": "intentional_package_namespace_with_compatibility_module",
        "canonical_owner": (
            "runtime.pipeline.legacy_pipeline.AdaptiveCognitivePipeline"
        ),
    } in report["intentional_namespace_compatibility_surfaces"]
