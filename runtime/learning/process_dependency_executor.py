"""Runtime learning export for process dependency reasoning execution."""

from runtime.process.process_dependency_executor import ProcessDependencyExecutor


process_dependency_executor = ProcessDependencyExecutor()


__all__ = ["ProcessDependencyExecutor", "process_dependency_executor"]
