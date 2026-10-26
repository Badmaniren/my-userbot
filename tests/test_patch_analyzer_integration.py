import unittest
import uuid
import random
import tempfile
import os
import shutil

from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError
from skills.code_sanitizer import CodeSanitizerError
from skills.code_validator import CodeValidatorError


class TestPatchAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.analyzer = PatchAnalyzer()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_patch_analyzer_full_pipeline_integration(self):
        random_suffix = uuid.uuid4().hex[:8]
        target_filename = f"module_{random_suffix}.py"

        add_count = random.randint(2, 5)
        del_count = random.randint(1, 3)

        diff_lines = [
            f"--- a/{target_filename}",
            f"+++ b/{target_filename}",
            f"@@ -1,{del_count} +1,{add_count} @@"
        ]

        for _ in range(del_count):
            diff_lines.append(f"-old_line_{uuid.uuid4().hex[:4]}()")

        for i in range(add_count):
            if i == 0:
                diff_lines.append("+os.system('echo test')")
            else:
                diff_lines.append(f"+print(val_{uuid.uuid4().hex[:4]})")

        diff_text = "\n".join(diff_lines) + "\n"

        file_path = os.path.join(self.test_dir, f"patch_{random_suffix}.diff")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(diff_text)

        analysis_result = self.analyzer.analyze_file(file_path)

        self.assertTrue(analysis_result.get("is_valid"))
        self.assertIn(target_filename, analysis_result.get("files"))
        self.assertEqual(analysis_result.get("additions"), add_count)
        self.assertEqual(analysis_result.get("deletions"), del_count)

        risks = analysis_result.get("syntax_risks", [])
        self.assertTrue(any(risk.get("type") == "dangerous_call" for risk in risks))

    def test_patch_analyzer_stream_and_invalid_integration(self):
        random_id = uuid.uuid4().hex
        corrupted_diff = f"@@ -1,1 +1,1 @@\n-invalid_del_{random_id}\n+mismatch_add\n"

        analysis_result = self.analyzer.analyze(corrupted_diff)

        self.assertFalse(analysis_result.get("is_valid"))
        self.assertTrue(len(analysis_result.get("errors")) > 0)
        self.assertEqual(analysis_result.get("statistics").get("total_changes"), 0)


if __name__ == "__main__":
    unittest.main()