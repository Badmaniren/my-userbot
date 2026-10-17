import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.patch_autofix_pipeline import PatchAutofixPipeline, patch_autofix_pipeline
from skills.patch_evaluator import PatchEvaluationResult


class TestPatchAutofixPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.target_file_name = f"test_file_{uuid.uuid4().hex[:8]}.py"
        self.target_file_path = os.path.join(self.test_dir, self.target_file_name)

        self.original_content = f"# Initial content {uuid.uuid4().hex}\nx = {random.randint(1, 100)}\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.original_content)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pipeline_integration_flow(self):
        unique_string = f"print('{uuid.uuid4().hex}')"

        malformed_patch = f"""--- {self.target_file_name}
+++ {self.target_file_name}
@@ -1,2 +1,2 @@
-x = 1
+x = 2
 {unique_string}
"""
        pipeline = PatchAutofixPipeline(self.test_dir)

        result = pipeline.run(patch_content=malformed_patch, target_file=self.target_file_name)

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(hasattr(result, "is_safe"))
        self.assertTrue(hasattr(result, "is_valid"))
        self.assertTrue(hasattr(result, "metrics"))

    def test_functional_interface_integration(self):
        random_val = random.randint(1000, 9999)
        patch_content = f"""--- {self.target_file_name}
+++ {self.target_file_name}
@@ -1,2 +1,2 @@
-x = 1
+x = {random_val}
"""
        result = patch_autofix_pipeline(
            repo_path=self.test_dir,
            patch_content=patch_content,
            target_file=self.target_file_name
        )

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertIsNotNone(result.metrics)


if __name__ == "__main__":
    unittest.main()