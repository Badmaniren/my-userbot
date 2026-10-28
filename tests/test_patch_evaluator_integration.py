import unittest
import uuid
import random
import io
from pathlib import Path

from skills.patch_evaluator import (
    PatchEvaluator,
    PatchEvaluationResult,
    PatchEvaluatorError,
    CodeSanitizer,
    CodeValidator,
    PatchVerifier,
    PatchAutocorrector,
    SystemTelemetry,
    patch_evaluator
)

class TestPatchEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.repo_path = Path(f"./test_repo_{uuid.uuid4().hex}")
        self.repo_path.mkdir(parents=True, exist_ok=True)
        self.evaluator = PatchEvaluator(repo_path=self.repo_path)

    def tearDown(self):
        if self.repo_path.exists():
            for p in self.repo_path.glob("*"):
                p.unlink()
            self.repo_path.rmdir()

    def test_evaluate_success_integration(self):
        random_id = uuid.uuid4().hex
        patch_content = f"# Patch content {random_id}\nprint('Hello, Integration!')"

        result = self.evaluator.evaluate(patch_content, collect_telemetry=True)

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)
        self.assertIn("snapshot_id", result.telemetry)
        self.assertEqual(result.telemetry["snapshot_id"], "dummy_snapshot")

    def test_evaluate_stream_integration(self):
        random_suffix = uuid.uuid4().hex
        stream_data = f"def test_func_{random_suffix}(): pass".encode('utf-8')
        stream = io.BytesIO(stream_data)

        result = self.evaluator.evaluate_stream(stream)

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)

    def test_evaluate_with_autocorrect_integration(self):
        random_prefix = uuid.uuid4().hex
        patch_content = f"malicious_code_marker_{random_prefix}"

        result = self.evaluator.evaluate_with_autocorrect(patch_content)

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(isinstance(result.was_corrected, bool))

    def test_functional_wrapper_integration(self):
        random_tag = uuid.uuid4().int
        patch_content = f"# Tag: {random_tag}"

        result = patch_evaluator(
            repo_path=self.repo_path,
            patch_data=patch_content,
            target_file=f"file_{random_tag}.py"
        )

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)

if __name__ == "__main__":
    unittest.main()