import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
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
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.repo_path = Path(f"/tmp/repo_{self.rand_suffix}")
        self.evaluator = PatchEvaluator(repo_path=self.repo_path)
        self.patch_content = f"diff --git a/{self.rand_suffix}.py b/{self.rand_suffix}.py\n+print('{self.rand_suffix}')"

    def test_patch_evaluation_result_defaults(self):
        res = PatchEvaluationResult()
        self.assertTrue(res.is_safe)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.metrics, {})
        self.assertEqual(res.reasons, [])
        self.assertEqual(res.telemetry, {})
        self.assertFalse(res.was_corrected)

    def test_patch_evaluation_result_custom(self):
        metric_key = f"key_{self.rand_suffix}"
        metric_val = random.randint(1, 100)
        reason_str = f"reason_{self.rand_suffix}"
        telemetry_key = f"tel_{self.rand_suffix}"
        
        res = PatchEvaluationResult(
            is_safe=False,
            is_valid=False,
            metrics={metric_key: metric_val},
            reasons=[reason_str],
            telemetry={telemetry_key: True},
            was_corrected=True
        )
        self.assertFalse(res.is_safe)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.metrics[metric_key], metric_val)
        self.assertIn(reason_str, res.reasons)
        self.assertTrue(res.telemetry[telemetry_key])
        self.assertTrue(res.was_corrected)

    def test_evaluate_success(self):
        metric_name = f"metric_{self.rand_suffix}"
        metric_value = random.randint(10, 500)

        with patch('skills.patch_evaluator.CodeSanitizer') as mock_sanitizer_cls, \
             patch('skills.patch_evaluator.CodeValidator') as mock_validator_cls, \
             patch('skills.patch_evaluator.PatchVerifier') as mock_verifier_cls:
            
            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.patch_content, True)

            mock_validator = mock_validator_cls.return_value
            mock_validator.validate.return_value = {
                "is_valid": True,
                "metrics": {metric_name: metric_value}
            }

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify.return_value = True

            result = self.evaluator.evaluate(self.patch_content, collect_telemetry=False)

            self.assertTrue(result.is_safe)
            self.assertTrue(result.is_valid)
            self.assertEqual(result.metrics.get(metric_name), metric_value)

    def test_evaluate_unsafe_patch(self):
        unsafe_reason = f"unsafe_reason_{self.rand_suffix}"

        with patch('skills.patch_evaluator.CodeSanitizer') as mock_sanitizer_cls:
            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.patch_content, False)
            mock_sanitizer.get_reasons.return_value = [unsafe_reason]

            result = self.evaluator.evaluate(self.patch_content)

            self.assertFalse(result.is_safe)
            self.assertFalse(result.is_valid)
            self.assertIn(unsafe_reason, result.reasons)

    def test_evaluate_with_telemetry(self):
        snapshot_id = f"snap_{self.rand_suffix}"

        with patch('skills.patch_evaluator.CodeSanitizer') as mock_sanitizer_cls, \
             patch('skills.patch_evaluator.CodeValidator') as mock_validator_cls, \
             patch('skills.patch_evaluator.PatchVerifier') as mock_verifier_cls, \
             patch('skills.patch_evaluator.SystemTelemetry') as mock_telemetry_cls:
            
            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.patch_content, True)

            mock_validator = mock_validator_cls.return_value
            mock_validator.validate.return_value = {"is_valid": True, "metrics": {}}

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify.return_value = True

            mock_telemetry = mock_telemetry_cls.return_value
            mock_telemetry.capture.return_value = {"snapshot_id": snapshot_id}

            result = self.evaluator.evaluate(self.patch_content, collect_telemetry=True)

            self.assertTrue(result.is_safe)
            self.assertEqual(result.telemetry.get("snapshot_id"), snapshot_id)

    def test_evaluate_exception_handling(self):
        err_msg = f"error_{self.rand_suffix}"

        with patch('skills.patch_evaluator.CodeSanitizer') as mock_sanitizer_cls:
            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.side_effect = RuntimeError(err_msg)

            with self.assertRaises(PatchEvaluatorError) as ctx:
                self.evaluator.evaluate(self.patch_content)
            self.assertIn(err_msg, str(ctx.exception))

    def test_evaluate_with_autocorrect_not_needed(self):
        with patch.object(self.evaluator, 'evaluate') as mock_eval:
            mock_result = PatchEvaluationResult(is_safe=True)
            mock_eval.return_value = mock_result

            with patch('skills.patch_evaluator.CodeSanitizer') as mock_sanitizer_cls:
                mock_sanitizer = mock_sanitizer_cls.return_value
                mock_sanitizer.sanitize.return_value = (self.patch_content, True)

                res = self.evaluator.evaluate_with_autocorrect(self.patch_content)
                self.assertFalse(res.was_corrected)
                mock_eval.assert_called_once_with(self.patch_content)

    def test_evaluate_with_autocorrect_applied(self):
        corrected_content = f"corrected_{self.patch_content}"

        with patch.object(self.evaluator, 'evaluate') as mock_eval:
            mock_result = PatchEvaluationResult(is_safe=True)
            mock_eval.return_value = mock_result

            with patch('skills.patch_evaluator.CodeSanitizer') as mock_sanitizer_cls, \
                 patch('skills.patch_evaluator.PatchAutocorrector') as mock_autocorr_cls:
                
                mock_sanitizer = mock_sanitizer_cls.return_value
                mock_sanitizer.sanitize.return_value = (self.patch_content, False)

                mock_autocorr = mock_autocorr_cls.return_value
                mock_autocorr.correct.return_value = (corrected_content, True)

                res = self.evaluator.evaluate_with_autocorrect(self.patch_content)
                self.assertTrue(res.was_corrected)
                mock_eval.assert_called_once_with(corrected_content)

    def test_evaluate_stream(self):
        stream_data = f"stream_data_{self.rand_suffix}".encode('utf-8')
        stream = io.BytesIO(stream_data)

        with patch.object(self.evaluator, 'evaluate') as mock_eval:
            mock_eval.return_value = PatchEvaluationResult()
            
            res = self.evaluator.evaluate_stream(stream)
            mock_eval.assert_called_once_with(f"stream_data_{self.rand_suffix}")
            self.assertIsInstance(res, PatchEvaluationResult)

    def test_module_level_patch_evaluator_function(self):
        target_file = f"file_{self.rand_suffix}.py"

        with patch('skills.patch_evaluator.PatchEvaluator.evaluate') as mock_eval:
            mock_result = PatchEvaluationResult(is_safe=True)
            mock_eval.return_value = mock_result

            res = patch_evaluator(repo_path=self.repo_path, patch_data=self.patch_content, target_file=target_file)
            mock_eval.assert_called_once_with(self.patch_content, target_file=target_file)
            self.assertEqual(res, mock_result)