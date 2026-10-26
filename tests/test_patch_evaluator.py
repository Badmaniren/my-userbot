import unittest
from unittest.mock import patch
import io
import uuid
import random
from pathlib import Path

from skills.patch_evaluator import (
    PatchEvaluatorError,
    PatchEvaluationResult,
    PatchEvaluator,
    patch_evaluator
)

class TestPatchEvaluator(unittest.TestCase):

    def setUp(self):
        self.random_repo = f"/tmp/{uuid.uuid4().hex}"
        self.evaluator = PatchEvaluator(repo_path=self.random_repo)

    def test_evaluation_result_defaults(self):
        result = PatchEvaluationResult()
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.metrics, {})
        self.assertEqual(result.reasons, [])
        self.assertEqual(result.telemetry, {})
        self.assertFalse(result.was_corrected)

    def test_evaluate_success_path(self):
        patch_text = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n+{uuid.uuid4().hex}"

        with patch('skills.patch_evaluator.CodeSanitizer.sanitize') as mock_sanitize, \
             patch('skills.patch_evaluator.CodeValidator.validate') as mock_validate, \
             patch('skills.patch_evaluator.PatchVerifier.verify') as mock_verify:
            
            mock_sanitize.return_value = (patch_text, True)
            expected_metric_key = uuid.uuid4().hex
            expected_metric_val = random.randint(1, 1000)
            mock_validate.return_value = {"is_valid": True, "metrics": {expected_metric_key: expected_metric_val}}
            mock_verify.return_value = True

            result = self.evaluator.evaluate(patch_text, collect_telemetry=False)

            self.assertTrue(result.is_safe)
            self.assertTrue(result.is_valid)
            self.assertIn(expected_metric_key, result.metrics)
            self.assertEqual(result.metrics[expected_metric_key], expected_metric_val)

    def test_evaluate_unsafe_patch(self):
        patch_text = f"malicious_payload_{uuid.uuid4().hex}"
        reason_msg = f"danger_{uuid.uuid4().hex}"

        with patch('skills.patch_evaluator.CodeSanitizer.sanitize') as mock_sanitize, \
             patch('skills.patch_evaluator.CodeSanitizer.get_reasons') as mock_get_reasons:
            
            mock_sanitize.return_value = (patch_text, False)
            mock_get_reasons.return_value = [reason_msg]

            result = self.evaluator.evaluate(patch_text)

            self.assertFalse(result.is_safe)
            self.assertFalse(result.is_valid)
            self.assertIn(reason_msg, result.reasons)

    def test_evaluate_with_telemetry(self):
        patch_text = f"content_{uuid.uuid4().hex}"
        snapshot_id = uuid.uuid4().hex

        with patch('skills.patch_evaluator.CodeSanitizer.sanitize') as mock_sanitize, \
             patch('skills.patch_evaluator.CodeValidator.validate') as mock_validate, \
             patch('skills.patch_evaluator.PatchVerifier.verify') as mock_verify, \
             patch('skills.patch_evaluator.SystemTelemetry.capture') as mock_telemetry:

            mock_sanitize.return_value = (patch_text, True)
            mock_validate.return_value = {"is_valid": True, "metrics": {}}
            mock_verify.return_value = True
            mock_telemetry.return_value = {"snapshot_id": snapshot_id}

            result = self.evaluator.evaluate(patch_text, collect_telemetry=True)

            self.assertTrue(result.is_safe)
            self.assertEqual(result.telemetry.get("snapshot_id"), snapshot_id)

    def test_evaluate_with_autocorrect_triggered(self):
        initial_patch = f"bad_code_{uuid.uuid4().hex}"
        corrected_patch = f"good_code_{uuid.uuid4().hex}"

        with patch('skills.patch_evaluator.CodeSanitizer.sanitize') as mock_sanitize, \
             patch('skills.patch_evaluator.PatchAutocorrector.correct') as mock_correct, \
             patch('skills.patch_evaluator.CodeValidator.validate') as mock_validate, \
             patch('skills.patch_evaluator.PatchVerifier.verify') as mock_verify:

            mock_sanitize.side_effect = [(initial_patch, False), (corrected_patch, True)]
            mock_correct.return_value = (corrected_patch, True)
            mock_validate.return_value = {"is_valid": True, "metrics": {}}
            mock_verify.return_value = True

            result = self.evaluator.evaluate_with_autocorrect(initial_patch)

            self.assertTrue(result.was_corrected)
            self.assertTrue(result.is_safe)

    def test_evaluate_stream(self):
        random_payload = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(random_payload)

        with patch.object(PatchEvaluator, 'evaluate') as mock_evaluate:
            expected_res = PatchEvaluationResult(is_safe=True, is_valid=True)
            mock_evaluate.return_value = expected_res

            res = self.evaluator.evaluate_stream(stream)
            self.assertEqual(res, expected_res)
            mock_evaluate.assert_called_once_with(random_payload.decode('utf-8'))

    def test_patch_evaluator_functional_wrapper(self):
        patch_data = f"data_{uuid.uuid4().hex}"
        target_file = f"src/{uuid.uuid4().hex}.py"

        with patch('skills.patch_evaluator.PatchEvaluator.evaluate') as mock_evaluate:
            expected_res = PatchEvaluationResult(is_safe=True)
            mock_evaluate.return_value = expected_res

            res = patch_evaluator(repo_path=self.random_repo, patch_data=patch_data, target_file=target_file)
            self.assertEqual(res, expected_res)
            mock_evaluate.assert_called_once_with(patch_data, target_file=target_file)

    def test_exception_wrapping(self):
        patch_text = f"crash_patch_{uuid.uuid4().hex}"
        err_msg = f"error_{uuid.uuid4().hex}"

        with patch('skills.patch_evaluator.CodeSanitizer.sanitize', side_effect=Exception(err_msg)):
            with self.assertRaises(PatchEvaluatorError) as ctx:
                self.evaluator.evaluate(patch_text)
            self.assertIn(err_msg, str(ctx.exception))