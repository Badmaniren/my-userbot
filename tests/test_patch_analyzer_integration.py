import unittest
import uuid
import random
import os
import tempfile
from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError

class TestPatchAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.analyzer = PatchAnalyzer()
        self.test_file_name = f"test_file_{uuid.uuid4().hex[:8]}.py"
        self.added_content_1 = f"print('Hello, {uuid.uuid4()}')"
        self.added_content_2 = f"value = {random.randint(1, 1000)}"

    def test_patch_analyzer_integration_flow(self):
        raw_patch = (
            f"diff --git a/dev/null b/{self.test_file_name}\n"
            f"new file mode 100644\n"
            f"--- /dev/null\n"
            f"+++ b/{self.test_file_name}\n"
            f"@@ -0,0 +1,2 @@\n"
            f"+{self.added_content_1}\n"
            f"+{self.added_content_2}\n"
        )

        result = self.analyzer.analyze(raw_patch)

        self.assertIn(self.test_file_name, result["affected_files"])
        self.assertIn(self.test_file_name, result["new_files"])
        self.assertEqual(result["total_added"], 2)
        self.assertEqual(result["total_removed"], 0)
        self.assertIn(self.added_content_1, result["details"])
        self.assertIn(self.added_content_2, result["details"])
        self.assertEqual(result["complexity"], 2.0)

    def test_patch_analyzer_with_file_input(self):
        deleted_file_name = f"old_module_{uuid.uuid4().hex[:8]}.py"
        removed_line = f"DEPRECATED_VAR = {random.randint(100, 999)}"
        
        raw_patch = (
            f"diff --git a/{deleted_file_name} b/dev/null\n"
            f"deleted file mode 100644\n"
            f"--- a/{deleted_file_name}\n"
            f"+++ /dev/null\n"
            f"@@ -1,1 +0,0 "
            f"-{removed_line}\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as tf:
            tf.write(raw_patch)
            temp_path = tf.name

        try:
            result = self.analyzer.analyze_file(temp_path)
            self.assertIn(deleted_file_name, result["deleted_files"])
            self.assertIn(deleted_file_name, result["affected_files"])
            self.assertEqual(result["total_removed"], 1)
            self.assertEqual(result["total_added"], 0)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()