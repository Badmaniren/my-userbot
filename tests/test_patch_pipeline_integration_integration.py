import unittest
import uuid
import tempfile
import os
from skills.patch_pipeline_integration import PatchPipelineIntegration, PatchPipelineError

class TestPatchPipelineIntegrationIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.pipeline = PatchPipelineIntegration(repo_path=self.repo_path)
        self.random_token = str(uuid.uuid4())

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pipeline_execution_with_valid_patch(self):
        target_filename = f"test_file_{uuid.uuid4().hex[:8]}.py"
        target_file_path = os.path.join(self.repo_path, target_filename)
        
        original_content = f"# {self.random_token}\ndef foo():\n    pass\n"
        with open(target_file_path, "w", encoding="utf-8") as f:
            f.write(original_content)

        patch_content = f"""diff --git a/{target_filename} b/{target_filename}
--- a/{target_filename}
+++ b/{target_filename}
@@ -1,3 +1,3 @@
-# {self.random_token}
+# {self.random_token} modified
 def foo():
-    pass
+    return True
"""

        result = self.pipeline.execute_pipeline(patch_content=patch_content, target_file=target_filename)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "is_safe"))
        self.assertTrue(hasattr(result, "is_valid"))

    def test_pipeline_execution_invalid_patch(self):
        invalid_patch = f"INVALID DIFF CONTENT {self.random_token}"
        with self.assertRaises(PatchPipelineError):
            self.pipeline.execute_pipeline(patch_content=invalid_patch)

if __name__ == "__main__":
    unittest.main()