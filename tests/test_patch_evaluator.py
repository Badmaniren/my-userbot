import unittest
from unittest.mock import patch
import io
import uuid
import random
from pathlib import Path
from skills.patch_evaluator import (
    PatchEvaluatorError,
    PatchEvaluationResult,
    CodeSanitizer,
    CodeValidator,
    PatchVerifier,
    PatchAutocorrector,
    SystemTelemetry,
    PatchEvaluator,
    patch_evaluator
)

class TestPatchEvaluator(unittest.TestCase):
    def setUp(self):
        self.random_repo_path = Path(f"/tmp/{uuid.uuid4().hex}")
        self.random_patch_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n+{uuid.uuid4().hex}"
        self.evaluator = PatchEvaluator(repo_path=self.random_repo_path)

    def test_patch_evaluation_result_defaults(self):
        result = PatchEvaluationResult()
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.metrics, {})
        self.assertEqual(result.reasons, [])
        self.assertEqual(result.telemetry, {})
        self.assertFalse(result.was_corrected)

    def test_patch_evaluation_result_custom_values(self):
        custom_safe = random.choice([True, False])
        custom_valid = random.choice([True, False])
        custom_metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        custom_reasons = [uuid.uuid4().hex]
        custom_telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}
        custom_corrected = random.choice([True, False])

        result = PatchEvaluationResult(
            is_safe=custom_safe,
            is_valid=custom_valid,
            metrics=custom_metrics,
            reasons=custom_reasons,
            telemetry=custom_telemetry,
            was_corrected=custom_corrected
        )

        self.assertEqual(result.is_safe, custom_safe)
        self.assertEqual(result.is_valid, custom_valid)
        self.assertEqual(result.metrics, custom_metrics)
        self.assertEqual(result.reasons, custom_reasons)
        self.assertEqual(result.telemetry, custom_telemetry)
        self.assertEqual(result.was_corrected, custom_corrected)

    def test_evaluate_success(self):
        metric_key = uuid.uuid4().hex
        metric_value = random.randint(10, 500)
        snapshot_id = uuid.uuid4().hex

        with patch('skills.patch_evaluator.CodeSanitizer.sanitize', return_value=(self.random_patch_content, True)), \
             patch('skills.patch_evaluator.CodeValidator.validate', return_value={"is_valid": True, "metrics": {metric_key: metric_value}}), \
             patch('skills.patch_evaluator.PatchVerifier.verify', return_value=True), \
             patch('skills.patch_evaluator.SystemTelemetry.capture', return_value={"snapshot_id": snapshot_id}):

            result = self.evaluator.evaluate(self.random_patch_content, collect_telemetry=True)

            self.assertTrue(result.is_safe)
            self.assertTrue(result.is_valid)
            self.assertEqual(result.metrics.get(metric_key), metric_value)
            self.assertEqual(result.telemetry.get("snapshot_id"), snapshot_id)

    def test_evaluate_unsafe_patch(self):
        reason_msg = uuid.uuid4().hex

        with patch('skills.patch_evaluator.CodeSanitizer.sanitize', return_value=(self.random_patch_content, False)), \
             patch('skills.patch_evaluator.CodeSanitizer.get_reasons', return_value=[reason_msg]):

            result = self.evaluator.evaluate(self.random_patch_content)

            self.assertFalse(result.is_safe)
            self.assertFalse(result.is_valid)
            self.assertIn(reason_msg, result.reasons)

    def test_evaluate_invalid_validation(self):
        with patch('skills.patch_evaluator.CodeSanitizer.sanitize', return_value=(self.random_patch_content, True)), \
             patch('skills.patch_evaluator.CodeValidator.validate', return_value={"is_valid": False, "metrics": {}}), \
             patch('skills.patch_evaluator.PatchVerifier.verify', return_value=True):

            result = self.evaluator.evaluate(self.random_patch_content)

            self.assertTrue(result.is_safe)
            self.assertFalse(result.is_valid)

    def test_evaluate_invalid_verification(self):
        with patch('skills.patch_evaluator.CodeSanitizer.sanitize', return_value=(self.random_patch_content, True)), \
             patch('skills.patch_evaluator.CodeValidator.validate', return_value={"is_valid": True, "metrics": {}}), \
             patch('skills.patch_evaluator.PatchVerifier.verify', return_value=False):

            result = self.evaluator.evaluate(self.random_patch_content)

            self.assertTrue(result.is_safe)
            self.assertFalse(result.is_valid)

    def test_evaluate_raises_patch_evaluator_error(self):
        error_msg = uuid.uuid4().hex

        with patch('skills.patch_evaluator.CodeSanitizer.sanitize', side_effect=Exception(error_msg)):
            with self.assertRaises(PatchEvaluatorError) as ctx:
                self.evaluator.evaluate(self.random_patch_content)
            self.assertIn(error_msg, str(ctx.exception))

    def test_evaluate_with_autocorrect_triggered(self):
        corrected_content = f"corrected_{uuid.uuid4().hex}"

        with patch('skills.patch_evaluator.CodeSanitizer.sanitize', side_effect=[(self.random_patch_content, False), (corrected_content, True)]), \
             patch('skills.patch_evaluator.PatchAutocorrector.correct', return_value=(corrected_content, True)), \
             patch('skills.patch_evaluator.CodeValidator.validate', return_value={"is_valid": True, "metrics": {}}), \
             patch('skills.patch_evaluator.PatchVerifier.verify', return_value=True):

            result = self.evaluator.evaluate_with_autocorrect(self.random_patch_content)

            self.assertTrue(result.is_safe)
            self.assertTrue(result.was_corrected)

    def test_evaluate_stream(self):
        stream_data = self.random_patch_content.encode('utf-8')
        stream = io.BytesIO(stream_data)

        with patch.object(self.evaluator, 'evaluate') as mock_evaluate:
            mock_evaluate.return_value = PatchEvaluationResult(is_safe=True, is_valid=True)
            
            result = self.evaluator.evaluate_stream(stream)
            
            mock_evaluate.assert_called_once_with(self.random_patch_content)
            self.assertTrue(result.is_safe)

    def test_functional_helper_patch_evaluator(self):
        target_file_name = f"{uuid.uuid4().hex}.py"

        with patch.object(PatchEvaluator, 'evaluate') as mock_evaluate:
            mock_result = PatchEvaluationResult(is_safe=True, is_valid=True)
            mock_evaluate.return_value = mock_result

            res = patch_evaluator(
                repo_path=self.random_repo_path,
                patch_data=self.random_patch_content,
                target_file=target_file_name
            )

            mock_evaluate.assert_called_once_with(self.random_patch_content, target_file=target_file_name)
            self.assertEqual(res, mock_result)

if __name__ == '__main__':
    unittest.main()