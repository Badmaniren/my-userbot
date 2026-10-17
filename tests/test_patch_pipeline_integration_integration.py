import unittest
import uuid
import random
import tempfile
import os
from pathlib import Path

from skills.patch_pipeline_integration import PatchPipelineIntegration
from skills.patch_analyzer import PatchAnalyzer
from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult


class TestPatchPipelineIntegrationIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        self.pipeline = PatchPipelineIntegration(repo_path=self.repo_path)
        
        self.unique_id = str(uuid.uuid4())
        self.random_value = random.randint(1000, 99999)
        
        self.target_file_name = f"test_file_{self.unique_id}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_file_name)
        
        original_content = f"# Initial version {self.unique_id}\ndef target_func_{self.random_value}():\n    return {self.random_value}\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(original_content)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pipeline_integration_real_execution(self):
        new_return_val = self.random_value + 1
        patch_content = (
            f"--- a/{self.target_file_name}\n"
            f"+++ b/{self.target_file_name}\n"
            f"@@ -1,3 +1,3 @@\n"
            f" # Initial version {self.unique_id}\n"
            f" def target_func_{self.random_value}():\n"
            f"-    return {self.random_value}\n"
            f"+    return {new_return_val}\n"
        )

        result = self.pipeline.execute_pipeline(
            patch_content=patch_content,
            target_file=self.target_file_name
        )

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_valid)
        self.assertTrue(result.is_safe)
        
        with open(self.target_file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()
            
        self.assertIn(str(new_return_val), updated_content)
        self.assertIn(self.unique_id, updated_content)


if __name__ == "__main__":
    unittest.main()