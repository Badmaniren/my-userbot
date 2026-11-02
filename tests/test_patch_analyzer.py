import io
import os
import random
import re
import unittest
import uuid
from unittest.mock import patch, mock_open

from skills.patch_analyzer import (
    PatchAnalyzerError,
    GitInspector,
    PatchAnalyzer,
    analyze
)


class TestPatchAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = PatchAnalyzer()
        self.random_repo_path = f"/repo/{uuid.uuid4().hex}"
        self.git_inspector = GitInspector(repo_path=self.random_repo_path)

    def test_git_inspector_init(self):
        self.assertEqual(self.git_inspector.repo_path, self.random_repo_path)

    def test_patch_analyzer_error_inheritance(self):
        self.assertTrue(issubclass(PatchAnalyzerError, Exception))
        err_msg = uuid.uuid4().hex
        with self.assertRaises(PatchAnalyzerError) as ctx:
            raise PatchAnalyzerError(err_msg)
        self.assertIn(err_msg, str(ctx.exception))

    def test_analyze_with_bytes_input(self):
        file_name = f"src/{uuid.uuid4().hex}.py"
        added_line = f"print('{uuid.uuid4().hex}')"
        patch_content = f"diff --git a/{file_name} b/{file_name}\n--- a/{file_name}\n+++ b/{file_name}\n@@ -1,1 +1,2られる@@\n+{added_line}\n".encode("utf-8")

        result = self.analyzer.analyze(patch_content)
        self.assertIn(file_name, result["affected_files"])
        self.assertIn(added_line, result["details"])
        self.assertGreaterEqual(result["total_added"], 1)

    def test_analyze_with_invalid_bytes_fallback(self):
        invalid_bytes = b"\xff\xfe\xfd\xfc"
        result = self.analyzer.analyze(invalid_bytes)
        self.assertEqual(result["affected_files"], [])
        self.assertEqual(result["total_added"], 0)
        self.assertEqual(result["total_removed"], 0)

    def test_analyze_with_non_string_non_bytes(self):
        random_number = random.randint(1000, 99999)
        result = self.analyzer.analyze(random_number)
        self.assertEqual(result["affected_files"], [])
        self.assertEqual(result["total_added"], 0)

    def test_analyze_new_and_deleted_files(self):
        new_file = f"modules/{uuid.uuid4().hex}.py"
        del_file = f"legacy/{uuid.uuid4().hex}.py"
        
        patch_content = (
            f"diff --git a/dev/null b/{new_file}\n"
            f"new file mode 100644\n"
            f"--- /dev/null\n"
            f"+++ b/{new_file}\n"
            f"@@ -0,0 +1,1 @@\n"
            f"+import {uuid.uuid4().hex}\n"
            f"diff --git a/{del_file} b/dev/null\n"
            f"deleted file mode 100644\n"
            f"--- a/{del_file}\n"
            f"+++ /dev/null\n"
            f"@@ -1,1 +0,0 @@\n"
            f"-old_var = {random.randint(1, 100)}\n"
        )

        result = self.analyzer.analyze(patch_content)
        self.assertIn(new_file, result["new_files"])
        self.assertIn(del_file, result["deleted_files"])
        self.assertIn(new_file, result["affected_files"])
        self.assertIn(del_file, result["affected_files"])
        self.assertEqual(result["total_added"], 1)
        self.assertEqual(result["total_removed"], 1)

    def test_analyze_stream(self):
        file_name = f"utils/{uuid.uuid4().hex}.py"
        added_content = f"VAL = '{uuid.uuid4().hex}'"
        patch_text = f"diff --git a/{file_name} b/{file_name}\n--- a/{file_name}\n+++ b/{file_name}\n+{added_content}\n"
        
        stream = io.BytesIO(patch_text.encode("utf-8"))
        result = self.analyzer.analyze_stream(stream)
        
        self.assertIn(file_name, result["affected_files"])
        self.assertIn(added_content, result["details"])

    def test_analyze_file(self):
        file_name = f"tests/test_{uuid.uuid4().hex}.py"
        patch_text = f"diff --git a/{file_name} b/{file_name}\n--- a/{file_name}\n+++ b/{file_name}\n-+{uuid.uuid4().hex}\n"
        
        mock_file_data = mock_open(read_data=patch_text)
        with patch("builtins.open", mock_file_data):
            random_path = f"/tmp/{uuid.uuid4().hex}.patch"
            result = self.analyzer.analyze_file(random_path)
            mock_file_data.assert_called_once_with(random_path, "r", encoding="utf-8")
            self.assertIn(file_name, result["affected_files"])

    def test_aliases_and_call(self):
        file_name = f"core/{uuid.uuid4().hex}.py"
        patch_text = f"diff --git a/{file_name} b/{file_name}\n--- a/{file_name}\n+++ b/{file_name}\n+x = {random.randint(1, 50)}\n"

        res_patch = self.analyzer.analyze_patch(patch_text)
        res_diff = self.analyzer.analyze_diff(patch_text)
        res_call = self.analyzer(patch_text)
        res_module_func = analyze(patch_text)

        for res in [res_patch, res_diff, res_call, res_module_func]:
            self.assertIn(file_name, res["affected_files"])
            self.assertEqual(res["total_added"], 1)

    def test_hunk_parsing_complexity(self):
        file_name = f"api/{uuid.uuid4().hex}.py"
        add_str = uuid.uuid4().hex
        rem_str = uuid.uuid4().hex
        
        patch_text = (
            f"diff --git a/{file_name} b/{file_name}\n"
            f"--- a/{file_name}\n"
            f"+++ b/{file_name}\n"
            f"@@ -10,3 +10,4 @@\n"
            f"-{rem_str}\n"
            f"+{add_str}\n"
            f"+additional_{uuid.uuid4().hex}\n"
        )

        result = self.analyzer.analyze(patch_text)
        self.assertEqual(result["total_added"], 2)
        self.assertEqual(result["total_removed"], 1)
        self.assertEqual(result["complexity"], 3.0)
        self.assertEqual(result["diff_complexity"], 3.0)
        self.assertEqual(result["additions"], 2)
        self.assertEqual(result["deletions"], 1)


if __name__ == "__main__":
    unittest.main()