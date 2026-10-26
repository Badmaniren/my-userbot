import unittest
import uuid
import random
import io
from pathlib import Path
from skills.patch_evaluator import (
    PatchEvaluator,
    PatchEvaluationResult,
    PatchEvaluatorError,
    patch_evaluator
)

class TestPatchEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.repo_path = str(Path("test_repo_" + uuid.uuid4().hex))
        self.evaluator = PatchEvaluator(repo_path=self.repo_path)

    def test_patch_evaluator_lifecycle_and_random_input(self):
        random_suffix = uuid.uuid4().hex
        random_metric_val = random.randint(1, 1000)
        
        patch_content = f"print('Integration test {random_suffix}: {random_metric_val}')"
        
        result = self.evaluator.evaluate(
            patch_content=patch_content,
            collect_telemetry=True,
            target_file=f"file_{random_suffix}.py"
        )
        
        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)
        self.assertIn("snapshot_id", result.telemetry)

    def test_patch_evaluator_stream_and_autocorrect(self):
        random_token = uuid.uuid4().hex
        stream_content = f"# Stream test content {random_token}".encode('utf-8')
        stream = io.BytesIO(stream_content)

        result = self.evaluator.evaluate_stream(stream)
        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)

        autocorrect_result = self.evaluator.evaluate_with_autocorrect(f"content_{random_token}")
        self.assertIsInstance(autocorrect_result, PatchEvaluationResult)
        self.assertIsInstance(autocorrect_result.was_corrected, bool)

    def test_functional_helper_wrapper(self):
        random_data = f"data_{uuid.uuid4().hex}"
        res = patch_evaluator(
            repo_path=self.repo_path,
            patch_data=random_data,
            target_file="dummy.py"
        )
        self.assertIsInstance(res, PatchEvaluationResult)
        self.assertTrue(res.is_safe)

if __name__ == "__main__":
    unittest.main()