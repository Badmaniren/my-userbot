import unittest
import uuid
import random
import io
from pathlib import Path
from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult, PatchEvaluatorError

class TestPatchEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.random_repo_name = f"test_repo_{uuid.uuid4().hex[:8]}"
        self.repo_path = Path(f"/tmp/{self.random_repo_name}")
        self.repo_path.mkdir(parents=True, exist_ok=True)
        self.evaluator = PatchEvaluator(self.repo_path)

    def tearDown(self):
        if self.repo_path.exists():
            for file in self.repo_path.glob("*"):
                file.unlink()
            self.repo_path.rmdir()

    def test_evaluate_integration_flow(self):
        random_string = uuid.uuid4().hex
        patch_content = f"diff --git a/test.py b/test.py\nindex 1234567..89abcdef 100644\n--- a/test.py\n+++ b/test.py\n@@ -1,1 +1,1 @@\n-print('old')\n+print('{random_string}')"
        
        target_file_name = f"target_{uuid.uuid4().hex[:6]}.py"
        
        result = self.evaluator.evaluate(
            patch_content=patch_content,
            collect_telemetry=True,
            target_file=target_file_name
        )
        
        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)
        self.assertIsInstance(result.metrics, dict)
        self.assertIsInstance(result.telemetry, dict)
        self.assertFalse(result.was_corrected)

    def test_evaluate_stream_integration(self):
        random_metric_val = random.randint(100, 999)
        patch_data = f"diff --git a/stream.py b/stream.py\n# Value: {random_metric_val}"
        stream = io.BytesIO(patch_data.encode('utf-8'))
        
        result = self.evaluator.evaluate_stream(stream)
        
        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)

    def test_evaluate_with_autocorrect_integration(self):
        random_suffix = uuid.uuid4().hex[:6]
        patch_content = f"invalid_patch_content_{random_suffix}"
        
        result = self.evaluator.evaluate_with_autocorrect(patch_content)
        
        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertIsInstance(result.was_corrected, bool)

if __name__ == '__main__':
    unittest.main()