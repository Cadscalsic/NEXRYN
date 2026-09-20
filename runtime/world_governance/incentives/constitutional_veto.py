"""Constitutional veto authority for non-voting core principles."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


NON_VOTING_CONSTITUTIONAL_CORE: frozenset[str] = frozenset({
    "truth_priority",
    "identity_continuity",
    "anti_domination",
    "human_support_mission",
    "evidence_before_truth",
    "locked_truth_integrity",
})


class ConstitutionalVeto:
    def evaluate(self, proposal: Mapping[str, Any] | Any) -> dict[str, Any]:
        data = self._data(proposal)
        touched = set()
        for key in ("modifies", "targets", "overrides", "weakens", "votes_on"):
            values = data.get(key, []) or []
            if isinstance(values, str):
                values = [values]
            touched.update(str(value).strip().lower() for value in values)
        direct = {str(key).strip().lower() for key in data.keys()}
        mentioned = set(self._mentioned_core_principles(data))
        violations = sorted(
            (touched | direct | mentioned) & NON_VOTING_CONSTITUTIONAL_CORE
        )
        if violations:
            return {
                "decision": "CONSTITUTIONAL_VETO",
                "allowed": False,
                "constitutional_violations": violations,
                "reason": "proposal_attempts_to_modify_non_voting_constitutional_core",
            }
        return {
            "decision": "PASS",
            "allowed": True,
            "constitutional_violations": [],
            "reason": "non_voting_constitutional_core_not_touched",
        }

    def _data(self, value: Mapping[str, Any] | Any) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        return dict(getattr(value, "__dict__", {}))

    def _mentioned_core_principles(self, value: Any) -> Iterable[str]:
        if isinstance(value, Mapping):
            for key, item in value.items():
                yield from self._mentioned_core_principles(key)
                yield from self._mentioned_core_principles(item)
            return
        if isinstance(value, (list, tuple, set, frozenset)):
            for item in value:
                yield from self._mentioned_core_principles(item)
            return
        text = str(value).lower()
        for principle in NON_VOTING_CONSTITUTIONAL_CORE:
            if principle in text:
                yield principle


constitutional_veto = ConstitutionalVeto()


__all__ = [
    "NON_VOTING_CONSTITUTIONAL_CORE",
    "ConstitutionalVeto",
    "constitutional_veto",
]
