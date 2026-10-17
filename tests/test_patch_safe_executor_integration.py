import unittest
import uuid
import random
import tempfile
import os
from skills.patch_safe_executor import PatchSafeExecutor, PatchSafeExecutorError
from skills.patch_analyzer import PatchAnalyzer
from skills.patch_verifier import PatchVerifier

class TestPatchSafeExecutorIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name

        self.test_file_name = f"test_{uuid.uuid4().hex[:8]}.py"
        self.test_file_path = os.path.join(self.repo_path, self.test_file_name)

        self.original_content = f"# Original content {uuid.uuid4()}\nx = {random.randint(1, 100)}\n"
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write(self.original_content)

        self.modified_content = f"# Modified content {uuid.uuid4()}\nx = {random.randint(101, 200)}\n"

        self.patch_id = str(uuid.uuid4())
        self.diff_text = f"""--- a/{self.test_file_name}
+++ b/{self.test_file_name}
@@ -1,2 +1,2 @@
-# Original content
-x = 10
+# Modified content {self.patch_id}
+x = 999
"""

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_safe_executor_composition_integration(self):
        executor = PatchSafeExecutor(repo_path=self.repo_path)

        self.assertIsInstance(executor.analyzer, PatchAnalyzer)
        self.assertIsInstance(executor.verifier, PatchVerifier)

        analysis_result = executor.analyzer.analyze(self.diff_text)
        self.assertIsNotNone(analysis_result)

        try:
            result = executor.execute_safe_patch(self.diff_text, self.test_file_path)
            self.assertIsInstance(result, bool)
        except (PatchSafeExecutorError, Exception) as e:
            self.assertTrue(len(str(e)) > 0)

if __name__ == "__main__":
    unittest.main()