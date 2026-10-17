import io
import os
import random
import string
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from skills.patch_analyzer import GitInspector, PatchAnalyzer, PatchAnalyzerError


class TestPatchAnalyzerInquisition(unittest.TestCase):
    def setUp(self):
        self.analyzer = PatchAnalyzer()

    def _generate_random_string(self, length=8):
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def _generate_random_filename(self, ext=".py"):
        return f"{self._generate_random_string(10)}{ext}"

    def _build_valid_diff(self, file_path, added_lines=None, deleted_lines=None, context_lines=None):
        if added_lines is None:
            added_lines = []
        if deleted_lines is None:
            deleted_lines = []
        if context_lines is None:
            context_lines = []

        old_count = len(deleted_lines) + len(context_lines)
        new_count = len(added_lines) + len(context_lines)

        diff_lines = [
            f"--- a/{file_path}",
            f"+++ b/{file_path}",
            f"@@ -1,{old_count} +1,{new_count} @@",
        ]
        for ctx in context_lines:
            diff_lines.append(f" {ctx}")
        for d in deleted_lines:
            diff_lines.append(f"-{d}")
        for a in added_lines:
            diff_lines.append(f"+{a}")

        return "\n".join(diff_lines)

    def test_git_inspector_success(self):
        random_repo = f"/tmp/{self._generate_random_string(12)}"
        random_hash = self._generate_random_string(40)
        random_output = f"commit {random_hash}\n--- a/{self._generate_random_filename()}\n"

        inspector = GitInspector(random_repo)
        self.assertEqual(inspector.repo_dir, random_repo)

        mock_result = MagicMock()
        mock_result.stdout = random_output

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            diff = inspector.get_file_diff(random_hash)
            self.assertEqual(diff, random_output)
            mock_run.assert_called_once_with(
                ["git", "show", "--unified=3", random_hash],
                cwd=random_repo,
                capture_output=True,
                text=True,
                check=True,
            )

    def test_git_inspector_failure_raises_patch_analyzer_error(self):
        random_repo = f"/tmp/{self._generate_random_string(8)}"
        random_hash = self._generate_random_string(32)
        inspector = GitInspector(random_repo)

        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
            with self.assertRaises(PatchAnalyzerError) as ctx:
                inspector.get_file_diff(random_hash)
            self.assertIn("Failed to get git diff", str(ctx.exception))

    def test_parse_invalid_types_and_empty(self):
        invalid_inputs = [None, 12345, [], {}, 3.14]
        for item in invalid_inputs:
            with self.assertRaises(PatchAnalyzerError):
                self.analyzer.parse(item)

        whitespaces = ["", "   ", "\n\t\n  "]
        for ws in whitespaces:
            with self.assertRaises(PatchAnalyzerError):
                self.analyzer.parse(ws)

    def test_validate_structure_invalid_diffs(self):
        garbage = f"random garbage {self._generate_random_string(30)}"
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.validate_structure(garbage)

        file_name = self._generate_random_filename()
        corrupted_header = f"--- a/{file_name}\n+++ b/{file_name}\n@@ BAD_HUNK @@\n+line"
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.validate_structure(corrupted_header)

        mismatch_hunk = f"--- a/{file_name}\n+++ b/{file_name}\n@@ -1,5 +1,5 @@\n+line1\n-line2"
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.validate_structure(mismatch_hunk)

    def test_parse_valid_single_file_chunks(self):
        filename = self._generate_random_filename()
        token_add = self._generate_random_string(16)
        token_del = self._generate_random_string(16)
        token_ctx = self._generate_random_string(16)

        diff = self._build_valid_diff(
            filename,
            added_lines=[token_add],
            deleted_lines=[token_del],
            context_lines=[token_ctx],
        )

        parsed = self.analyzer.parse(diff)
        self.assertIn("files", parsed)
        self.assertEqual(len(parsed["files"]), 1)
        file_obj = parsed["files"][0]
        self.assertEqual(file_obj["target_file"], filename)
        self.assertEqual(len(file_obj["chunks"]), 1)
        chunk = file_obj["chunks"][0]
        self.assertEqual(chunk["old_count"], 1)
        self.assertEqual(chunk["new_count"], 1)

    def test_get_statistics_calculation(self):
        file1 = self._generate_random_filename()
        file2 = self._generate_random_filename()

        adds1 = [self._generate_random_string(10) for _ in range(3)]
        dels1 = [self._generate_random_string(10) for _ in range(2)]
        diff1 = self._build_valid_diff(file1, added_lines=adds1, deleted_lines=dels1)

        adds2 = [self._generate_random_string(10) for _ in range(4)]
        dels2 = [self._generate_random_string(10) for _ in range(1)]
        diff2 = self._build_valid_diff(file2, added_lines=adds2, deleted_lines=dels2)

        combined_diff = diff1 + "\n" + diff2
        stats = self.analyzer.get_statistics(combined_diff)

        self.assertEqual(stats["files_changed"], 2)
        self.assertEqual(stats["additions"], 7)
        self.assertEqual(stats["deletions"], 3)
        self.assertEqual(stats["total_changes"], 10)

    def test_get_statistics_invalid_type(self):
        stats = self.analyzer.get_statistics(None)
        self.assertEqual(stats["files_changed"], 0)
        self.assertEqual(stats["additions"], 0)
        self.assertEqual(stats["deletions"], 0)
        self.assertEqual(stats["total_changes"], 0)

    def test_detect_syntax_risks_eval_exec_os_system(self):
        file_path = self._generate_random_filename()
        danger_var = self._generate_random_string(6)
        lines = [
            f"import os",
            f"eval('{danger_var}')",
            f"exec('{danger_var}')",
            f"os.system('{danger_var}')",
        ]
        diff = self._build_valid_diff(file_path, added_lines=lines)

        risks = self.analyzer.detect_syntax_risks(diff)
        danger_types = [r["type"] for r in risks if r["type"] == "dangerous_call"]
        self.assertEqual(len(danger_types), 3)

    def test_detect_syntax_risks_merge_conflicts(self):
        file_path = self._generate_random_filename()
        branch_a = self._generate_random_string(6)
        branch_b = self._generate_random_string(6)
        conflict_lines = [
            f"<<<<<<< {branch_a}",
            f"print('{branch_a}')",
            f"=======",
            f"print('{branch_b}')",
            f">>>>>>> {branch_b}",
        ]
        diff = self._build_valid_diff(file_path, added_lines=conflict_lines)

        risks = self.analyzer.detect_syntax_risks(diff)
        conflict_risks = [r for r in risks if r["type"] == "merge_conflict_marker"]
        self.assertEqual(len(conflict_risks), 3)

    def test_detect_syntax_risks_unbalanced_delimiters(self):
        file_path = self._generate_random_filename()
        var_name = self._generate_random_string(5)
        unbalanced_lines = [
            f"{var_name} = [1, 2,",
            f"func_call(",
            f"val = {'{'}",
        ]
        diff = self._build_valid_diff(file_path, added_lines=unbalanced_lines)

        risks = self.analyzer.detect_syntax_risks(diff)
        delimiter_risks = [r for r in risks if r["type"] == "unbalanced_delimiter"]
        self.assertEqual(len(delimiter_risks), 2)

    def test_detect_syntax_risks_invalid_input(self):
        self.assertEqual(self.analyzer.detect_syntax_risks(None), [])
        self.assertEqual(self.analyzer.detect_syntax_risks(1234), [])

    def test_analyze_full_pipeline_valid(self):
        file_path = self._generate_random_filename()
        payload = self._generate_random_string(12)
        diff = self._build_valid_diff(file_path, added_lines=[f"x = '{payload}'"])

        result = self.analyzer.analyze(diff)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["files"], [file_path])
        self.assertEqual(result["additions"], 1)
        self.assertEqual(result["deletions"], 0)
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["chunks"]), 1)

    def test_analyze_full_pipeline_invalid(self):
        corrupted_diff = f"{self._generate_random_string(30)}\n{self._generate_random_string(30)}"
        result = self.analyzer.analyze(corrupted_diff)
        self.assertFalse(result["is_valid"])
        self.assertGreater(len(result["errors"]), 0)
        self.assertEqual(result["statistics"]["total_changes"], 0)

    def test_analyze_stream(self):
        file_path = self._generate_random_filename()
        secret = self._generate_random_string(14)
        diff = self._build_valid_diff(file_path, added_lines=[secret])

        stream = io.StringIO(diff)
        result = self.analyzer.analyze_stream(stream)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["files"], [file_path])
        self.assertEqual(result["additions"], 1)

    def test_analyze_file(self):
        file_path = self._generate_random_filename()
        secret = self._generate_random_string(14)
        diff = self._build_valid_diff(file_path, added_lines=[secret])

        temp_dir = tempfile.mkdtemp()
        temp_patch_path = os.path.join(temp_dir, f"{self._generate_random_string(8)}.patch")
        try:
            with open(temp_patch_path, "w", encoding="utf-8") as f:
                f.write(diff)

            result = self.analyzer.analyze_file(temp_patch_path)
            self.assertTrue(result["is_valid"])
            self.assertEqual(result["files"], [file_path])
            self.assertEqual(result["additions"], 1)
        finally:
            if os.path.exists(temp_patch_path):
                os.remove(temp_patch_path)
            os.rmdir(temp_dir)


if __name__ == "__main__":
    unittest.main()