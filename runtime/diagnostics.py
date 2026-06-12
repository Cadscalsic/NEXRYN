# runtime/diagnostics.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ConceptDiagnostic:
    name: str
    strength: Optional[float] = None
    state: Optional[str] = None
    candidate_ready: Optional[bool] = None
    contradiction: Optional[float] = None
    causal_validation_score: Optional[float] = None
    contextual_truth_score: Optional[float] = None
    semantic_context_score: Optional[float] = None
    failed_gates: Optional[List[str]] = None
    why: Optional[List[str]] = None
    how_we_know: Optional[List[str]] = None
    when_valid: Optional[List[str]] = None
    when_invalid: Optional[List[str]] = None


class RuntimeDiagnostics:
    """
    Diagnostic inspection layer for NEXRYN.

    This module does not change cognitive decisions.
    It only reads runtime reports, memory objects, and governance outputs
    to explain what the system knows and why concepts are blocked.
    """

    def __init__(self, runtime: Any):
        self.runtime = runtime

    # --------------------------------------------------
    # SAFE GETTERS
    # --------------------------------------------------

    def _get(self, name: str, default: Any = None) -> Any:
        return getattr(self.runtime, name, default)

    def _get_report(self) -> Dict[str, Any]:
        return (
            self._get("report", None)
            or self._get("runtime_report", None)
            or self._get("last_report", None)
            or {}
        )

    def _get_concepts(self) -> Dict[str, Any]:
        report = self._get_report()
        return (
            report.get("concepts")
            or self._get("concepts", None)
            or self._get("concept_memory", None)
            or {}
        )

    def _get_truth_candidates(self) -> Dict[str, Any]:
        report = self._get_report()
        return (
            report.get("truth_candidates")
            or report.get("truth_candidate_report")
            or self._get("truth_candidates", None)
            or {}
        )

    def _get_truth_commits(self) -> Dict[str, Any]:
        report = self._get_report()
        return (
            report.get("truth_commits")
            or report.get("truth_commit_report")
            or self._get("truth_commits", None)
            or {}
        )

    def _get_contexts(self) -> Any:
        report = self._get_report()
        return (
            report.get("contexts")
            or report.get("contextual_truth_report")
            or report.get("context_discovery_report")
            or self._get("contexts", None)
            or {}
        )

    def _get_truth_graveyard_consistency(self) -> Dict[str, Any]:
        report = self._get_report()
        governance = report.get("governance_reports", {})

        return (
            report.get("truth_graveyard_consistency_report")
            or report.get("truth_graveyard_consistency")
            or governance.get("truth_graveyard_consistency")
            or self._get("truth_graveyard_consistency_report", None)
            or {}
        )

    # --------------------------------------------------
    # PUBLIC COMMANDS
    # --------------------------------------------------

    def stats(self) -> None:
        concepts = self._get_concepts()
        candidates = self._get_truth_candidates()
        commits = self._get_truth_commits()

        stable_truths = []
        boundary = []
        discovering = []

        for name, data in concepts.items():
            state = self._read_field(data, "state")
            if state == "STABLE_TRUTH":
                stable_truths.append(name)
            elif state == "BOUNDARY_REFINEMENT":
                boundary.append(name)
            elif state == "DISCOVERING":
                discovering.append(name)

        print("\n==================================================")
        print("NEXRYN :: COGNITIVE STATS")
        print("==================================================")
        print(f"Total Concepts: {len(concepts)}")
        print(f"Stable Truths: {len(stable_truths)}")
        print(f"Boundary Refinement: {len(boundary)}")
        print(f"Discovering: {len(discovering)}")
        print(f"Truth Candidates: {len(candidates)}")
        print(f"Truth Commit Entries: {len(commits)}")

        if stable_truths:
            print("\nStable Truths:")
            for item in stable_truths:
                print(f"  - {item}")

        if boundary:
            print("\nBoundary Refinement Concepts:")
            for item in boundary:
                print(f"  - {item}")

    def audit(self) -> None:
        concepts = self._get_concepts()

        print("\n==================================================")
        print("NEXRYN :: CONCEPT AUDIT")
        print("==================================================")

        if not concepts:
            print("No concept data available.")
            return

        for name, data in concepts.items():
            diagnostic = self._build_concept_diagnostic(name, data)
            self._print_concept_summary(diagnostic)

        self._print_truth_graveyard_consistency()

    def explain(self, concept_name: str) -> None:
        concepts = self._get_concepts()
        candidates = self._get_truth_candidates()
        commits = self._get_truth_commits()

        print("\n==================================================")
        print(f"NEXRYN :: EXPLAIN CONCEPT :: {concept_name}")
        print("==================================================")

        concept_data = concepts.get(concept_name)
        candidate_data = candidates.get(concept_name)
        commit_data = commits.get(concept_name)

        if concept_data is None and candidate_data is None and commit_data is None:
            print(f"Concept not found: {concept_name}")
            return

        merged = {}
        for source in [concept_data, candidate_data, commit_data]:
            if isinstance(source, dict):
                merged.update(source)

        diagnostic = self._build_concept_diagnostic(concept_name, merged)

        self._print_concept_summary(diagnostic)

        print("\nWhy:")
        self._print_list(diagnostic.why)

        print("\nHow We Know:")
        self._print_list(diagnostic.how_we_know)

        print("\nWhen Valid:")
        self._print_list(diagnostic.when_valid)

        print("\nWhen Invalid:")
        self._print_list(diagnostic.when_invalid)

        failed = diagnostic.failed_gates or []
        if failed:
            print("\nBlocked By:")
            for gate in failed:
                print(f"  - {gate}")
        else:
            print("\nBlocked By: none detected")

    def identity(self) -> None:
        commits = self._get_truth_commits()

        print("\n==================================================")
        print("NEXRYN :: IDENTITY GOVERNANCE DIAGNOSTICS")
        print("==================================================")

        if not commits:
            print("No identity governance data available.")
            return

        for name, data in commits.items():
            identity_state = self._read_field(data, "identity_state")
            governance_state = self._read_field(data, "identity_governance_state")
            failed_gates = self._read_field(data, "failed_identity_governance_gates", [])

            print(f"\n{name}")
            print(f"  identity_state: {identity_state}")
            print(f"  governance_state: {governance_state}")

            if failed_gates:
                print("  failed_identity_gates:")
                for gate in failed_gates:
                    print(f"    - {gate}")
            else:
                print("  failed_identity_gates: none")

    def contexts(self) -> None:
        contexts = self._get_contexts()

        print("\n==================================================")
        print("NEXRYN :: CONTEXT DIAGNOSTICS")
        print("==================================================")

        if not contexts:
            print("No context data available.")
            return

        if isinstance(contexts, dict):
            for name, data in contexts.items():
                print(f"\n{name}")
                if isinstance(data, dict):
                    for key, value in data.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {data}")
        elif isinstance(contexts, list):
            for item in contexts:
                print(f"  - {item}")
        else:
            print(contexts)

    def truths(self) -> None:
        concepts = self._get_concepts()

        print("\n==================================================")
        print("NEXRYN :: STABLE TRUTHS")
        print("==================================================")

        for name, data in concepts.items():
            if self._read_field(data, "state") == "STABLE_TRUTH":
                strength = self._read_field(data, "strength")
                contradiction = self._read_field(data, "ledger_average_contradiction")
                print(f"{name} strength={strength} contradiction={contradiction}")

    def candidates(self) -> None:
        candidates = self._get_truth_candidates()

        print("\n==================================================")
        print("NEXRYN :: TRUTH CANDIDATES")
        print("==================================================")

        if not candidates:
            print("No truth candidate data available.")
            return

        for name, data in candidates.items():
            eligible = self._read_field(data, "eligible")
            blocked = self._read_field(data, "blocked", [])
            contradiction = self._read_field(data, "effective_contradiction")
            print(f"\n{name}")
            print(f"  eligible: {eligible}")
            print(f"  contradiction: {contradiction}")
            print(f"  blocked: {blocked}")

    # --------------------------------------------------
    # INTERNAL HELPERS
    # --------------------------------------------------

    def _read_field(self, data: Any, field: str, default: Any = None) -> Any:
        if isinstance(data, dict):
            return data.get(field, default)
        return getattr(data, field, default)

    def _build_concept_diagnostic(self, name: str, data: Any) -> ConceptDiagnostic:
        return ConceptDiagnostic(
            name=name,
            strength=self._read_field(data, "strength"),
            state=self._read_field(data, "state"),
            candidate_ready=self._read_field(data, "candidate_ready"),
            contradiction=(
                self._read_field(data, "ledger_average_contradiction")
                or self._read_field(data, "effective_contradiction")
            ),
            causal_validation_score=self._read_field(data, "causal_validation_score"),
            contextual_truth_score=self._read_field(data, "contextual_truth_score"),
            semantic_context_score=self._read_field(data, "semantic_context_score"),
            failed_gates=self._read_field(data, "failed_gates", []),
            why=self._read_field(data, "why", []),
            how_we_know=self._read_field(data, "how_we_know", []),
            when_valid=self._read_field(data, "when_valid", []),
            when_invalid=self._read_field(data, "when_invalid", []),
        )

    def _print_concept_summary(self, diagnostic: ConceptDiagnostic) -> None:
        print(f"\n{diagnostic.name}")
        print(f"  state: {diagnostic.state}")
        print(f"  strength: {diagnostic.strength}")
        print(f"  candidate_ready: {diagnostic.candidate_ready}")
        print(f"  contradiction: {diagnostic.contradiction}")
        print(f"  causal_validation_score: {diagnostic.causal_validation_score}")
        print(f"  contextual_truth_score: {diagnostic.contextual_truth_score}")
        print(f"  semantic_context_score: {diagnostic.semantic_context_score}")

    def _print_truth_graveyard_consistency(self) -> None:
        report = self._get_truth_graveyard_consistency()

        if not report:
            return

        print("\n==================================================")
        print("NEXRYN :: TRUTH / GRAVEYARD CONSISTENCY")
        print("==================================================")
        print(
            "truth_graveyard_conflicts:",
            report.get("truth_graveyard_conflicts", 0),
        )
        print(
            "stale_graveyard_entries:",
            report.get("stale_graveyard_entries", 0),
        )
        print(
            "resurrection_conflicts:",
            report.get("resurrection_conflicts", 0),
        )
        print(
            "constitutional_consistency_score:",
            report.get("constitutional_consistency_score"),
        )

        audit_rows = report.get("audit_report", [])
        if not audit_rows:
            print("audit_report: none")
            return

        print("\nAudit Report:")
        for row in audit_rows:
            if not (
                row.get("state_conflict")
                or row.get("stale_graveyard_entry")
                or row.get("resurrection_conflict")
            ):
                continue

            print(f"\n{row.get('concept')}")
            print(f"  truth_state: {row.get('truth_state')}")
            print(f"  graveyard_state: {row.get('graveyard_state')}")
            print(f"  source_of_truth: {row.get('source_of_truth')}")
            print(f"  last_update_cycle: {row.get('last_update_cycle')}")

    def _print_list(self, values: Optional[List[str]]) -> None:
        if not values:
            print("  - none")
            return

        for value in values:
            print(f"  - {value}")
