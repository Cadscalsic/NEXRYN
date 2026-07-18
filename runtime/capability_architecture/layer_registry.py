"""Canonical layer registry for capability providers."""

from __future__ import annotations

from typing import Any

from runtime.capability_architecture.layer_descriptor import LayerDescriptor


class LayerRegistry:
    def __init__(self):
        self._layers: dict[str, LayerDescriptor] = {}
        self.registration_failures: list[dict[str, Any]] = []

    def register(self, descriptor: LayerDescriptor) -> bool:
        if not descriptor.layer_id or not descriptor.layer_name:
            self.registration_failures.append({
                "layer_id": descriptor.layer_id,
                "layer_name": descriptor.layer_name,
                "reason": "INVALID_LAYER_DESCRIPTOR",
            })
            return False
        self._layers[descriptor.layer_name] = descriptor
        return True

    def get(self, layer_name: str) -> LayerDescriptor | None:
        return self._layers.get(str(layer_name))

    def all(self) -> list[LayerDescriptor]:
        return list(self._layers.values())

    def legacy_layers(self) -> list[LayerDescriptor]:
        return [item for item in self.all() if item.legacy_status == "LEGACY"]

    def as_dict(self) -> dict[str, Any]:
        return {
            "layers": {
                item.layer_name: item.as_dict()
                for item in self.all()
            },
            "registration_failures": list(self.registration_failures),
        }


__all__ = ["LayerRegistry"]
