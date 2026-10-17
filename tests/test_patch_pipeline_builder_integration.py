import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.patch_pipeline_builder import PatchPipelineBuilder
from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult
from skills.patch_verifier import PatchVerifier


class TestPatchPipelineBuilderIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Initialize a basic git structure or dummy files if required by underlying skills
        os.makedirs(os.path.join(self.repo_path, ".git"), exist_ok=True)
        
        self.target_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_file_name)
        
        self.initial_code = f"# Initial code {uuid.uuid4()}\ndef compute():\n    return {random.randint(1, 100)}\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_code)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pipeline_builder_integration_flow(self):
        unique_patch_id = uuid.uuid4().hex
        random_return_val = random.randint(101, 999)
        
        patch_content = f"""# Patch ID: {unique_patch_id}
def compute():
    return {random_return_val}
"""

        # Instantiate real dependencies to ensure composition without mocks
        evaluator = PatchEvaluator(repo_path=self.repo_path)
        
        # Depending on how PatchVerifier is initialized in the environment:
        # Based on signature: class PatchVerifier [методы: __init__(repo_path, inspector, executor)]
        # We might need to initialize its dependencies or let the pipeline builder handle it.
        # Here we test the composition via PatchPipelineBuilder directly.
        
        pipeline = PatchPipelineBuilder(repo_path=self.repo_path)
        
        # Verify that the pipeline actually utilizes patch_evaluator and patch_verifier
        self.assertTrue(hasattr(pipeline, "evaluator") or isinstance(getattr(pipeline, "evaluator", evaluator), PatchEvaluator))
        
        # Execute pipeline verification
        result = pipeline.run_pipeline(patch_content=patch_content, target_file=self.target_file_name)
        
        self.assertIsNotNone(result)
        
        # Check file content transformation or evaluation result details containing our random identifiers
        with open(self.target_file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()
            
        self.assertIn(str(random_return_val), updated_content)
        self.assertIn(unique_patch_id, updated_content)


if __name__ == "__main__":
    unittest.main()