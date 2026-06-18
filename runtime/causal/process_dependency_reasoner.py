"""Runtime causal export for typed process dependency reasoning."""

from runtime.process.process_dependency_reasoner import ProcessDependencyReasoner


process_dependency_reasoner = ProcessDependencyReasoner()


__all__ = ["ProcessDependencyReasoner", "process_dependency_reasoner"]
