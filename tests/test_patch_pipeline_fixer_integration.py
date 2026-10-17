import unittest
import uuid
import random
import tempfile
import os
from pathlib import Path

from skills.patch_pipeline_fixer import PatchPipelineFixer, PatchPipelineFixerError
from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult
from skills.patch_checker import PatchChecker, PatchCheckerError

class TestPatchPipelineFixerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        self.unique_id = str(uuid.uuid4())
        self.target_file_name = f"module_{self.unique_id[:8]}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_file_name)
        
        self.random_value = random.randint(1000, 99999)
        initial_code = f"# Initial state {self.unique_id}\nSECRET_NUM = {self.random_value}\n\ndef compute():\n    return SECRET_NUM * 2\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(initial_code)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pipeline_fixer_end_to_end_integration(self):
        new_random_value = random.randint(100000, 999999)
        patch_content = f"""--- {self.target_file_name}
+++ {self.target_file_name}
@@ -1,5 +1,5 @@
-# Initial state {self.unique_id}
-SECRET_NUM = {self.random_value}
+# Updated state {self.unique_id}
+SECRET_NUM = {new_random_value}
 
 def compute():
     return SECRET_NUM * 2
"""

        pipeline = PatchPipelineFixer(repo_path=self.repo_path)
        
        result = pipeline.process_and_apply(
            patch_content=patch_content,
            target_file=self.target_file_name
        )

        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertTrue(result["success"], f"Pipeline failed with details: {result}")
        
        with open(self.target_file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        self.assertIn(str(new_random_value), updated_content)
        self.assertIn(self.unique_id, updated_content)

    def test_pipeline_fixer_invalid_patch_handling(self):
        corrupted_patch = f"INVALID_DIFF_FORMAT_{uuid.uuid4()} === RANDOM GARBAGE"
        
        pipeline = PatchPipelineFixer(repo_path=self.repo_path)
        
        result = pipeline.process_and_apply(
            patch_content=corrupted_patch,
            target_file=self.target_file_name
        )

        self.assertIsInstance(result, dict)
        self.assertFalse(result.get("success", True))
        self.assertIn("error", result)

if __name__ == "__main__":
    unittest.main()