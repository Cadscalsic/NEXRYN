"""Execute the typed dependency reasoning pipeline."""

from __future__ import annotations

from typing import Iterable

from runtime.process.process_dependency_resolver import (
    ProcessDependencyResolver,
)
from runtime.process.process_dependency_validator import (
    ProcessDependencyValidator,
)


class ProcessDependencyExecutor:
    """Run typed resolution, chain construction, validation, and reporting."""

    system_name = "process_dependency_executor"

    def __init__(
        self,
        resolver: ProcessDependencyResolver | None = None,
        validator: ProcessDependencyValidator | None = None,
    ):
        self.resolver = resolver or ProcessDependencyResolver()
        self.validator = validator or ProcessDependencyValidator()

    def execute(
        self,
        concept: str,
        observed_contradictions: Iterable[str] | None = None,
    ) -> dict:
        report = self.resolver.resolve(
            concept,
            observed_contradictions=observed_contradictions,
        )
        validation = self.validator.validate(report)
        return {
            **report,
            "system": self.system_name,
            "typed_dependency_validation_report": validation,
            "architecture_bottleneck": False,
            "recommended_next_step": "consume_reasoned_dependency_chains",
            "governance_consumable": bool(
                validation.get("typed_dependency_validation_passed")
                and report.get("dependency_chain_depth", 0) > 0
                and report.get("dependency_chain_coverage", 0.0) > 0.0
            ),
        }


__all__ = ["ProcessDependencyExecutor"]
