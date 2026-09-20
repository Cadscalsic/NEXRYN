from pathlib import Path


WORKFLOW = Path(".github/workflows/nexryn-cross-mode-regression.yml")


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def executor_job(text: str) -> str:
    return text.split("  executor-semantic-contract:", 1)[1]


def test_executor_check_has_stable_identity_and_is_unconditional():
    text = workflow_text()
    job = executor_job(text)
    assert "name: Executor Semantic Contract Gate" in job
    assert "if:" not in job
    assert "matrix:" not in job
    assert "needs:" not in job


def test_all_integration_events_create_the_required_check():
    text = workflow_text()
    assert "  pull_request:\n" in text
    assert "  merge_group:\n" in text
    assert "  push:\n" in text
    assert "      - clean-main\n" in text
    assert "      - main\n" in text


def test_no_path_filter_can_bypass_the_check():
    text = workflow_text()
    trigger = text.split("jobs:", 1)[0]
    assert "paths:" not in trigger
    assert "paths-ignore:" not in trigger


def test_executor_job_fails_with_checker_or_test_failure():
    job = executor_job(workflow_text())
    assert "continue-on-error:" not in job
    assert "python tools/executor_contract_ci.py" in job
    assert "tests/test_executor_contract_ci.py" in job
    assert "tests/test_candidate_semantic_equivalence.py" in job


def test_workflow_uses_minimal_permissions_and_bounded_runtime():
    text = workflow_text()
    job = executor_job(text)
    assert "permissions:\n  contents: read" in text
    assert "timeout-minutes: 15" in job
