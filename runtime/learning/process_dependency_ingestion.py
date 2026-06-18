"""Runtime learning export for typed process dependency ingestion."""

from runtime.process.process_dependency_ingestion import (
    ProcessDependencyIngestion,
)


process_dependency_ingestion = ProcessDependencyIngestion()


__all__ = ["ProcessDependencyIngestion", "process_dependency_ingestion"]
