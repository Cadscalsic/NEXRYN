"""Capability input and output contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InputContract:
    required_inputs: tuple[str, ...] = ()
    optional_inputs: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "required_inputs": list(self.required_inputs),
            "optional_inputs": list(self.optional_inputs),
        }


@dataclass(frozen=True)
class OutputContract:
    produced_outputs: tuple[str, ...] = ()
    optional_outputs: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "produced_outputs": list(self.produced_outputs),
            "optional_outputs": list(self.optional_outputs),
        }


__all__ = ["InputContract", "OutputContract"]
