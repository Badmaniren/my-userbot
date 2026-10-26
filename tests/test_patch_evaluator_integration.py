import unittest
import io
import uuid
import random
from pathlib import Path
from skills.patch_evaluator import (
    PatchEvaluator,
    PatchEvaluatorError,
    PatchEvaluationResult,
    patch_evaluator
)

class TestPatchEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.random_repo_name = f"test_repo_{uuid.uuid4().hex[:8]}"
        self.repo_path = Path(self.random_repo_name)
        self.repo_path.mkdir(exist_ok=True)
        self.evaluator = PatchEvaluator(repo_path=self.repo_path)

    def tearDown(self):
        if self.repo_path.exists():
            for item in self.repo_path.iterdir():
                try:
                    item.unlink()
                except Exception:
                    pass
            try:
                self.repo_path.rmdir()
            except Exception:
                pass

    def test_evaluate_standard_flow(self):
        unique_marker = uuid.uuid4().hex
        patch_content = f"print('{unique_marker}')\n"
        
        result = self.evaluator.evaluate(patch_content, collect_telemetry=True)

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)
        self.assertIn("snapshot_id", result.telemetry)

    def test_evaluate_stream_flow(self):
        unique_content = f"x = {random.randint(1, 100)}\n"
        stream = io.BytesIO(unique_content.encode('utf-8'))

        result = self.evaluator.evaluate_stream(stream)

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)

    def test_convenience_function(self):
        random_value = random.random()
        patch_data = f"val = {random_value}\n"

        result = patch_evaluator(repo_path=self.repo_path, patch_data=patch_data)
        
        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)

    def test_exception_handling_no_silent_swallowing(self):
        from unittest.mock import patch
        err_id = uuid.uuid4().hex
        with patch('skills.patch_evaluator.CodeSanitizer.sanitize', side_effect=ValueError(f"Forced error {err_id}")):
            with self.assertRaises(PatchEvaluatorError) as context:
                self.evaluator.evaluate("test content")

        self.assertIn("Forced error", str(context.exception))
        self.assertIsInstance(context.exception.__cause__, ValueError)

if __name__ == "__main__":
    unittest.main()