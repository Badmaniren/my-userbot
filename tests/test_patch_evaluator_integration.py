import unittest
import io
import uuid
import random
from pathlib import Path

from skills.patch_evaluator import PatchEvaluator, patch_evaluator, PatchEvaluationResult, PatchEvaluatorError


class TestPatchEvaluatorIntegration(unittest.TestCase):

    def setUp(self):
        self.repo_path = Path(f"/tmp/test_repo_{uuid.uuid4().hex}")
        self.repo_path.mkdir(parents=True, exist_ok=True)
        self.evaluator = PatchEvaluator(repo_path=self.repo_path)

    def tearDown(self):
        if self.repo_path.exists():
            for item in self.repo_path.iterdir():
                if item.is_file():
                    item.unlink()
            self.repo_path.rmdir()

    def test_evaluate_basic_success(self):
        random_id = uuid.uuid4().hex
        patch_content = f"# Patch content {random_id}\nprint('Hello, Integration!')"
        
        result = self.evaluator.evaluate(patch_content, collect_telemetry=True)

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)
        self.assertIn("snapshot_id", result.telemetry)

    def test_evaluate_stream(self):
        random_str = uuid.uuid4().hex
        stream_content = f"def foo():\n    return '{random_str}'".encode('utf-8')
        stream = io.BytesIO(stream_content)

        result = self.evaluator.evaluate_stream(stream)

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)

    def test_evaluate_with_autocorrect(self):
        random_suffix = uuid.uuid4().hex[:8]
        patch_content = f"code_snippet_{random_suffix}"

        result = self.evaluator.evaluate_with_autocorrect(patch_content)

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)
        self.assertIsInstance(result.was_corrected, bool)

    def test_functional_helper(self):
        random_target = f"file_{uuid.uuid4().hex}.py"
        patch_data = f"# target: {(target_file_data := random_target)}\nx = {random.randint(1, 100)}"

        result = patch_evaluator(
            repo_path=self.repo_path,
            patch_data=patch_data,
            target_file=(target_target := target_file_data)
        )

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)


if __name__ == '__main__':
    unittest.main()