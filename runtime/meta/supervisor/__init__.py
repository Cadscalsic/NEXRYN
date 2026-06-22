"""Meta-cognitive supervisor authority."""

from runtime.meta.supervisor.execution_memory import (
    ExecutionMemory,
    ExecutionRecord,
    execution_memory,
)
from runtime.meta.supervisor.meta_supervisor import (
    CognitiveDirective,
    MetaSupervisor,
    meta_supervisor,
)
from runtime.meta.supervisor.program_memory import (
    ProgramMemory,
    ProgramRecord,
    program_memory,
)
from runtime.meta.supervisor.strategy_memory import (
    StrategyMemory,
    StrategyRecord,
    strategy_memory,
)
from runtime.meta.supervisor.task_signature_engine import (
    TaskSignature,
    TaskSignatureEngine,
    task_signature_engine,
)


__all__ = [
    "CognitiveDirective",
    "ExecutionMemory",
    "ExecutionRecord",
    "MetaSupervisor",
    "ProgramMemory",
    "ProgramRecord",
    "StrategyMemory",
    "StrategyRecord",
    "TaskSignature",
    "TaskSignatureEngine",
    "execution_memory",
    "meta_supervisor",
    "program_memory",
    "strategy_memory",
    "task_signature_engine",
]
