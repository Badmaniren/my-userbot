import io
import os
import random
import string
import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch

try:
    from skills.patch_analyzer import GitInspector, PatchAnalyzer, PatchAnalyzerError
except ImportError:
    from patch_analyzer import GitInspector, PatchAnalyzer, PatchAnalyzerError


def _rand_name(prefix="test_"):
    return f"{prefix}{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}"


class TestPatchAnalyzerError(unittest.TestCase):
    def test_exception_inheritance_and_raising(self):
        msg = f"Error_{_rand_name()}"
        with self.assertRaises(PatchAnalyzerError) as ctx:
            raise PatchAnalyzerError(msg)
        self.assertEqual(str(ctx.exception), msg)


class TestGitInspector(unittest.TestCase):
    def test_init_sets_repo_path(self):
        rand_path = f"/tmp/{_rand_name('repo_')}"
        inspector = GitInspector(rand_path)
        self.assertEqual(inspector.repo_path, rand_path)


class TestPatchAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = PatchAnalyzer()

    def test_analyze_standard_diff(self):
        filename = f"src/{_rand_name()}.py"
        add_lines_count = random.randint(3, 8)
        rem_lines_count = random.randint(2, 6)

        added_content = [f"line_add_{_rand_name()}" for _ in range(add_lines_count)]
        removed_content = [f"line_rem_{_rand_name()}" for _ in range(rem_lines_count)]

        patch_lines = [
            f"diff --git a/{filename} b/{filename}",
            f"--- a/{filename}",
            f"+++ b/{filename}",
        ]
        for line in added_content:
            patch_lines.append(f"+{line}")
        for line in removed_content:
            patch_lines.append(f"-{line}")

        raw_patch = "\n".join(patch_lines)
        result = self.analyzer.analyze(raw_patch)

        self.assertEqual(result["total_added"], add_lines_count)
        self.assertEqual(result["total_removed"], rem_lines_count)
        self.assertEqual(result["additions"], add_lines_count)
        self.assertEqual(result["deletions"], rem_lines_count)
        self.assertEqual(result["added_lines"], add_lines_count)
        self.assertEqual(result["deleted_lines"], rem_lines_count)
        self.assertEqual(result["complexity"], float(add_lines_count + rem_lines_count))
        self.assertEqual(result["diff_complexity"], float(add_lines_count + rem_lines_count))
        self.assertIn(filename, result["affected_files"])
        self.assertIn(filename, result["files"])

        for line in added_content:
            self.assertIn(line, result["details"])
        for line in removed_content:
            self.assertIn(line, result["details"])

    def test_analyze_new_file(self):
        filename = f"docs/{_rand_name()}.md"
        val_content = f"content_{_rand_name()}"

        raw_patch = (
            f"diff --git a/dev/null b/{filename}\n"
            f"new file mode 100644\n"
            f"--- /dev/null\n"
            f"+++ b/{filename}\n"
            f"+{val_content}\n"
        )

        result = self.analyzer.analyze(raw_patch)

        self.assertIn(filename, result["new_files"])
        self.assertIn(filename, result["affected_files"])
        self.assertEqual(result["total_added"], 1)
        self.assertEqual(result["total_removed"], 0)

    def test_analyze_deleted_file(self):
        filename = f"legacy/{_rand_name()}.py"
        val_content = f"old_code_{_rand_name()}"

        raw_patch = (
            f"diff --git a/{filename} b/dev/null\n"
            f"deleted file mode 100644\n"
            f"--- a/{filename}\n"
            f"+++ /dev/null\n"
            f"-{val_content}\n"
        )

        result = self.analyzer.analyze(raw_patch)

        self.assertIn(filename, result["deleted_files"])
        self.assertIn(filename, result["affected_files"])
        self.assertEqual(result["total_added"], 0)
        self.assertEqual(result["total_removed"], 1)

    def test_analyze_bytes_input(self):
        filename = f"pkg/{_rand_name()}.py"
        line_val = f"data_{_rand_name()}"
        raw_patch_str = f"diff --git a/{filename} b/{filename}\n+{line_val}\n"
        raw_patch_bytes = raw_patch_str.encode("utf-8")

        result = self.analyzer.analyze(raw_patch_bytes)

        self.assertEqual(result["total_added"], 1)
        self.assertIn(filename, result["affected_files"])
        self.assertIn(line_val, result["details"])

    def test_analyze_invalid_bytes_fallback(self):
        invalid_bytes = b"\x80\x81\xff\xfe"
        result = self.analyzer.analyze(invalid_bytes)

        self.assertEqual(result["total_added"], 0)
        self.assertEqual(result["total_removed"], 0)
        self.assertEqual(result["affected_files"], [])

    def test_analyze_non_string_non_bytes_input(self):
        num_input = random.randint(1000, 9999)
        result = self.analyzer.analyze(num_input)

        self.assertEqual(result["total_added"], 0)
        self.assertEqual(result["total_removed"], 0)

    def test_analyze_stream(self):
        filename = f"stream/{_rand_name()}.txt"
        val_content = f"stream_val_{_rand_name()}"
        raw_patch = f"diff --git a/{filename} b/{filename}\n+{val_content}\n"

        stream = io.BytesIO(raw_patch.encode("utf-8"))
        result = self.analyzer.analyze_stream(stream)

        self.assertEqual(result["total_added"], 1)
        self.assertIn(filename, result["affected_files"])
        self.assertIn(val_content, result["details"])

    def test_analyze_file(self):
        filename = f"file/{_rand_name()}.txt"
        val_content = f"file_val_{_rand_name()}"
        raw_patch = f"diff --git a/{filename} b/{filename}\n+{val_content}\n"

        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as tmp:
            tmp.write(raw_patch)
            tmp_path = tmp.name

        try:
            result = self.analyzer.analyze_file(tmp_path)
            self.assertEqual(result["total_added"], 1)
            self.assertIn(filename, result["affected_files"])
            self.assertIn(val_content, result["details"])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_aliases_and_callable(self):
        filename = f"alias/{_rand_name()}.py"
        val_content = f"alias_val_{_rand_name()}"
        raw_patch = f"diff --git a/{filename} b/{filename}\n+{val_content}\n"

        res_base = self.analyzer.analyze(raw_patch)
        res_patch = self.analyzer.analyze_patch(raw_patch)
        res_diff = self.analyzer.analyze_diff(raw_patch)
        res_call = self.analyzer(raw_patch)

        self.assertEqual(res_base, res_patch)
        self.assertEqual(res_base, res_diff)
        self.assertEqual(res_base, res_call)


if __name__ == "__main__":
    unittest.main()