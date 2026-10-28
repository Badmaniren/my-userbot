import io
import random
import string
import unittest
from unittest.mock import MagicMock, mock_open, patch

from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError


class TestPatchAnalyzer(unittest.TestCase):
    def setUp(self):
        self.random_prefix = f"ref_{uuid_hex()}"

    def _generate_random_filepath(self) -> str:
        depth = random.randint(1, 4)
        parts = [
            "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 8)))
            for _ in range(depth)
        ]
        ext = random.choice([".py", ".ts", ".go", ".rs", ".cpp", ".md"])
        return "/".join(parts) + ext

    def _generate_single_file_diff(self):
        file_path = self._generate_random_filepath()
        added_count = random.randint(1, 15)
        removed_count = random.randint(1, 15)

        added_tokens = [
            f"token_{uuid_hex()}_{i}" for i in range(added_count)
        ]
        removed_tokens = [
            f"old_token_{uuid_hex()}_{i}" for i in range(removed_count)
        ]

        diff_lines = [
            f"diff --git a/{file_path} b/{file_path}",
            f"index {uuid_hex()[:7]}..{uuid_hex()[:7]} 100644",
            f"--- a/{file_path}",
            f"+++ b/{file_path}",
            f"@@ -1,{removed_count} +1,{added_count} @@",
        ]

        for token in removed_tokens:
            diff_lines.append(f"-    # {token}")
        for token in added_tokens:
            diff_lines.append(f"+    # {token}")

        raw_patch = "\n".join(diff_lines) + "\n"
        return {
            "path": file_path,
            "added_count": added_count,
            "removed_count": removed_count,
            "added_tokens": added_tokens,
            "removed_tokens": removed_tokens,
            "raw_patch": raw_patch,
        }

    def test_analyze_single_file_patch_structure(self):
        diff_data = self._generate_single_file_diff()
        analyzer = PatchAnalyzer()

        result = analyzer.analyze(diff_data["raw_patch"])

        self.assertIsInstance(result, dict)
        self.assertIn("affected_files", result)
        self.assertIn(diff_data["path"], result["affected_files"])

        if "total_added" in result:
            self.assertEqual(result["total_added"], diff_data["added_count"])
        if "total_removed" in result:
            self.assertEqual(result["total_removed"], diff_data["removed_count"])

    def test_extracted_line_content_verification(self):
        diff_data = self._generate_single_file_diff()
        analyzer = PatchAnalyzer()

        analysis = analyzer.analyze(diff_data["raw_patch"])

        extracted_added = str(analysis.get("added_lines", "")) + str(
            analysis.get("details", "")
        )
        for token in diff_data["added_tokens"]:
            self.assertIn(token, extracted_added)

    def test_multi_file_patch_file_listing_and_totals(self):
        file_count = random.randint(2, 5)
        diffs = [self._generate_single_file_diff() for _ in range(file_count)]
        combined_patch = "\n".join([d["raw_patch"] for d in diffs])

        expected_files = {d["path"] for d in diffs}
        expected_added = sum(d["added_count"] for d in diffs)
        expected_removed = sum(d["removed_count"] for d in diffs)

        analyzer = PatchAnalyzer()
        report = analyzer.analyze(combined_patch)

        affected = set(report.get("affected_files", []))
        self.assertEqual(affected, expected_files)

        if "total_added" in report:
            self.assertEqual(report["total_added"], expected_added)
        if "total_removed" in report:
            self.assertEqual(report["total_removed"], expected_removed)

    def test_diff_complexity_score_calculation(self):
        diff_data = self._generate_single_file_diff()
        analyzer = PatchAnalyzer()

        analysis = analyzer.analyze(diff_data["raw_patch"])

        self.assertIn("complexity", analysis)
        complexity = analysis["complexity"]
        self.assertIsInstance(complexity, (int, float))
        self.assertGreaterEqual(complexity, 0)

    def test_empty_or_whitespace_patch_handling(self):
        analyzer = PatchAnalyzer()
        whitespace_patch = "   \n\n  \t  \n"

        try:
            res = analyzer.analyze(whitespace_patch)
            self.assertEqual(res.get("affected_files", []), [])
            self.assertEqual(res.get("total_added", 0), 0)
            self.assertEqual(res.get("total_removed", 0), 0)
        except PatchAnalyzerError:
            pass

    def test_malformed_patch_raises_exception_or_handles_gracefully(self):
        analyzer = PatchAnalyzer()
        garbage_string = f"GARBAGE_TOKEN_{uuid_hex()}_{uuid_hex()}"

        try:
            res = analyzer.analyze(garbage_string)
            self.assertIsInstance(res, dict)
            self.assertEqual(len(res.get("affected_files", [])), 0)
        except PatchAnalyzerError as exc:
            self.assertIsInstance(exc, PatchAnalyzerError)

    def test_stream_patch_reading_and_chaos_payload(self):
        diff_data = self._generate_single_file_diff()
        patch_bytes = diff_data["raw_patch"].encode("utf-8")
        stream_mock = io.BytesIO(patch_bytes)

        analyzer = PatchAnalyzer()

        if hasattr(analyzer, "analyze_stream"):
            res = analyzer.analyze_stream(stream_mock)
        else:
            res = analyzer.analyze(stream_mock.read().decode("utf-8"))

        self.assertIn(diff_data["path"], res.get("affected_files", []))

    def test_file_reading_with_mock_open(self):
        diff_data = self._generate_single_file_diff()
        fake_path = f"/tmp/{uuid_hex()}/{uuid_hex()}.patch"

        analyzer = PatchAnalyzer()

        with patch("builtins.open", mock_open(read_data=diff_data["raw_patch"])):
            if hasattr(analyzer, "analyze_file"):
                res = analyzer.analyze_file(fake_path)
            else:
                with open(fake_path, "r", encoding="utf-8") as f:
                    content = f.read()
                res = analyzer.analyze(content)

        self.assertIn(diff_data["path"], res.get("affected_files", []))

    def test_patch_with_new_file_creation(self):
        new_file = self._generate_random_filepath()
        token = f"new_file_token_{uuid_hex()}"
        diff_lines = [
            f"diff --git a/dev/null b/{new_file}",
            "new file mode 100644",
            f"--- /dev/null",
            f"+++ b/{new_file}",
            "@@ -0,0 +1,1 @@",
            f"+{token}",
        ]
        raw_patch = "\n".join(diff_lines) + "\n"

        analyzer = PatchAnalyzer()
        res = analyzer.analyze(raw_patch)

        self.assertIn(new_file, res.get("affected_files", []))
        if "new_files" in res:
            self.assertIn(new_file, res["new_files"])

    def test_patch_with_file_deletion(self):
        deleted_file = self._generate_random_filepath()
        token = f"deleted_token_{uuid_hex()}"
        diff_lines = [
            f"diff --git a/{deleted_file} b/dev/null",
            "deleted file mode 100644",
            f"--- a/{deleted_file}",
            "+++ /dev/null",
            "@@ -1,1 +0,0 @@",
            f"-{token}",
        ]
        raw_patch = "\n".join(diff_lines) + "\n"

        analyzer = PatchAnalyzer()
        res = analyzer.analyze(raw_patch)

        self.assertIn(deleted_file, res.get("affected_files", []))
        if "deleted_files" in res:
            self.assertIn(deleted_file, res["deleted_files"])


def uuid_hex() -> str:
    import uuid

    return uuid.uuid4().hex


if __name__ == "__main__":
    unittest.main()