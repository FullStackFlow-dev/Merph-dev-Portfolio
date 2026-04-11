"""
Tests for the Python report-generation logic embedded in the 'report' job
of .github/workflows/ci-cd.yml.

The script was changed in this PR to:
- Use "notebooks" instead of "notes" in the dirs list
- Set project name to "MerphDev" (was "MerphDev Learning and Certifications")
- Add os.makedirs("docs", exist_ok=True) before writing the JSON file
- Simplify print output to "Report generated"
"""

import json
import os
import sys
import importlib.util
import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, mock_open


# ---------------------------------------------------------------------------
# Helper: reproduce the exact script logic from the workflow inline script
# ---------------------------------------------------------------------------

def run_report_script(base_dir: str) -> dict:
    """
    Replicates the logic of the inline Python script in the workflow's
    'Generate report' step, running inside *base_dir* so that directory
    existence checks work correctly.
    """
    import os as _os
    import json as _json

    original_cwd = _os.getcwd()
    _os.chdir(base_dir)
    try:
        report = {
            "generated_at": datetime.now().isoformat(),
            "project": "MerphDev",
            "statistics": {},
        }

        dirs = [
            "learning-paths",
            "certifications",
            "notebooks",
            "models",
            "docs",
        ]

        for d in dirs:
            if _os.path.exists(d):
                md_files = [f for f in _os.listdir(d) if f.endswith(".md")]
                report["statistics"][d] = len(md_files)

        _os.makedirs("docs", exist_ok=True)

        with open("docs/latest-report.json", "w") as f:
            _json.dump(report, f, indent=2)

        return report
    finally:
        _os.chdir(original_cwd)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmpproject(tmp_path):
    """Return a temporary directory that mimics the project layout."""
    return tmp_path


# ---------------------------------------------------------------------------
# Tests: project name
# ---------------------------------------------------------------------------

class TestProjectName:
    """The project field must be exactly 'MerphDev' after the PR change."""

    def test_project_name_is_merphdev(self, tmpproject):
        report = run_report_script(str(tmpproject))
        assert report["project"] == "MerphDev"

    def test_project_name_not_old_value(self, tmpproject):
        """Regression: ensure the old verbose name was dropped."""
        report = run_report_script(str(tmpproject))
        assert report["project"] != "MerphDev Learning and Certifications"


# ---------------------------------------------------------------------------
# Tests: dirs list uses "notebooks" not "notes"
# ---------------------------------------------------------------------------

class TestDirectoryList:
    """The scanned dirs must include 'notebooks' and must NOT include 'notes'."""

    def test_notebooks_directory_is_scanned(self, tmpproject):
        (tmpproject / "notebooks").mkdir()
        (tmpproject / "notebooks" / "intro.md").write_text("# intro")
        report = run_report_script(str(tmpproject))
        assert "notebooks" in report["statistics"]

    def test_notes_directory_is_not_scanned(self, tmpproject):
        # Even if a 'notes' dir exists it must NOT appear in statistics.
        (tmpproject / "notes").mkdir()
        (tmpproject / "notes" / "anything.md").write_text("# note")
        report = run_report_script(str(tmpproject))
        assert "notes" not in report["statistics"]

    def test_all_expected_dirs_in_scan_list(self, tmpproject):
        expected = {"learning-paths", "certifications", "notebooks", "models", "docs"}
        for d in expected:
            (tmpproject / d).mkdir()
        report = run_report_script(str(tmpproject))
        assert set(report["statistics"].keys()) == expected

    def test_missing_directories_are_excluded_from_statistics(self, tmpproject):
        # Only create a subset of dirs; missing ones must not appear at all.
        (tmpproject / "notebooks").mkdir()
        (tmpproject / "notebooks" / "nb.md").write_text("# nb")
        report = run_report_script(str(tmpproject))
        for absent in ("learning-paths", "certifications", "models"):
            assert absent not in report["statistics"]


# ---------------------------------------------------------------------------
# Tests: os.makedirs("docs", exist_ok=True)
# ---------------------------------------------------------------------------

class TestDocsMakedirs:
    """The script must create docs/ automatically when it does not exist."""

    def test_docs_dir_created_when_missing(self, tmpproject):
        assert not (tmpproject / "docs").exists()
        run_report_script(str(tmpproject))
        assert (tmpproject / "docs").is_dir()

    def test_docs_dir_creation_is_idempotent(self, tmpproject):
        """exist_ok=True means calling makedirs twice must not raise."""
        (tmpproject / "docs").mkdir()
        # Should not raise even though docs/ already exists.
        run_report_script(str(tmpproject))
        assert (tmpproject / "docs").is_dir()


# ---------------------------------------------------------------------------
# Tests: JSON output file
# ---------------------------------------------------------------------------

class TestOutputFile:
    """The report must be written to docs/latest-report.json."""

    def test_report_file_is_created(self, tmpproject):
        run_report_script(str(tmpproject))
        assert (tmpproject / "docs" / "latest-report.json").exists()

    def test_report_file_is_valid_json(self, tmpproject):
        run_report_script(str(tmpproject))
        content = (tmpproject / "docs" / "latest-report.json").read_text()
        parsed = json.loads(content)
        assert isinstance(parsed, dict)

    def test_report_has_required_top_level_keys(self, tmpproject):
        run_report_script(str(tmpproject))
        data = json.loads((tmpproject / "docs" / "latest-report.json").read_text())
        assert "generated_at" in data
        assert "project" in data
        assert "statistics" in data

    def test_report_generated_at_is_iso_format(self, tmpproject):
        run_report_script(str(tmpproject))
        data = json.loads((tmpproject / "docs" / "latest-report.json").read_text())
        # Must be parseable as a datetime
        datetime.fromisoformat(data["generated_at"])

    def test_report_statistics_counts_only_md_files(self, tmpproject):
        nb = tmpproject / "notebooks"
        nb.mkdir()
        (nb / "one.md").write_text("# one")
        (nb / "two.md").write_text("# two")
        (nb / "ignore.txt").write_text("not md")
        (nb / "ignore.py").write_text("# python")
        report = run_report_script(str(tmpproject))
        assert report["statistics"]["notebooks"] == 2

    def test_report_statistics_empty_directory_yields_zero(self, tmpproject):
        (tmpproject / "models").mkdir()
        report = run_report_script(str(tmpproject))
        assert report["statistics"]["models"] == 0

    def test_report_statistics_multiple_dirs(self, tmpproject):
        for d, count in [("learning-paths", 3), ("certifications", 1), ("notebooks", 2)]:
            dpath = tmpproject / d
            dpath.mkdir()
            for i in range(count):
                (dpath / f"file{i}.md").write_text(f"# {i}")
        report = run_report_script(str(tmpproject))
        assert report["statistics"]["learning-paths"] == 3
        assert report["statistics"]["certifications"] == 1
        assert report["statistics"]["notebooks"] == 2

    def test_report_json_is_indented(self, tmpproject):
        """The JSON must be pretty-printed (indent=2) for readability."""
        run_report_script(str(tmpproject))
        raw = (tmpproject / "docs" / "latest-report.json").read_text()
        # Pretty-printed JSON contains newlines
        assert "\n" in raw