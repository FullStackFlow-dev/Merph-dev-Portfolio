"""
Tests for the YAML structure of .github/workflows/ci-cd.yml.

Focuses exclusively on changes introduced in this PR:
- check-links job now has `needs: validate`
- required_files list contains "notebooks/README.md" (not "notes/README.md")
- deploy job requires both validate and report (needs: [validate, report])
- report job requires validate (needs: validate)
- Python inline script dirs list contains "notebooks" not "notes"
- Python inline script project name is "MerphDev"
"""

import re
import pytest
import yaml
from pathlib import Path

WORKFLOW_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "ci-cd.yml"


def _strip_heredocs(text: str) -> str:
    """
    Replace bash heredoc blocks (python3 << 'EOF' ... EOF) with an empty
    quoted string so that PyYAML can parse the surrounding YAML structure
    without tripping over the un-indented Python source lines.
    """
    return re.sub(
        r"python3\s*<<\s*'EOF'.*?^EOF",
        '"<heredoc-stripped>"',
        text,
        flags=re.DOTALL | re.MULTILINE,
    )


@pytest.fixture(scope="module")
def workflow() -> dict:
    raw = WORKFLOW_PATH.read_text()
    sanitised = _strip_heredocs(raw)
    return yaml.safe_load(sanitised)


@pytest.fixture(scope="module")
def workflow_text() -> str:
    return WORKFLOW_PATH.read_text()


# ---------------------------------------------------------------------------
# Tests: check-links job now needs validate
# ---------------------------------------------------------------------------

class TestCheckLinksJobDependency:
    """check-links must declare needs: validate (new in this PR)."""

    def test_check_links_needs_validate(self, workflow):
        job = workflow["jobs"]["check-links"]
        needs = job.get("needs")
        assert needs is not None, "check-links job must have a 'needs' field"
        if isinstance(needs, list):
            assert "validate" in needs
        else:
            assert needs == "validate"

    def test_check_links_needs_is_not_empty(self, workflow):
        job = workflow["jobs"]["check-links"]
        needs = job.get("needs")
        assert needs, "check-links 'needs' must not be empty"


# ---------------------------------------------------------------------------
# Tests: validate job — required files list
# ---------------------------------------------------------------------------

class TestValidateJobRequiredFiles:
    """The bash script must reference notebooks/README.md, not notes/README.md."""

    def test_notebooks_readme_in_required_files(self, workflow_text):
        assert "notebooks/README.md" in workflow_text, (
            "notebooks/README.md must be listed in required_files"
        )

    def test_notes_readme_not_in_required_files(self, workflow_text):
        # notes/README.md must NOT appear anywhere in the workflow
        assert "notes/README.md" not in workflow_text, (
            "notes/README.md must not appear in the workflow (renamed to notebooks)"
        )

    def test_required_files_list_contains_all_expected_paths(self, workflow_text):
        expected_paths = [
            "README.md",
            "learning-paths/cybersecurity.md",
            "learning-paths/ai-ml.md",
            "learning-paths/devops-cloud.md",
            "learning-paths/web-fullstack.md",
            "learning-paths/git-github.md",
            "certifications/README.md",
            "notebooks/README.md",
            "models/README.md",
            "docs/ROADMAP.md",
        ]
        for path in expected_paths:
            assert path in workflow_text, f"Expected path '{path}' not found in workflow"


# ---------------------------------------------------------------------------
# Tests: validate job — messages
# ---------------------------------------------------------------------------

class TestValidateJobMessages:
    """Error and success messages must match the updated text from the PR."""

    def test_error_message_is_validation_failed(self, workflow_text):
        assert "Validation failed" in workflow_text

    def test_error_message_has_no_missing_files_suffix(self, workflow_text):
        assert "Validation failed — missing files" not in workflow_text, (
            "Old error message suffix '— missing files' must be removed"
        )

    def test_success_message_is_structure_ok(self, workflow_text):
        assert "Structure OK" in workflow_text

    def test_success_message_not_old_value(self, workflow_text):
        assert "All structure is valid" not in workflow_text, (
            "Old success message 'All structure is valid' must be replaced by 'Structure OK'"
        )


# ---------------------------------------------------------------------------
# Tests: report job — Python script changes
# ---------------------------------------------------------------------------

class TestReportJobPythonScript:
    """The inline Python script must use 'notebooks' and 'MerphDev'."""

    def test_python_script_uses_notebooks_dir(self, workflow_text):
        # The word "notebooks" must appear in the workflow (as a Python string)
        assert '"notebooks"' in workflow_text or "'notebooks'" in workflow_text, (
            "Python script dirs list must include 'notebooks'"
        )

    def test_python_script_does_not_use_notes_dir(self, workflow_text):
        # "notes" as a standalone Python string must not appear
        assert '"notes"' not in workflow_text and "'notes'" not in workflow_text, (
            "Python script must not reference old 'notes' directory"
        )

    def test_python_script_project_name_is_merphdev(self, workflow_text):
        assert '"MerphDev"' in workflow_text or "'MerphDev'" in workflow_text

    def test_python_script_project_name_not_old_value(self, workflow_text):
        old_name = "MerphDev Learning and Certifications"
        assert old_name not in workflow_text, (
            f"Old project name '{old_name}' must be replaced with 'MerphDev'"
        )

    def test_python_script_uses_makedirs(self, workflow_text):
        assert "os.makedirs" in workflow_text, (
            "Python script must call os.makedirs to ensure docs/ exists"
        )

    def test_python_script_makedirs_uses_exist_ok(self, workflow_text):
        assert "exist_ok=True" in workflow_text, (
            "os.makedirs must use exist_ok=True to be idempotent"
        )

    def test_python_script_writes_to_docs_latest_report_json(self, workflow_text):
        assert "docs/latest-report.json" in workflow_text


# ---------------------------------------------------------------------------
# Tests: report job — dependencies
# ---------------------------------------------------------------------------

class TestReportJobDependency:
    """report job must need validate."""

    def test_report_needs_validate(self, workflow):
        job = workflow["jobs"]["report"]
        needs = job.get("needs")
        assert needs is not None, "report job must have a 'needs' field"
        if isinstance(needs, list):
            assert "validate" in needs
        else:
            assert needs == "validate"


# ---------------------------------------------------------------------------
# Tests: deploy job — dependencies
# ---------------------------------------------------------------------------

class TestDeployJobDependency:
    """deploy must need both validate and report."""

    def test_deploy_needs_validate_and_report(self, workflow):
        job = workflow["jobs"]["deploy"]
        needs = job.get("needs", [])
        if isinstance(needs, str):
            needs = [needs]
        assert "validate" in needs, "deploy must depend on validate"
        assert "report" in needs, "deploy must depend on report"

    def test_deploy_only_runs_on_main(self, workflow):
        job = workflow["jobs"]["deploy"]
        condition = job.get("if", "")
        assert "refs/heads/main" in condition, (
            "deploy job must only run on pushes to main"
        )


# ---------------------------------------------------------------------------
# Tests: workflow trigger configuration
# ---------------------------------------------------------------------------

class TestWorkflowTriggers:
    """The workflow must be triggered on push and pull_request to main, plus a schedule.

    Note: PyYAML (YAML 1.1) parses the bare `on:` key as boolean True, so the
    trigger block is accessed via workflow[True].
    """

    def _triggers(self, workflow: dict) -> dict:
        # PyYAML 1.1 interprets `on` as True; fall back to string key as well.
        return workflow.get(True) or workflow.get("on") or {}

    def test_triggers_on_push_to_main(self, workflow):
        branches = self._triggers(workflow)["push"]["branches"]
        assert "main" in branches

    def test_triggers_on_pull_request_to_main(self, workflow):
        branches = self._triggers(workflow)["pull_request"]["branches"]
        assert "main" in branches

    def test_has_weekly_schedule(self, workflow):
        schedule = self._triggers(workflow)["schedule"]
        assert isinstance(schedule, list) and len(schedule) > 0
        cron = schedule[0]["cron"]
        assert cron == "0 0 * * 1", f"Expected Monday midnight cron, got: {cron}"


# ---------------------------------------------------------------------------
# Tests: overall job structure
# ---------------------------------------------------------------------------

class TestJobStructure:
    """All four jobs must exist with correct names."""

    def test_validate_job_exists(self, workflow):
        assert "validate" in workflow["jobs"]

    def test_check_links_job_exists(self, workflow):
        assert "check-links" in workflow["jobs"]

    def test_report_job_exists(self, workflow):
        assert "report" in workflow["jobs"]

    def test_deploy_job_exists(self, workflow):
        assert "deploy" in workflow["jobs"]

    def test_all_jobs_run_on_ubuntu_latest(self, workflow):
        for job_name, job in workflow["jobs"].items():
            assert job.get("runs-on") == "ubuntu-latest", (
                f"Job '{job_name}' must run on ubuntu-latest"
            )