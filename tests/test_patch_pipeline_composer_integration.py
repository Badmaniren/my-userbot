import unittest
import uuid
import random
import tempfile
import os
from skills.patch_pipeline_composer import PatchPipelineComposer
from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult
from skills.patch_analyzer import PatchAnalyzer

class TestPatchPipelineComposerIntegration(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.composer = PatchPipelineComposer(repo_path=self.repo_path)
        
    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pipeline_composition_real_execution(self):
        unique_id = str(uuid.uuid4())
        random_value = random.randint(1000, 9999)
        
        target_filename = f"test_file_{unique_id}.py"
        target_file_path = os.path.join(self.repo_path, target_filename)
        
        original_code = f"def compute_{unique_id}():\n    return {random_value}\n"
        with open(target_file_path, "w", encoding="utf-8") as f:
            f.write(original_code)
            
        modified_code = f"def compute_{unique_id}():\n    return {random_value} + 1\n"
        
        patch_content = f"""--- a/{target_filename}
+++ b/{target_filename}
@@ -1,2 +1,2 @@
 def compute_{unique_id}():
-    return {random_value}
+    return {random_value} + 1
"""

        result = self.composer.process(patch_content=patch_content, target_file=target_filename)
        
        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(hasattr(result, 'is_safe'))
        self.assertTrue(hasattr(result, 'is_valid'))
        self.assertIsInstance(result.metrics, dict)
        self.assertIsInstance(result.reasons, list)

    def test_pipeline_with_malformed_patch_data(self):
        unique_id = str(uuid.uuid4())
        bad_patch = f"INVALID_DIFF_CONTENT_{unique_id}"
        target_filename = f"non_existent_{unique_id}.py"
        
        result = self.composer.process(patch_content=bad_patch, target_file=target_filename)
        
        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertFalse(result.is_valid)

if __name__ == "__main__":
    unittest.main()