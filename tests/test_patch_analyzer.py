import io
import random
import string
import unittest
import uuid
from unittest.mock import patch, mock_open

from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError


def _generate_random_token(length=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _generate_random_filename(ext=".py"):
    folder = _generate_random_token(6)
    name = _generate_random_token(10)
    return f"{folder}/{name}{ext}"


def _build_unified_diff(file_path, old_lines, new_lines, start_old=1, start_new=1):
    diff_lines = [
        f"--- a/{file_path}",
        f"+++ b/{file_path}",
        f"@@ -{start_old},{len(old_lines)} +{start_new},{len(new_lines)} @@",
    ]
    for line in old_lines:
        diff_lines.append(f"-{line}")
    for line in new_lines:
        diff_lines.append(f"+{line}")
    return "\n".join(diff_lines) + "\n"


class TestPatchAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = PatchAnalyzer()

    def test_parse_valid_single_file_diff(self):
        rand_file = _generate_random_filename()
        rand_var = f"var_{_generate_random_token(6)}"
        rand_val = random.randint(100, 9999)

        old_lines = [f"{rand_var} = {rand_val}"]
        new_lines = [
            f"{rand_var} = {rand_val + 1}",
            f"print({rand_var})",
        ]
        diff_text = _build_unified_diff(rand_file, old_lines, new_lines)

        result = self.analyzer.parse(diff_text)

        self.assertIn("files", result)
        self.assertEqual(len(result["files"]), 1)
        file_info = result["files"][0]
        self.assertIn(rand_file, file_info["target_file"])
        self.assertEqual(len(file_info["chunks"]), 1)

        chunk = file_info["chunks"][0]
        self.assertEqual(chunk["old_count"], len(old_lines))
        self.assertEqual(chunk["new_count"], len(new_lines))

    def test_statistics_calculation_accuracy(self):
        file_count = random.randint(2, 4)
        total_additions = 0
        total_deletions = 0
        diff_chunks = []

        for _ in range(file_count):
            rand_file = _generate_random_filename()
            add_count = random.randint(1, 5)
            del_count = random.randint(1, 5)
            total_additions += add_count
            total_deletions += del_count

            old_lines = [f"old_{_generate_random_token(4)}_{idx} = False" for idx in range(del_count)]
            new_lines = [f"new_{_generate_random_token(4)}_{idx} = True" for idx in range(add_count)]
            diff_chunks.append(_build_unified_diff(rand_file, old_lines, new_lines))

        full_diff = "\n".join(diff_chunks)
        stats = self.analyzer.get_statistics(full_diff)

        self.assertEqual(stats["files_changed"], file_count)
        self.assertEqual(stats["additions"], total_additions)
        self.assertEqual(stats["deletions"], total_deletions)
        self.assertEqual(stats["total_changes"], total_additions + total_deletions)

    def test_detect_syntax_risk_unclosed_delimiter(self):
        rand_file = _generate_random_filename()
        rand_func = f"func_{_generate_random_token(6)}"
        broken_line = f"def {rand_func}(arg1, arg2: [1, 2, "
        
        diff_text = _build_unified_diff(rand_file, [], [broken_line])
        risks = self.analyzer.detect_syntax_risks(diff_text)

        self.assertTrue(any(risk.get("type") == "unbalanced_delimiter" for risk in risks))
        self.assertTrue(any(rand_func in risk.get("details", "") for risk in risks))

    def test_detect_syntax_risk_merge_conflict_marker(self):
        rand_file = _generate_random_filename()
        conflict_marker = f"<<<<<<< HEAD:{_generate_random_token(6)}"
        rand_content = f"value = '{_generate_random_token(12)}'"

        diff_text = _build_unified_diff(rand_file, [], [conflict_marker, rand_content])
        risks = self.analyzer.detect_syntax_risks(diff_text)

        self.assertTrue(any(risk.get("type") == "merge_conflict_marker" for risk in risks))

    def test_detect_dangerous_calls_risk(self):
        rand_file = _generate_random_filename()
        dangerous_func = random.choice(["eval", "exec", "os.system"])
        payload = f"payload_{_generate_random_token(5)}"
        risky_line = f"{dangerous_func}('{payload}')"

        diff_text = _build_unified_diff(rand_file, [], [risky_line])
        risks = self.analyzer.detect_syntax_risks(diff_text)

        self.assertTrue(any(risk.get("type") == "dangerous_call" for risk in risks))
        self.assertTrue(any(dangerous_func in risk.get("details", "") for risk in risks))

    def test_corrupted_hunk_header_raises_exception(self):
        rand_file = _generate_random_filename()
        corrupted_header = f"@@ -invalid_header +{_generate_random_token(4)} @@"
        bad_diff = (
            f"--- a/{rand_file}\n"
            f"+++ b/{rand_file}\n"
            f"{corrupted_header}\n"
            f"+random_code_{_generate_random_token(5)} = 42\n"
        )

        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.validate_structure(bad_diff)

    def test_empty_or_whitespace_diff_raises_exception(self):
        empty_diff = "   \n\t  \n"
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.parse(empty_diff)

    def test_invalid_diff_type_raises_exception(self):
        invalid_input = random.choice([None, 12345, [], {}])
        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.parse(invalid_input)

    def test_analyze_aggregate_pipeline(self):
        rand_file = _generate_random_filename()
        del_name = f"del_{_generate_random_token(4)}"
        add_name = f"add_{_generate_random_token(4)}"
        old_lines = [f"{del_name} = 1"]
        new_lines = [f"{add_name} = 2"]

        diff_text = _build_unified_diff(rand_file, old_lines, new_lines)
        analysis = self.analyzer.analyze(diff_text)

        self.assertIn("parsed", analysis)
        self.assertIn("statistics", analysis)
        self.assertIn("risks", analysis)
        self.assertIn("is_valid", analysis)

        self.assertTrue(analysis["is_valid"])
        self.assertEqual(analysis["statistics"]["additions"], 1)
        self.assertEqual(analysis["statistics"]["deletions"], 1)

    def test_analyze_stream_reading(self):
        rand_file = _generate_random_filename()
        rand_var = f"stream_{_generate_random_token(6)}"
        diff_text = _build_unified_diff(rand_file, [], [f"{rand_var} = 999"])

        stream = io.StringIO(diff_text)
        stats = self.analyzer.analyze_stream(stream)

        self.assertEqual(stats["statistics"]["files_changed"], 1)
        self.assertEqual(stats["statistics"]["additions"], 1)

    def test_analyze_file_with_mocked_io(self):
        rand_path = f"/var/tmp/{_generate_random_token(8)}/{_generate_random_token(5)}.patch"
        rand_file = _generate_random_filename()
        diff_text = _build_unified_diff(rand_file, ["x = 1"], ["x = 2", "y = 3"])

        with patch("builtins.open", mock_open(read_data=diff_text)) as mocked_file:
            analysis = self.analyzer.analyze_file(rand_path)
            mocked_file.assert_called_once_with(rand_path, "r", encoding="utf-8")
            self.assertEqual(analysis["statistics"]["additions"], 2)
            self.assertEqual(analysis["statistics"]["deletions"], 1)

    def test_hunk_line_count_mismatch_validation(self):
        rand_file = _generate_random_filename()
        declared_add_count = 5
        actual_add_lines = [f"val_{idx} = {idx}" for idx in range(2)]  # Only 2 lines instead of 5
        
        diff_text = (
            f"--- a/{rand_file}\n"
            f"+++ b/{rand_file}\n"
            f"@@ -0,0 +1,{declared_add_count} @@\n"
        )
        for line in actual_add_lines:
            diff_text += f"+{line}\n"

        with self.assertRaises(PatchAnalyzerError):
            self.analyzer.validate_structure(diff_text)


if __name__ == "__main__":
    unittest.main()