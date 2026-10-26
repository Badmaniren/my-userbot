import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.patch_analyzer import PatchAnalyzer, GitInspector, PatchAnalyzerError


class TestPatchAnalyzerInquisitor(unittest.TestCase):

    def setUp(self):
        self.analyzer = PatchAnalyzer()
        self.random_prefix = uuid.uuid4().hex[:8]
        self.file_name = f"{self.random_prefix}_module.py"
        self.commit_hash = uuid.uuid4().hex
        self.repo_dir = f"/tmp/{uuid.uuid4().hex}"

    def test_patch_analyzer_error_hierarchy(self):
        exc = PatchAnalyzerError(f"Error {self.random_prefix}")
        self.assertIsInstance(exc, Exception)

    def test_git_inspector_success(self):
        inspector = GitInspector(self.repo_dir)
        expected_output = f"diff --git a/{self.file_name} b/{self.file_name}\n--- a/{self.file_name}\n+++ b/{self.file_name}\n@@ -1,1 +1,1 B\n-{self.random_prefix}\n+{self.random_prefix}_new"

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = expected_output
            mock_run.return_value = mock_result

            result = inspector.get_file_diff(self.commit_hash)
            self.assertEqual(result, expected_output)
            mock_run.assert_called_once_with(
                ["git", "show", "--unified=3", self.commit_hash],
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                check=True
            )

    def test_git_inspector_failure(self):
        inspector = GitInspector(self.repo_dir)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception(f"Git crash {self.random_prefix}")

            with self.assertRaises(PatchAnalyzerError) as ctx:
                inspector.get_file_diff(self.commit_hash)
            self.assertIn(self.random_prefix, str(ctx.exception))

    def test_parse_valid_diff(self):
        diff = f"""--- a/{self.file_name}
+++ b/{self.file_name}
@@ -1,1 +1,1 @@
-{self.random_prefix}_old
+{self.random_prefix}_new
"""
        parsed = self.analyzer.parse(diff)
        self.assertIn("files", parsed)
        self.assertEqual(len(parsed["files"]), 1)
        self.assertEqual(parsed["files"][0]["target_file"], self.file_name)
        self.assertEqual(len(parsed["files"][0]["chunks"]), 1)

    def test_parse_invalid_type(self):
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.parse(12345)

    def test_parse_empty_diff(self):
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.parse("   \n   ")

    def test_validate_structure_valid(self):
        diff = f"""--- a/{self.file_name}
+++ b/{self.file_name}
@@ -1,1 +1,1 @@
-{self.random_prefix}_line1
+{self.random_prefix}_line2
"""
        # Should not raise
        self.analyzer.validate_structure(diff)

    def test_validate_structure_corrupted_hunk(self):
        diff = f"""--- a/{self.file_name}
+++ b/{self.file_name}
@@ invalid_header @@
-{self.random_prefix}
+{self.random_prefix}
"""
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.validate_structure(diff)

    def test_validate_structure_mismatch(self):
        diff = f"""--- a/{self.file_name}
+++ b/{self.file_name}
@@ -1,5 +1,1 @@
-{self.random_prefix}_1
-{self.random_prefix}_2
+{self.random_prefix}_new
"""
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.validate_structure(diff)

    def test_get_statistics(self):
        diff = f"""--- a/{self.file_name}
+++ b/{self.file_name}
@@ -1,2 +1,3 @@
-{self.random_prefix}_del1
+{self.random_prefix}_add1
+{self.random_prefix}_add2
"""
        stats = self.analyzer.get_statistics(diff)
        self.assertEqual(stats["files_changed"], 1)
        self.assertEqual(stats["additions"], 2)
        self.assertEqual(stats["deletions"], 1)
        self.assertEqual(stats["total_changes"], 3)

    def test_get_statistics_invalid_type(self):
        stats = self.analyzer.get_statistics(None)
        self.assertEqual(stats["files_changed"], 0)
        self.assertEqual(stats["additions"], 0)

    def test_detect_syntax_risks_merge_conflict(self):
        marker = random.choice(["<<<<<<<", "=======", ">>>>>>>"])
        diff = f"""--- a/{self.file_name}
+++ b/{self.file_name}
@@ -1,1 +1,1 @@
-{self.random_prefix}
+{marker} {self.random_prefix}
"""
        risks = self.analyzer.detect_syntax_risks(diff)
        self.assertTrue(any(r["type"] == "merge_conflict_marker" for r in risks))

    def test_detect_syntax_risks_dangerous_call(self):
        call = random.choice(["eval", "exec", "os.system"])
        diff = f"""--- a/{self.file_name}
+++ b/{self.file_name}
@@ -1,1 +1,1 @@
-{self.random_prefix}
+{call}("{self.random_prefix}")
"""
        risks = self.analyzer.detect_syntax_risks(diff)
        self.assertTrue(any(r["type"] == "dangerous_call" for r in risks))

    def test_detect_syntax_risks_unbalanced_delimiter(self):
        diff = f"""--- a/{self.file_name}
+++ b/{self.file_name}
@@ -1,1 +1,1 @@
-{self.random_prefix}
+{self.random_prefix}(
"""
        risks = self.analyzer.detect_syntax_risks(diff)
        self.assertTrue(any(r["type"] == "unbalanced_delimiter" for r in risks))

    def test_detect_syntax_risks_invalid_type(self):
        risks = self.analyzer.detect_syntax_risks(12345)
        self.assertEqual(risks, [])

    def test_analyze_success(self):
        diff = f"""--- a/{self.file_name}
+++ b/{self.file_name}
@@ -1,1 +1,1 @@
-{self.random_prefix}_old
+{self.random_prefix}_new
"""
        result = self.analyzer.analyze(diff)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["files"], [self.file_name])
        self.assertEqual(result["additions"], 1)
        self.assertEqual(result["deletions"], 1)
        self.assertEqual(result["errors"], [])

    def test_analyze_failure(self):
        diff = f"INVALID DIFF CONTENT {self.random_prefix}"
        result = self.analyzer.analyze(diff)
        self.assertFalse(result["is_valid"])
        self.assertTrue(len(result["errors"]) > 0)
        self.assertEqual(result["statistics"]["additions"], 0)

    def test_analyze_stream(self):
        diff = f"""--- a/{self.file_name}
+++ b/{self.file_name}
@@ -1,1 +1,1 @@
-{self.random_prefix}_old
+{self.random_prefix}_new
"""
        stream = io.StringIO(diff)
        result = self.analyzer.analyze_stream(stream)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["files"], [self.file_name])

    def test_analyze_file(self):
        diff = f"""--- a/{self.file_name}
+++ b/{self.file_name}
@@ -1,1 +1,1 @@
-{self.random_prefix}_old
+{self.random_prefix}_new
"""
        mock_file_data = io.StringIO(diff)
        with patch("builtins.open", return_value=mock_file_data) as mock_open:
            result = self.analyzer.analyze_file(f"/path/to/{self.file_name}")
            mock_open.assert_called_once()
            self.assertTrue(result["is_valid"])
            self.assertEqual(result["files"], [self.file_name])