import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.patch_analyzer import PatchAnalyzer, GitInspector, PatchAnalyzerError


class TestPatchAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = PatchAnalyzer()
        self.rand_str = uuid.uuid4().hex
        self.rand_filename = f"{self.rand_str}.py"
        self.rand_commit = uuid.uuid4().hex

    def test_patch_analyzer_error_inheritance(self):
        self.assertTrue(issubclass(PatchAnalyzerError, Exception))

    def test_git_inspector_success(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        inspector = GitInspector(repo_path)
        expected_output = f"diff --git a/{self.rand_filename} b/{self.rand_filename}\n..."
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = expected_output
            result = inspector.get_file_diff(self.rand_commit)
            self.assertEqual(result, expected_output)
            mock_run.assert_called_once()

    def test_git_inspector_failure(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        inspector = GitInspector(repo_path)

        with patch("subprocess.run", side_effect=Exception(self.rand_str)):
            with self.assertRaises(PatchAnalyzerError) as ctx:
                inspector.get_file_diff(self.rand_commit)
            self.assertIn(self.rand_str, str(ctx.exception))

    def test_parse_invalid_type(self):
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.parse(random.randint(1, 100))

    def test_parse_empty_diff(self):
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.parse("")
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.parse("   \n  ")

    def test_parse_valid_diff(self):
        diff_text = f"--- a/{self.rand_filename}\n+++ b/{self.rand_filename}\n@@ -1,1 +1,1__\n-old line {self.rand_str}\n+new line {self.rand_str}"
        # Заменим заголовок ханка на валидный
        diff_text = f"--- a/{self.rand_filename}\n+++ b/{self.rand_filename}\n@@ -1,1 +1,1 @@\n-old line {self.rand_str}\n+new line {self.rand_str}"

        result = self.analyzer.parse(diff_text)
        self.assertIn("files", result)
        self.assertEqual(len(result["files"]), 1)
        self.assertEqual(result["files"][0]["target_file"], self.rand_filename)
        self.assertEqual(len(result["files"][0]["chunks"]), 1)
        self.assertEqual(result["files"][0]["chunks"][0]["old_count"], 1)
        self.assertEqual(result["files"][0]["chunks"][0]["new_count"], 1)

    def test_validate_structure_mismatch(self):
        diff_text = f"--- a/{self.rand_filename}\n+++ b/{self.rand_filename}\n@@ -1,5 +1,1 @@\n-old line 1\n-old line 2\n+new line 1"
        with self.assertRaises(PatchAnalyzerError) as ctx:
            self.analyzer.validate_structure(diff_text)
        self.assertIn("Hunk line count mismatch", str(ctx.exception))

    def test_validate_structure_corrupted_header(self):
        diff_text = f"--- a/{self.rand_filename}\n+++ b/{self.rand_filename}\n@@ invalid header @@\n-old\n+new"
        with self.assertRaises(PatchAnalyzerError) as ctx:
            self.analyzer.validate_structure(diff_text)
        self.assertIn("Corrupted hunk header", str(ctx.exception))

    def test_get_statistics(self):
        diff_text = f"--- a/{self.rand_filename}\n+++ b/{self.rand_filename}\n@@ -1,1 +1,2 @@\n-line\n+line1\n+line2"
        stats = self.analyzer.get_statistics(diff_text)
        self.assertEqual(stats["files_changed"], 1)
        self.assertEqual(stats["additions"], 2)
        self.assertEqual(stats["deletions"], 1)
        self.assertEqual(stats["total_changes"], 3)

    def test_get_statistics_invalid_type(self):
        stats = self.analyzer.get_statistics(None)
        self.assertEqual(stats["files_changed"], 0)
        self.assertEqual(stats["additions"], 0)

    def test_detect_syntax_risks(self):
        conflict_marker = "<<<<<<< HEAD"
        dangerous_func = f"os.system('{self.rand_str}')"
        unbalanced = f"foo = bar({self.rand_str}"

        diff_text = f"--- a/{self.rand_filename}\n+++ b/{self.rand_filename}\n@@ -1,3 +1,3 @@\n+{conflict_marker}\n+{dangerous_func}\n+{unbalanced}"

        risks = self.analyzer.detect_syntax_risks(diff_text)
        risk_types = [r["type"] for r in risks]

        self.assertIn("merge_conflict_marker", risk_types)
        self.assertIn("dangerous_call", risk_types)
        self.assertIn("unbalanced_delimiter", risk_types)

    def test_detect_syntax_risks_invalid_type(self):
        risks = self.analyzer.detect_syntax_risks(12345)
        self.assertEqual(risks, [])

    def test_analyze_success(self):
        diff_text = f"--- a/{self.rand_filename}\n+++ b/{self.rand_filename}\n@@ -1,1 +1,1 @@\n-old\n+print('{self.rand_str}')"
        result = self.analyzer.analyze(diff_text)
        
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["files"], [self.rand_filename])
        self.assertEqual(result["additions"], 1)
        self.assertEqual(result["deletions"], 1)
        self.assertIn(self.rand_filename, str(result["parsed"]))

    def test_analyze_failure(self):
        result = self.analyzer.analyze("")
        self.assertFalse(result["is_valid"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_analyze_stream(self):
        diff_text = f"--- a/{self.rand_filename}\n+++ b/{self.rand_filename}\n@@ -1,1 +1,1 @@\n-old\n+new {self.rand_str}"
        stream = io.StringIO(diff_text)
        result = self.analyzer.analyze_stream(stream)
        self.assertTrue(result["is_valid"])
        self.assertIn(self.rand_filename, result["files"])

    def test_analyze_file(self):
        diff_text = f"--- a/{self.rand_filename}\n+++ b/{self.rand_filename}\n@@ -1,1 +1,1 @@\n-old\n+new {self.rand_str}"
        mock_open_data = unittest.mock.mock_open(read_data=diff_text)
        with patch("builtins.open", mock_open_data):
            result = self.analyzer.analyze_file(f"/path/to/{uuid.uuid4().hex}.patch")
            self.assertTrue(result["is_valid"])
            self.assertEqual(result["files"], [self.rand_filename])