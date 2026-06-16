"""Compatibility export for canonical process signature extraction."""

from core.process.process_signature_engine import (
    PROCESS_SIGNATURE_RULES as SIGNATURE_RULES,
    ProcessSignatureEngine,
)

__all__ = [
    "ProcessSignatureEngine",
    "SIGNATURE_RULES",
]
