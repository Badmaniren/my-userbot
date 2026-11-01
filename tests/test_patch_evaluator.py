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
        self.rand_repo = str(Path(uuid.uuid4().hex, uuid.uuid4().hex))
        self.rand_patch_content = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py\n+print('{uuid.uuid4().hex}')"
        self.rand_target = f"{uuid.uuid4().hex}.py"

    def test_patch_evaluation_result_defaults(self):
        res = PatchEvaluationResult()
        self.assertTrue(res.is_safe)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.metrics, {})
        self.assertEqual(res.reasons, [])
        self.assertEqual(res.telemetry, {})
        self.assertFalse(res.was_corrected)

    def test_patch_evaluation_result_custom(self):
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(1, 100)
        rand_reason = uuid.uuid4().hex
        rand_tele_key = uuid.uuid4().hex
        
        res = PatchEvaluationResult(
            is_safe=False,
            is_valid=False,
            metrics={rand_metric_key: rand_metric_val},
            reasons=[rand_reason],
            telemetry={rand_tele_key: True},
            was_corrected=True
        )
        self.assertFalse(res.is_safe)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.metrics[rand_metric_key], rand_metric_val)
        self.assertIn(rand_reason, res.reasons)
        self.assertTrue(res.telemetry[rand_tele_key])
        self.assertTrue(res.was_corrected)

    def test_code_sanitizer_default(self):
        sanitizer = CodeSanitizer()
        content, is_safe = sanitizer.sanitize(self.rand_patch_content)
        self.assertEqual(content, self.rand_patch_content)
        self.assertTrue(is_safe)
        self.assertEqual(sanitizer.get_reasons(), [])

    def test_code_validator_default(self):
        validator = CodeValidator()
        res = validator.validate(self.rand_patch_content)
        self.assertTrue(res.get("is_valid"))
        self.assertIn("metrics", res)

    def test_patch_verifier_default(self):
        verifier = PatchVerifier()
        self.assertTrue(verifier.verify(self.rand_patch_content))

    def test_patch_autocorrector_default(self):
        corrector = PatchAutocorrector()
        content, corrected = corrector.correct(self.rand_patch_content)
        self.assertEqual(content, self.rand_patch_content)
        self.assertTrue(corrected)

    def test_system_telemetry_default(self):
        telemetry = SystemTelemetry()
        data = telemetry.capture()
        self.assertIn("snapshot_id", data)

    def test_patch_evaluator_evaluate_success(self):
        rand_metric_name = uuid.uuid4().hex
        rand_metric_value = random.randint(500, 1000)

        with patch("skills.patch_evaluator.CodeSanitizer") as mock_sanitizer_cls, \
             patch("skills.patch_evaluator.CodeValidator") as mock_validator_cls, \
             patch("skills.patch_evaluator.PatchVerifier") as mock_verifier_cls:

            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.rand_patch_content, True)

            mock_validator = mock_validator_cls.return_value
            mock_validator.validate.return_value = {
                "is_valid": True,
                "metrics": {rand_metric_name: rand_metric_value}
            }

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify.return_value = True

            evaluator = PatchEvaluator(self.rand_repo)
            result = evaluator.evaluate(self.rand_patch_content, collect_telemetry=False, target_file=self.rand_target)

            self.assertTrue(result.is_safe)
            self.assertTrue(result.is_valid)
            self.assertEqual(result.metrics[rand_metric_name], rand_metric_value)

    def test_patch_evaluator_evaluate_unsafe(self):
        rand_reason = uuid.uuid4().hex

        with patch("skills.patch_evaluator.CodeSanitizer") as mock_sanitizer_cls:
            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.rand_patch_content, False)
            mock_sanitizer.get_reasons.return_value = [rand_reason]

            evaluator = PatchEvaluator(self.rand_repo)
            result = evaluator.evaluate(self.rand_patch_content)

            self.assertFalse(result.is_safe)
            self.assertFalse(result.is_valid)
            self.assertIn(rand_reason, result.reasons)

    def test_patch_evaluator_evaluate_with_telemetry(self):
        rand_snapshot = uuid.uuid4().hex

        with patch("skills.patch_evaluator.CodeSanitizer") as mock_sanitizer_cls, \
             patch("skills.patch_evaluator.CodeValidator") as mock_validator_cls, \
             patch("skills.patch_evaluator.PatchVerifier") as mock_verifier_cls, \
             patch("skills.patch_evaluator.SystemTelemetry") as mock_telemetry_cls:

            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.rand_patch_content, True)

            mock_validator = mock_validator_cls.return_value
            mock_validator.validate.return_value = {"is_valid": True, "metrics": {}}

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify.return_value = True

            mock_telemetry = mock_telemetry_cls.return_value
            mock_telemetry.capture.return_value = {"snapshot_id": rand_snapshot}

            evaluator = PatchEvaluator(self.rand_repo)
            result = evaluator.evaluate(self.rand_patch_content, collect_telemetry=True)

            self.assertTrue(result.is_safe)
            self.assertEqual(result.telemetry.get("snapshot_id"), rand_snapshot)

    def test_patch_evaluator_validator_exception_handled(self):
        with patch("skills.patch_evaluator.CodeSanitizer") as mock_sanitizer_cls, \
             patch("skills.patch_evaluator.CodeValidator") as mock_validator_cls, \
             patch("skills.patch_evaluator.PatchVerifier") as mock_verifier_cls:

            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.rand_patch_content, True)

            mock_validator = mock_validator_cls.return_value
            mock_validator.validate.side_effect = RuntimeError(uuid.uuid4().hex)

            mock_verifier = mock_verifier_cls.return_value
            mock_verifier.verify.return_value = True

            evaluator = PatchEvaluator(self.rand_repo)
            result = evaluator.evaluate(self.rand_patch_content)

            self.assertTrue(result.is_safe)
            self.assertTrue(result.is_valid)

    def test_patch_evaluator_validator_raises_evaluator_error(self):
        rand_err_msg = uuid.uuid4().hex

        with patch("skills.patch_evaluator.CodeSanitizer") as mock_sanitizer_cls, \
             patch("skills.patch_evaluator.CodeValidator") as mock_validator_cls:

            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.rand_patch_content, True)

            mock_validator = mock_validator_cls.return_value
            mock_validator.validate.side_effect = PatchEvaluatorError(rand_err_msg)

            evaluator = PatchEvaluator(self.rand_repo)
            with self.assertRaises(PatchEvaluatorError) as ctx:
                evaluator.evaluate(self.rand_patch_content)
            self.assertIn(rand_err_msg, str(ctx.exception))

    def test_patch_evaluator_evaluate_with_autocorrect_unsafe(self):
        with patch("skills.patch_evaluator.CodeSanitizer") as mock_sanitizer_cls, \
             patch("skills.patch_evaluator.PatchAutocorrector") as mock_autocorrect_cls, \
             patch.object(PatchEvaluator, "evaluate") as mock_evaluate:

            mock_sanitizer = mock_sanitizer_cls.return_value
            mock_sanitizer.sanitize.return_value = (self.rand_patch_content, False)

            mock_autocorrect = mock_autocorrect_cls.return_value
            rand_corrected_content = f"corrected_{uuid.uuid4().hex}"
            mock_autocorrect.correct.return_value = (rand_corrected_content, True)

            mock_eval_result = PatchEvaluationResult(was_corrected=False)
            mock_evaluate.return_value = mock_eval_result

            evaluator = PatchEvaluator(self.rand_repo)
            res = evaluator.evaluate_with_autocorrect(self.rand_patch_content)

            mock_autocorrect.correct.assert_called_once_with(self.rand_patch_content)
            mock_evaluate.assert_called_once_with(rand_corrected_content)
            self.assertTrue(res.was_corrected)

    def test_patch_evaluator_evaluate_stream(self):
        rand_stream_data = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(rand_stream_data)

        with patch.object(PatchEvaluator, "evaluate") as mock_evaluate:
            mock_evaluate.return_value = PatchEvaluationResult()

            evaluator = PatchEvaluator(self.rand_repo)
            evaluator.evaluate_stream(stream)

            mock_evaluate.assert_called_once_with(rand_stream_data.decode('utf-8'))

    def test_global_patch_evaluator_function(self):
        with patch("skills.patch_evaluator.PatchEvaluator.evaluate") as mock_evaluate:
            mock_evaluate.return_value = PatchEvaluationResult()

            res = patch_evaluator(self.rand_repo, self.rand_patch_content, target_file=self.rand_target)
            self.assertIsInstance(res, PatchEvaluationResult)
            mock_evaluate.assert_called_once_with(self.rand_patch_content, target_file=self.rand_target)