import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
from pathlib import Path

from skills.patch_evaluator import (
    PatchEvaluator,
    PatchEvaluatorError,
    PatchEvaluationResult
)

class TestPatchEvaluatorInquisitor(unittest.TestCase):

    def setUp(self):
        self.evaluator_id = uuid.uuid4().hex
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.patch_content = f"def func_{uuid.uuid4().hex[:8]}():\n    return '{uuid.uuid4().hex}'"
        self.evaluator = PatchEvaluator(repo_path=self.repo_path)

    def test_init_sets_properties(self):
        random_path = f"/var/repo/{uuid.uuid4().hex}"
        evaluator = PatchEvaluator(repo_path=random_path)
        self.assertEqual(evaluator.repo_path, random_path)

    def test_evaluate_patch_success(self):
        expected_score = round(random.uniform(0.5, 1.0), 2)
        random_metric = uuid.uuid4().hex

        with patch('skills.patch_evaluator.CodeSanitizer') as mock_sanitizer_cls, \
             patch('skills.patch_evaluator.CodeValidator') as mock_validator_cls, \
             patch('skills.patch_evaluator.PatchVerifier') as mock_verifier_cls:
            
            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.patch_content, True)

            mock_validator = mock_validator_cls.return_value
            mock_validator.validate.return_value = {"is_valid": True, "metrics": {random_metric: expected_score}}

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify.return_value = True

            result = self.evaluator.evaluate(self.patch_content)

            self.assertIsInstance(result, PatchEvaluationResult)
            self.assertTrue(result.is_safe)
            self.assertTrue(result.is_valid)
            self.assertEqual(result.metrics[random_metric], expected_score)
            mock_sanitizer.sanitize.assert_called_once_with(self.patch_content)

    def test_evaluate_patch_sanitization_failure(self):
        error_msg = uuid.uuid4().hex
        with patch('skills.patch_evaluator.CodeSanitizer') as mock_sanitizer_cls:
            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.side_effect = Exception(error_msg)

            with self.assertRaises(PatchEvaluatorError) as ctx:
                self.evaluator.evaluate(self.patch_content)
            
            self.assertIn(error_msg, str(ctx.exception))

    def test_evaluate_patch_unsafe_code(self):
        random_reason = uuid.uuid4().hex
        with patch('skills.patch_evaluator.CodeSanitizer') as mock_sanitizer_cls:
            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.patch_content, False)
            mock_sanitizer.get_reasons.return_value = [random_reason]

            result = self.evaluator.evaluate(self.patch_content)

            self.assertFalse(result.is_safe)
            self.assertIn(random_reason, result.reasons)

    def test_evaluate_with_telemetry_snapshot(self):
        snapshot_id = uuid.uuid4().hex
        mock_telemetry = MagicMock()
        mock_telemetry.capture.return_value = {"snapshot_id": snapshot_id}

        with patch('skills.patch_evaluator.SystemTelemetry', return_value=mock_telemetry), \
             patch('skills.patch_evaluator.CodeSanitizer') as mock_sanitizer_cls, \
             patch('skills.patch_evaluator.CodeValidator') as mock_validator_cls, \
             patch('skills.patch_evaluator.PatchVerifier') as mock_verifier_cls:

            mock_sanitizer_cls.return_value.sanitize.return_value = (self.patch_content, True)
            mock_validator_cls.return_value.validate.return_value = {"is_valid": True, "metrics": {}}
            mock_verifier_cls.return_value.verify.return_value = True

            result = self.evaluator.evaluate(self.patch_content, collect_telemetry=True)
            self.assertEqual(result.telemetry["snapshot_id"], snapshot_id)

    def test_patch_autocorrection_trigger(self):
        autocorrect_msg = uuid.uuid4().hex
        with patch('skills.patch_evaluator.CodeSanitizer') as mock_sanitizer_cls, \
             patch('skills.patch_evaluator.PatchAutocorrector') as mock_autocorrect_cls:

            mock_sanitizer_cls.return_value.sanitize.return_value = (self.patch_content, False)
            mock_autocorrect_cls.return_value.correct.return_value = (self.patch_content, True)

            result = self.evaluator.evaluate_with_autocorrect(self.patch_content)
            self.assertTrue(result.was_corrected)
            mock_autocorrect_cls.return_value.correct.assert_called_once()

    def test_stream_patch_evaluation_from_io(self):
        random_bytes = f"print('{uuid.uuid4().hex}')".encode('utf-8')
        stream = io.BytesIO(random_bytes)

        with patch('skills.patch_evaluator.CodeSanitizer') as mock_sanitizer_cls, \
             patch('skills.patch_evaluator.CodeValidator') as mock_validator_cls, \
             patch('skills.patch_evaluator.PatchVerifier') as mock_verifier_cls:

            mock_sanitizer_cls.return_value.sanitize.return_value = (random_bytes.decode('utf-8'), True)
            mock_validator_cls.return_value.validate.return_value = {"is_valid": True, "metrics": {}}
            mock_verifier_cls.return_value.verify.return_value = True

            result = self.evaluator.evaluate_stream(stream)
            self.assertTrue(result.is_valid)

if __name__ == '__main__':
    unittest.main()