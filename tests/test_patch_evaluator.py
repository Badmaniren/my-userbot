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
    CodeAutocorrector,
    SystemTelemetry,
    PatchEvaluator,
    patch_evaluator
)

class TestPatchEvaluator(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = Path(f"/tmp/{uuid.uuid4().hex}")
        self.random_patch_content = f"print('{uuid.uuid4().hex}')\n"
        self.evaluator = PatchEvaluator(repo_path=self.random_repo_path)

    def test_patch_evaluation_result_defaults(self):
        result = PatchEvaluationResult()
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.metrics, {})
        self.assertEqual(result.reasons, [])
        self.assertEqual(result.telemetry, {})
        self.assertFalse(result.was_corrected)

    def test_patch_evaluation_result_custom(self):
        is_safe = random.choice([True, False])
        is_valid = random.choice([True, False])
        metrics_key = uuid.uuid4().hex
        metrics_val = random.randint(1, 100)
        metrics = {metrics_key: metrics_val}
        reason = uuid.uuid4().hex
        reasons = [reason]
        telemetry_key = uuid.uuid4().hex
        telemetry_val = uuid.uuid4().hex
        telemetry = {telemetry_key: telemetry_val}
        was_corrected = random.choice([True, False])

        result = PatchEvaluationResult(
            is_safe=is_safe,
            is_valid=is_valid,
            metrics=metrics,
            reasons=reasons,
            telemetry=telemetry,
            was_corrected=was_corrected
        )

        self.assertEqual(result.is_safe, is_safe)
        self.assertEqual(result.is_valid, is_valid)
        self.assertEqual(result.metrics[metrics_key], metrics_val)
        self.assertIn(reason, result.reasons)
        self.assertEqual(result.telemetry[telemetry_key], telemetry_val)
        self.assertEqual(result.was_corrected, was_corrected)

    def test_evaluator_init(self):
        self.assertEqual(self.evaluator.repo_path, str(self.random_repo_path))

    def test_evaluate_success(self):
        expected_metric_key = uuid.uuid4().hex
        expected_metric_val = random.randint(10, 500)

        with patch.object(CodeSanitizer, 'sanitize', return_value=(self.random_patch_content, True)) as mock_sanitize, \
             patch.object(CodeValidator, 'validate', return_value={"is_valid": True, "metrics": {expected_metric_key: expected_metric_val}}) as mock_validate, \
             patch.object(PatchVerifier, 'verify', return_value=True) as mock_verify:

            result = self.evaluator.evaluate(self.random_patch_content, collect_telemetry=False)

            mock_sanitize.assert_called_once_with(self.random_patch_content)
            mock_validate.assert_called_once_with(self.random_patch_content)
            mock_verify.assert_called_once_with(self.random_patch_content)

            self.assertTrue(result.is_safe)
            self.assertTrue(result.is_valid)
            self.assertEqual(result.metrics[expected_metric_key], expected_metric_val)
            self.assertEqual(result.telemetry, {})

    def test_evaluate_unsafe_patch(self):
        reason_msg = uuid.uuid4().hex
        with patch.object(CodeSanitizer, 'sanitize', return_value=(self.random_patch_content, False)) as mock_sanitize, \
             patch.object(CodeSanitizer, 'get_reasons', return_value=[reason_msg]) as mock_reasons:

            result = self.evaluator.evaluate(self.random_patch_content)

            mock_sanitize.assert_called_once_with(self.random_patch_content)
            mock_reasons.assert_called_once()

            self.assertFalse(result.is_safe)
            self.assertFalse(result.is_valid)
            self.assertIn(reason_msg, result.reasons)

    def test_evaluate_with_telemetry(self):
        snapshot_id = uuid.uuid4().hex
        with patch.object(CodeSanitizer, 'sanitize', return_value=(self.random_patch_content, True)), \
             patch.object(CodeValidator, 'validate', return_value={"is_valid": True, "metrics": {}}), \
             patch.object(PatchVerifier, 'verify', return_value=True), \
             patch.object(SystemTelemetry, 'capture', return_value={"snapshot_id": snapshot_id}) as mock_capture:

            result = self.evaluator.evaluate(self.random_patch_content, collect_telemetry=True)

            mock_capture.assert_called_once()
            self.assertEqual(result.telemetry.get("snapshot_id"), snapshot_id)

    def test_evaluate_exception_handling(self):
        error_msg = uuid.uuid4().hex
        with patch.object(CodeSanitizer, 'sanitize', side_effect=Exception(error_msg)):
            with self.assertRaises(PatchEvaluatorError) as ctx:
                self.evaluator.evaluate(self.random_patch_content)
            self.assertIn(error_msg, str(ctx.exception))

    def test_evaluate_with_autocorrect_not_needed(self):
        with patch.object(CodeSanitizer, 'sanitize', return_value=(self.random_patch_content, True)), \
             patch.object(CodeValidator, 'validate', return_value={"is_valid": True, "metrics": {}}), \
             patch.object(PatchVerifier, 'verify', return_value=True), \
             patch.object(PatchAutocorrector, 'correct') as mock_correct:

            result = self.evaluator.evaluate_with_autocorrect(self.random_patch_content)

            mock_correct.assert_not_called()
            self.assertFalse(result.was_corrected)
            self.assertTrue(result.is_safe)

    def test_evaluate_with_autocorrect_needed(self):
        corrected_content = f"# {uuid.uuid4().hex}\n" + self.random_patch_content
        with patch.object(CodeSanitizer, 'sanitize', side_effect=[(self.random_patch_content, False), (corrected_content, True)]), \
             patch.object(CodeAutocorrector, 'correct', return_value=(corrected_content, True)) as mock_correct, \
             patch.object(CodeValidator, 'validate', return_value={"is_valid": True, "metrics": {}}), \
             patch.object(PatchVerifier, 'verify', return_value=True):

            result = self.evaluator.evaluate_with_autocorrect(self.random_patch_content)

            mock_correct.assert_called_once_with(self.random_patch_content)
            self.assertTrue(result.was_corrected)
            self.assertTrue(result.is_safe)

    def test_evaluate_stream(self):
        stream_data = f"def {uuid.uuid4().hex}(): pass\n".encode('utf-8')
        stream = io.BytesIO(stream_data)

        with patch.object(PatchEvaluator, 'evaluate') as mock_evaluate:
            self.evaluator.evaluate_stream(stream)
            mock_evaluate.assert_called_once_with(stream_data.decode('utf-8'))

    def test_module_level_patch_evaluator_function(self):
        target_file_name = f"{uuid.uuid4().hex}.py"
        with patch.object(PatchEvaluator, 'evaluate', return_value=PatchEvaluationResult()) as mock_evaluate:
            res = patch_evaluator(
                repo_path=self.random_repo_path,
                patch_data=self.random_patch_content,
                target_file=target_file_name
            )
            mock_evaluate.assert_called_once_with(self.random_patch_content, target_file=target_file_name)
            self.assertIsInstance(res, PatchEvaluationResult)

if __name__ == '__main__':
    unittest.main()