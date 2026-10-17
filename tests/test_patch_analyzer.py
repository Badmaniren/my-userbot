import io
import os
import random
import string
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from skills.patch_analyzer import (
    GitInspector,
    PatchAnalyzer,
    PatchAnalyzerError,
)


class TestPatchAnalyzerExhaustive(unittest.TestCase):
    def setUp(self):
        self.analyzer = PatchAnalyzer()

    def _generate_random_word(self, min_len=5, max_len=12):
        chars = string.ascii_letters + string.digits
        length = random.randint(min_len, max_len)
        return "".join(random.choices(chars, k=length))

    def _generate_random_filepath(self):
        folder = self._generate_random_word(4, 8)
        filename = self._generate_random_word(6, 12)
        ext = random.choice([".py", ".txt", ".json", ".md", ".cpp"])
        return f"{folder}/{filename}{ext}"

    def _create_valid_diff(self, file_path, old_lines, new_lines, context_before=None, context_after=None):
        if context_before is None:
            context_before = [f" context_pre_{self._generate_random_word()}" for _ in range(random.randint(1, 2))]
        if context_after is None:
            context_after = [f" context_post_{self._generate_random_word()}" for _ in range(random.randint(1, 2))]

        diff_lines = [
            f"--- a/{file_path}",
            f"+++ b/{file_path}",
        ]

        old_count = len(context_before) + len(old_lines) + len(context_after)
        new_count = len(context_before) + len(new_lines) + len(context_after)

        old_start = random.randint(1, 100)
        new_start = random.randint(1, 100)

        header = f"@@ -{old_start},{old_count} +{new_start},{new_count} @@"
        diff_lines.append(header)

        for line in context_before:
            diff_lines.append(line if line.startswith(" ") else f" {line}")
        for line in old_lines:
            diff_lines.append(line if line.startswith("-") else f"-{line}")
        for line in new_lines:
            diff_lines.append(line if line.startswith("+") else f"+{line}")
        for line in context_after:
            diff_lines.append(line if line.startswith(" ") else f" {line}")

        return "\n".join(diff_lines)

    def test_git_inspector_success(self):
        repo_dir = f"/tmp/repo_{self._generate_random_word()}"
        commit_hash = "".join(random.choices("0123456789abcdef", k=40))
        expected_output = f"diff --git a/test b/test\n+{self._generate_random_word()}"

        inspector = GitInspector(repo_dir=repo_dir)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=expected_output)
            output = inspector.get_file_diff(commit_hash)

            mock_run.assert_called_once_with(
                ["git", "show", "--unified=3", commit_hash],
                cwd=repo_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(output, expected_output)

    def test_git_inspector_failure(self):
        repo_dir = f"/tmp/repo_{self._generate_random_word()}"
        commit_hash = "".join(random.choices("0123456789abcdef", k=40))

        inspector = GitInspector(repo_dir=repo_dir)

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=128, cmd="git show", stderr=b"fatal: bad object"
            )
            with self.assertRaises(PatchAnalyzerError) as ctx:
                inspector.get_file_diff(commit_hash)
            self.assertIn("Failed to get git diff", str(ctx.exception))

    def test_validate_structure_invalid_types_and_empty(self):
        non_strings = [None, 1234, [], {}, 3.14]
        for val in non_strings:
            with self.assertRaises(PatchAnalyzerError):
                self.analyzer.validate_structure(val)

        whitespace_only = ["", "   ", "\t\t\n", "\r\n"]
        for ws in whitespace_only:
            with self.assertRaises(PatchAnalyzerError):
                self.analyzer.validate_structure(ws)

    def test_validate_structure_corrupted_hunk_header(self):
        corrupted_header = f"@@ invalid_range +1,2 @@\n+{self._generate_random_word()}"
        with self.assertRaises(PatchAnalyzerError) as ctx:
            self.analyzer.validate_structure(corrupted_header)
        self.assertIn("Corrupted hunk header", str(ctx.exception))

    def test_validate_structure_hunk_count_mismatch(self):
        file_path = self._generate_random_filepath()
        # Declares 2 lines for old and 2 lines for new, but we provide 1 and 1
        diff_text = (
            f"--- a/{file_path}\n"
            f"+++ b/{file_path}\n"
            f"@@ -1,2 +1,2 @@\n"
            f"-{self._generate_random_word()}\n"
            f"+{self._generate_random_word()}\n"
        )
        with self.assertRaises(PatchAnalyzerError) as ctx:
            self.analyzer.validate_structure(diff_text)
        self.assertIn("Hunk line count mismatch", str(ctx.exception))

    def test_parse_valid_single_file_patch(self):
        path = self._generate_random_filepath()
        del_line = f"del_{self._generate_random_word()}"
        add_line_1 = f"add_{self._generate_random_word()}"
        add_line_2 = f"add_{self._generate_random_word()}"

        diff = self._create_valid_diff(
            file_path=path,
            old_lines=[del_line],
            new_lines=[add_line_1, add_line_2],
            context_before=[" ctx_pre"],
            context_after=[" ctx_post"],
        )

        result = self.analyzer.parse(diff)
        self.assertIn("files", result)
        self.assertEqual(len(result["files"]), 1)

        file_data = result["files"][0]
        self.assertEqual(file_data["target_file"], path)
        self.assertEqual(len(file_data["chunks"]), 1)

        chunk = file_data["chunks"][0]
        self.assertEqual(chunk["old_count"], 1)
        self.assertEqual(chunk["new_count"], 2)

    def test_parse_multiple_files_patch(self):
        path1 = self._generate_random_filepath()
        path2 = self._generate_random_filepath()
        while path1 == path2:
            path2 = self._generate_random_filepath()

        diff1 = self._create_valid_diff(path1, [self._generate_random_word()], [self._generate_random_word()])
        diff2 = self._create_valid_diff(path2, [self._generate_random_word()], [self._generate_random_word()])

        combined_diff = f"{diff1}\n{diff2}"
        result = self.analyzer.parse(combined_diff)

        self.assertEqual(len(result["files"]), 2)
        target_files = [f["target_file"] for f in result["files"]]
        self.assertIn(path1, target_files)
        self.assertIn(path2, target_files)

    def test_parse_invalid_inputs(self):
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.parse(None)

        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.parse("    \n  ")

    def test_get_statistics_calculation(self):
        file1 = self._generate_random_filepath()
        file2 = self._generate_random_filepath()

        add_count_f1 = random.randint(2, 5)
        del_count_f1 = random.randint(1, 3)

        add_count_f2 = random.randint(1, 4)
        del_count_f2 = random.randint(2, 4)

        old_lines_1 = [f"del_{self._generate_random_word()}" for _ in range(del_count_f1)]
        new_lines_1 = [f"add_{self._generate_random_word()}" for _ in range(add_count_f1)]

        old_lines_2 = [f"del_{self._generate_random_word()}" for _ in range(del_count_f2)]
        new_lines_2 = [f"add_{self._generate_random_word()}" for _ in range(add_count_f2)]

        diff1 = self._create_valid_diff(file1, old_lines_1, new_lines_1)
        diff2 = self._create_valid_diff(file2, old_lines_2, new_lines_2)
        combined = f"{diff1}\n{diff2}"

        stats = self.analyzer.get_statistics(combined)

        expected_additions = add_count_f1 + add_count_f2
        expected_deletions = del_count_f1 + del_count_f2

        self.assertEqual(stats["files_changed"], 2)
        self.assertEqual(stats["additions"], expected_additions)
        self.assertEqual(stats["deletions"], expected_deletions)
        self.assertEqual(stats["total_changes"], expected_additions + expected_deletions)

    def test_get_statistics_non_string(self):
        stats = self.analyzer.get_statistics(random.choice([None, 42, [], {}]))
        self.assertEqual(stats, {"files_changed": 0, "additions": 0, "deletions": 0, "total_changes": 0})

    def test_detect_syntax_risks_merge_markers(self):
        marker = random.choice(["<<<<<<<", "=======", ">>>>>>>"])
        content_word = self._generate_random_word()
        line = f"+ {marker} {content_word}"
        path = self._generate_random_filepath()

        diff = self._create_valid_diff(path, ["old_line"], [line[1:]])
        risks = self.analyzer.detect_syntax_risks(diff)

        found_marker = any(r.get("type") == "merge_conflict_marker" for r in risks)
        self.assertTrue(found_marker)

    def test_detect_syntax_risks_dangerous_calls(self):
        danger = random.choice(["eval", "exec", "os.system"])
        rand_arg = self._generate_random_word()
        line = f"{danger}('{rand_arg}')"
        path = self._generate_random_filepath()

        diff = self._create_valid_diff(path, ["clean_code()"], [line])
        risks = self.analyzer.detect_syntax_risks(diff)

        danger_risks = [r for r in risks if r.get("type") == "dangerous_call"]
        self.assertGreater(len(danger_risks), 0)
        self.assertIn(danger, danger_risks[0]["details"])

    def test_detect_syntax_risks_unbalanced_delimiters(self):
        suffix = random.choice([",", "(", "["])
        line = f"call_func_{self._generate_random_word()}(" + suffix
        path = self._generate_random_filepath()

        diff = self._create_valid_diff(path, ["safe_line()"], [line])
        risks = self.analyzer.detect_syntax_risks(diff)

        unbalanced = [r for r in risks if r.get("type") == "unbalanced_delimiter"]
        self.assertGreater(len(unbalanced), 0)

    def test_detect_syntax_risks_non_string(self):
        self.assertEqual(self.analyzer.detect_syntax_risks(12345), [])

    def test_analyze_valid_patch(self):
        path = self._generate_random_filepath()
        token = self._generate_random_word()
        diff = self._create_valid_diff(path, ["old_val = 1"], [f"new_val = '{token}'"])

        res = self.analyzer.analyze(diff)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["errors"], [])
        self.assertIn(path, res["files"])
        self.assertEqual(res["additions"], 1)
        self.assertEqual(res["deletions"], 1)
        self.assertEqual(len(res["chunks"]), 1)
        self.assertEqual(res["chunks"][0]["new_count"], 1)

    def test_analyze_invalid_patch(self):
        garbage = f"not_a_diff_{self._generate_random_word()}"
        res = self.analyzer.analyze(garbage)

        self.assertFalse(res["is_valid"])
        self.assertGreater(len(res["errors"]), 0)
        self.assertEqual(res["syntax_risks"], [])
        self.assertEqual(res["statistics"]["total_changes"], 0)

    def test_analyze_stream(self):
        path = self._generate_random_filepath()
        token = self._generate_random_word()
        diff = self._create_valid_diff(path, ["var_old"], [f"var_{token}"])

        stream = io.StringIO(diff)
        res = self.analyzer.analyze_stream(stream)

        self.assertTrue(res["is_valid"])
        self.assertIn(path, res["files"])

    def test_analyze_file(self):
        path = self._generate_random_filepath()
        token = self._generate_random_word()
        diff = self._create_valid_diff(path, ["const_a"], [f"const_{token}"])

        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as tmp:
            tmp.write(diff)
            tmp_path = tmp.name

        try:
            res = self.analyzer.analyze_file(tmp_path)
            self.assertTrue(res["is_valid"])
            self.assertIn(path, res["files"])
            self.assertEqual(res["additions"], 1)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()