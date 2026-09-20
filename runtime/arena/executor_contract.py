"""Authoritative identity and replay policy for the Arena candidate executor."""

EXECUTOR_CONTRACT_ID = "nexryn.arena.candidate_simulator"
EXECUTOR_CONTRACT_VERSION = "1.0"
EXECUTOR_FINGERPRINT_NAMESPACE = (
    f"{EXECUTOR_CONTRACT_ID}@{EXECUTOR_CONTRACT_VERSION}"
)
EXECUTOR_NORMALIZATION_VERSION = "candidate_normalizer.v1"

EXACT_VERSION_REPLAY = "EXACT_VERSION_REPLAY"
VERIFIED_COMPATIBLE_REPLAY = "VERIFIED_COMPATIBLE_REPLAY"
MIGRATION_REQUIRED = "MIGRATION_REQUIRED"
UNSUPPORTED_LEGACY_CONTRACT = "UNSUPPORTED_LEGACY_CONTRACT"
UNDETERMINED = "UNDETERMINED"


def classify_replay(contract_id: object, contract_version: object) -> str:
    """Fail closed unless an artifact names the exact current contract."""
    if (
        str(contract_id) == EXECUTOR_CONTRACT_ID
        and str(contract_version) == EXECUTOR_CONTRACT_VERSION
    ):
        return EXACT_VERSION_REPLAY
    if str(contract_id) == EXECUTOR_CONTRACT_ID and contract_version:
        return MIGRATION_REQUIRED
    if contract_id:
        return UNSUPPORTED_LEGACY_CONTRACT
    return UNDETERMINED


__all__ = [
    "EXECUTOR_CONTRACT_ID",
    "EXECUTOR_CONTRACT_VERSION",
    "EXECUTOR_FINGERPRINT_NAMESPACE",
    "EXECUTOR_NORMALIZATION_VERSION",
    "classify_replay",
]
