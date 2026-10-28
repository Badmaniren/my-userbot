import unittest
from unittest.mock import patch, MagicMock
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
        self.rand_repo = str(uuid.uuid4().hex)
        self.rand_patch = str(uuid.uuid4().hex)
        self.evaluator = PatchEvaluator(repo_path=self.rand_repo)

    def test_patch_evaluation_result_defaults(self):
        result = PatchEvaluationResult()
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.metrics, {})
        self.assertEqual(result.reasons, [])
        self.assertEqual(result.telemetry, {})
        self.assertFalse(result.was_corrected)

    def test_code_sanitizer_default(self):
        sanitizer = CodeSanitizer()
        content = uuid.uuid4().hex
        res_content, is_safe = sanitizer.sanitize(content)
        self.assertEqual(res_content, content)
        self.assertTrue(is_safe)
        self.assertEqual(sanitizer.get_reasons(), [])

    def test_code_validator_default(self):
        validator = CodeValidator()
        res = validator.validate(uuid.uuid4().hex)
        self.assertTrue(res.get("is_valid"))
        self.assertIn("metrics", res)

    def test_patch_verifier_default(self):
        verifier = PatchVerifier()
        self.assertTrue(verifier.verify(uuid.uuid4().hex))

    def test_patch_autocorrector_default(self):
        autocorrector = PatchAutocorrector()
        content = uuid.uuid4().hex
        res_content, success = autocorrector.correct(content)
        self.assertEqual(res_content, content)
        self.assertTrue(success)

    def test_system_telemetry_default(self):
        telemetry = SystemTelemetry()
        snap = telemetry.capture()
        self.assertIn("snapshot_id", snap)

    def test_patch_evaluator_init(self):
        path_str = str(uuid.uuid4().hex)
        evaluator = PatchEvaluator(repo_path=Path(path_str))
        self.assertEqual(evaluator.repo_path, path_str)

    def test_evaluate_success_flow(self):
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(1, 1000)

        with patch("skills.patch_evaluator.CodeSanitizer") as mock_sanitizer_cls, \
             patch("skills.patch_evaluator.CodeValidator") as mock_validator_cls, \
             patch("skills.patch_evaluator.PatchVerifier") as mock_verifier_cls:
            
            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.rand_patch, True)

            mock_validator = mock_validator_cls.return_value
            mock_validator.validate.return_value = {
                "is_valid": True,
                "metrics": {rand_metric_key: rand_metric_val}
            }

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify.return_value = True

            result = self.evaluator.evaluate(self.rand_patch, collect_telemetry=True)

            self.assertTrue(result.is_safe)
            self.assertTrue(result.is_valid)
            self.assertEqual(result.metrics.get(rand_metric_key), rand_metric_val)
            self.assertIn("snapshot_id", result.telemetry)

    def test_evaluate_unsafe_patch(self):
        rand_reason = uuid.uuid4().hex

        with patch("skills.patch_evaluator.CodeSanitizer") as mock_sanitizer_cls:
            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.rand_patch, False)
            mock_sanitizer.get_reasons.return_value = [rand_reason]

            result = self.evaluator.evaluate(self.rand_patch)

            self.assertFalse(result.is_safe)
            self.assertFalse(result.is_valid)
            self.assertIn(rand_reason, result.reasons)

    def test_evaluate_validator_exception_handling(self):
        with patch("skills.patch_evaluator.CodeSanitizer") as mock_sanitizer_cls, \
             patch("skills.patch_evaluator.CodeValidator") as mock_validator_cls, \
             patch("skills.patch_evaluator.PatchVerifier") as mock_verifier_cls:
            
            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.rand_patch, True)

            mock_validator = mock_validator_cls.return_value
            mock_validator.validate.side_effect = Exception(uuid.uuid4().hex)

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify.return_value = True

            result = self.evaluator.evaluate(self.rand_patch)

            self.assertTrue(result.is_safe)
            self.assertFalse(result.is_valid)

    def test_evaluate_verifier_exception_handling(self):
        with patch("skills.patch_evaluator.CodeSanitizer") as mock_sanitizer_cls, \
             patch("skills.patch_evaluator.CodeValidator") as mock_validator_cls, \
             patch("skills.patch_evaluator.PatchVerifier") as mock_verifier_cls:
            
            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.rand_patch, True)

            mock_validator = mock_validator_cls.return_value
            mock_validator.validate.return_value = {"is_valid": True, "metrics": {}}

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify.side_effect = Exception(uuid.uuid4().hex)

            result = self.evaluator.evaluate(self.rand_patch)

            self.assertTrue(result.is_safe)
            self.assertFalse(result.is_valid)

    def test_evaluate_raises_patch_evaluator_error(self):
        with patch("skills.patch_evaluator.CodeSanitizer") as mock_sanitizer_cls:
            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.side_effect = PatchEvaluatorError(uuid.uuid4().hex)

            with self.assertRaises(PatchEvaluatorError):
                self.evaluator.evaluate(self.rand_patch)

    def test_evaluate_with_autocorrect_unsafe(self):
        with patch("skills.patch_evaluator.CodeSanitizer") as mock_sanitizer_cls, \
             patch("skills.patch_evaluator.PatchAutocorrector") as mock_autocorrector_cls, \
             patch.object(self.evaluator, "evaluate") as mock_eval_method:
            
            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.rand_patch, False)

            mock_autocorrector = mock_autocorrector_cls.return_value
            corrected_patch = uuid.uuid4().hex
            mock_autocorrector.correct.return_value = (corrected_patch, True)

            mock_eval_result = PatchEvaluationResult(is_safe=True, is_valid=True)
            mock_eval_method.return_value = mock_eval_result

            res = self.evaluator.evaluate_with_autocorrect(self.rand_patch)

            mock_autocorrector.correct.assert_called_once_with(self.rand_patch)
            mock_eval_method.assert_called_once_with(corrected_patch)
            self.assertTrue(res.was_corrected)

    def test_evaluate_stream(self):
        rand_content = uuid.uuid4().hex
        stream = io.BytesIO(rand_content.encode('utf-8'))

        with patch.object(self.evaluator, "evaluate") as mock_eval:
            mock_eval.return_value = PatchEvaluationResult()
            res = self.evaluator.evaluate_stream(stream)
            mock_eval.assert_called_once_with(rand_content)
            self.assertIsInstance(res, PatchEvaluationResult)

    def test_functional_patch_evaluator_wrapper(self):
        target = uuid.uuid4().hex
        with patch("skills.patch_evaluator.PatchEvaluator.evaluate") as mock_eval:
            mock_eval.return_value = PatchEvaluationResult()
            res = patch_evaluator(self.rand_repo, self.rand_patch, target_file=target)
            mock_eval.assert_called_once_with(self.rand_patch, target_file=target)
            self.assertIsInstance(res, PatchEvaluationResult)