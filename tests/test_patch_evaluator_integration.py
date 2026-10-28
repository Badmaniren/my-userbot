import unittest
import uuid
import random
import io
from pathlib import Path
from skills.patch_evaluator import PatchEvaluator, patch_evaluator, PatchEvaluationResult, PatchEvaluatorError
from skills.code_sanitizer import CodeSanitizer
from skills.code_validator import CodeValidator
from skills.patch_verifier import PatchVerifier
from skills.patch_autocorrector import PatchAutocorrector
from skills.system_telemetry import SystemTelemetry

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

    def test_evaluate_integration_real_flow(self):
        random_str = uuid.uuid4().hex
        patch_content = f"print('{random_str}')"
        
        result = self.evaluator.evaluate(patch_content, collect_telemetry=True)
        
        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)
        self.assertIn("snapshot_id", result.telemetry)

    def test_evaluate_stream_integration(self):
        random_str = uuid.uuid4().hex
        stream_data = io.BytesIO(f"def test_{random_str}(): pass".encode('utf-8'))
        
        result = self.evaluator.evaluate_stream(stream_data)
        
        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)

    def test_function_wrapper_integration(self):
        random_str = uuid.uuid4().hex
        patch_data = f"# {random_str}"
        
        result = patch_evaluator(repo_path=self.repo_path, patch_data=patch_data)
        
        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)

    def test_evaluate_with_autocorrect_integration(self):
        random_str = uuid.uuid4().hex
        patch_content = f"malicious_code_{random_str} = True"
        
        result = self.evaluator.evaluate_with_autocorrect(patch_content)
        
        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertIsInstance(result.was_corrected, bool)

if __name__ == "__main__":
    unittest.main()