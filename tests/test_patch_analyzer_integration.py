import unittest
import uuid
import random
import os
import tempfile

from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError
from skills.patch_sanitizer import PatchSanitizer
from skills.code_sanitizer import CodeSanitizer


class TestPatchAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.analyzer = PatchAnalyzer()
        self.patch_sanitizer = PatchSanitizer()
        self.code_sanitizer = CodeSanitizer()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_secure_pipeline_integration_with_sanitized_data(self):
        random_id = str(uuid.uuid4())[:8]
        target_filename = f"module_{random_id}.py"

        raw_diff = f"""--- a/{target_filename}
+++ b/{target_filename}
@@ -1,1 +1,2 @@
-print("old_{random_id}")
+print("new_{random_id}")
+eval("os.system('rm -rf /')")
"""

        sanitized_diff = self.patch_sanitizer.sanitize(raw_diff) if hasattr(self.patch_sanitizer, "sanitize") else raw_diff

        analysis_result = self.analyzer.analyze(sanitized_diff)

        self.assertTrue(analysis_result.get("is_valid"), f"Analysis failed with errors: {analysis_result.get('errors')}")
        self.assertIn(target_filename, analysis_result.get("files", []))
        self.assertGreaterEqual(analysis_result.get("additions", 0), 1)

        risks = analysis_result.get("syntax_risks", [])
        risk_types = [r.get("type") for r in risks]
        self.assertIn("dangerous_call", risk_types)

    def test_file_stream_and_statistics_integration(self):
        random_suffix = uuid.uuid4().hex[:6]
        file_path = os.path.join(self.temp_dir.name, f"patch_{random_suffix}.diff")

        file_content = f"""--- a/src/app.py
+++ b/src/app.py
@@ -5,1 +5,1 @@
-x = {random.randint(1, 50)}
+x = {random.randint(51, 100)}
"""

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        file_result = self.analyzer.analyze_file(file_path)
        self.assertTrue(file_result.get("is_valid"))
        self.assertEqual(file_result["statistics"]["files_changed"], 1)
        self.assertEqual(file_result["statistics"]["additions"], 1)
        self.assertEqual(file_result["statistics"]["deletions"], 1)

        with open(file_path, "r", encoding="utf-8") as stream_f:
            stream_result = self.analyzer.analyze_stream(stream_f)
            self.assertTrue(stream_result.get("is_valid"))
            self.assertEqual(stream_result["statistics"]["total_changes"], 2)


if __name__ == "__main__":
    unittest.main()