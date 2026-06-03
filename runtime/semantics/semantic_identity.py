# ============================================
# NEXRYN SEMANTIC IDENTITY
# ============================================

from dataclasses import dataclass


IDENTITY_PREFIX_LAYERS = {
    "structural": "structural_signature",
    "causal": "causal_signature",
    "geometric": "geometric_signature",
    "spatial": "geometric_signature",
    "symbolic": "symbolic_signature",
    "color": "symbolic_signature",
    "quantitative": "behavioral_signature",
    "count": "behavioral_signature",
    "density": "behavioral_signature",
    "object": "structural_signature",
    "translation": "geometric_signature",
    "topology": "structural_signature",
    "size": "structural_signature"
}


@dataclass
class SemanticIdentity:

    causal_signature: str = "none"
    structural_signature: str = "none"
    symbolic_signature: str = "none"
    geometric_signature: str = "none"
    behavioral_signature: str = "none"

    def as_dict(self):

        return {
            "causal_signature": self.causal_signature,
            "structural_signature": self.structural_signature,
            "symbolic_signature": self.symbolic_signature,
            "geometric_signature": self.geometric_signature,
            "behavioral_signature": self.behavioral_signature
        }


def build_semantic_identity(
    strategy_name
):

    identity = SemanticIdentity()

    tokens = str(
        strategy_name
    ).split(
        "_"
    )

    for token in tokens:

        layer = IDENTITY_PREFIX_LAYERS.get(
            token
        )

        if layer is None:

            continue

        current_value = getattr(
            identity,
            layer
        )

        if current_value == "none":

            setattr(
                identity,
                layer,
                token
            )

        elif token not in current_value.split("+"):

            setattr(
                identity,
                layer,
                current_value + "+" + token
            )

    return identity


def identity_overlap(
    first_identity,
    second_identity
):

    first = first_identity.as_dict()
    second = second_identity.as_dict()

    active_layers = 0
    shared_layers = 0
    conflicting_layers = 0

    for key in first:

        first_value = first.get(key)
        second_value = second.get(key)

        if first_value == "none" and second_value == "none":

            continue

        active_layers += 1

        if first_value == second_value:

            shared_layers += 1

        elif first_value != "none" and second_value != "none":

            conflicting_layers += 1

    if active_layers == 0:

        return {
            "overlap": 0.0,
            "conflict": 0.0,
            "active_layers": 0,
            "shared_layers": 0,
            "conflicting_layers": 0
        }

    return {
        "overlap": round(shared_layers / active_layers, 4),
        "conflict": round(conflicting_layers / active_layers, 4),
        "active_layers": active_layers,
        "shared_layers": shared_layers,
        "conflicting_layers": conflicting_layers
    }
