import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
from skills.patch_analyzer import PatchAnalyzer, GitInspector, PatchAnalyzerError


class TestPatchAnalyzerInquisition(unittest.TestCase):

    def setUp(self):
        self.analyzer = PatchAnalyzer()
        self.random_repo_dir = f"/tmp/{uuid.uuid4().hex}"
        self.inspector = GitInspector(repo_dir=self.random_repo_dir)

    def test_git_inspector_success(self):
        commit = uuid.uuid4().hex
        expected_output = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n--- a/file\n+++ b/file\n@@ -1,1 +1,1K@@\n-old\n+new"
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=expected_output)
            result = self.inspector.get_file_diff(commit)
            self.assertEqual(result, expected_output)
            mock_run.assert_called_once()

    def test_git_inspector_error(self):
        commit = uuid.uuid4().hex
        with patch("subprocess.run", side_effect=Exception("git error")):
            with self.assertRaises(PatchAnalyzerError):
                self.inspector.get_file_diff(commit)

    def test_patch_analyzer_invalid_type(self):
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.parse(12345)

    def test_patch_analyzer_empty_string(self):
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.parse("   ")

    def test_patch_analyzer_valid_diff(self):
        file_name = f"{uuid.uuid4().hex}.py"
        diff_content = f"--- a/{file_name}\n+++ b/{file_name}\n@@ -1,1 +1,1 @@\n-old_line_{uuid.uuid4().hex}\n+new_line_{uuid.uuid4().hex}\n"

        result = self.analyzer.analyze(diff_content)
        self.assertTrue(result["is_valid"])
        self.assertIn(file_name, result["files"])
        self.assertEqual(result["additions"], 1)
        self.assertEqual(result["deletions"], 1)

    def test_patch_analyzer_syntax_risks(self):
        conflict_marker = f"<<<<<<< {uuid.uuid4().hex}"
        dangerous_func = f"eval('{uuid.uuid4().hex}')"
        diff_content = f"--- a/risk.py\n+++ b/risk.py\n@@ -1,1 +1,2 @@\n+{conflict_marker}\n+{dangerous_func}\n"

        risks = self.analyzer.detect_syntax_risks(diff_content)
        self.assertGreaterEqual(len(risks), 2)
        risk_types = [r["type"] for r in risks]
        self.assertIn("merge_conflict_marker", risk_types)
        self.assertIn("dangerous_call", risk_types)

    def test_patch_analyzer_analyze_stream(self):
        file_name = f"{uuid.uuid4().hex}.py"
        content = f"--- a/{file_name}\n+++ b/{file_name}\n@@ -1,1 +1,1 @@\n-line1\n+line2\n"
        stream = io.StringIO(content)

        result = self.analyzer.analyze_stream(stream)
        self.assertTrue(result["is_valid"])
        self.assertIn(file_name, result["files"])

    def test_patch_analyzer_statistics(self):
        diff_content = "--- a/a.py\n+++ b/a.py\n@@ -1,3 +1,3 @@\n-del1\n-del2\n+add1\n+add2\n+add3\n"
        stats = self.analyzer.get_statistics(diff_content)
        self.assertEqual(stats["files_changed"], 1)
        self.assertEqual(stats["additions"], 3)
        self.assertEqual(stats["deletions"], 2)
        self.assertEqual(stats["total_changes"], 5)

    def test_patch_analyzer_invalid_structure_mismatch(self):
        diff_content = "--- a/a.py\n+++ b/a.py\n@@ -1,5 +1,1 @@\n-line1\n+line2\n"
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.validate_structure(diff_content)

    def test_patch_analyzer_corrupted_hunk_header(self):
        diff_content = "--- a/a.py\n+++ b/a.py\n@@ INVALID_HEADER @@\n-line1\n+line2\n"
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.validate_structure(diff_content)


if __name__ == "__main__":
    unittest.main()