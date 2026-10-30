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

class TestPatchEvaluatorInquisition(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/repo_{uuid.uuid4().hex}"
        self.rand_patch = f"def func_{uuid.uuid4().hex}(): pass\n"
        self.evaluator = PatchEvaluator(repo_path=self.rand_repo)

    def test_patch_evaluation_result_defaults(self):
        result = PatchEvaluationResult()
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.metrics, {})
        self.assertEqual(result.reasons, [])
        self.assertEqual(result.telemetry, {})
        self.assertFalse(result.was_corrected)

    def test_code_sanitizer_defaults(self):
        sanitizer = CodeSanitizer()
        content, is_safe = sanitizer.sanitize(self.rand_patch)
        self.assertEqual(content, self.rand_patch)
        self.assertTrue(is_safe)
        self.assertEqual(sanitizer.get_reasons(), [])

    def test_code_validator_defaults(self):
        validator = CodeValidator()
        res = validator.validate(self.rand_patch)
        self.assertTrue(res.get("is_valid"))
        self.assertEqual(res.get("metrics"), {})

    def test_patch_verifier_defaults(self):
        verifier = PatchVerifier()
        self.assertTrue(verifier.verify(self.rand_patch))

    def test_patch_autocorrector_defaults(self):
        autocorrector = PatchAutocorrector()
        content, corrected = autocorrector.correct(self.rand_patch)
        self.assertEqual(content, self.rand_patch)
        self.assertTrue(corrected)

    def test_system_telemetry_defaults(self):
        telemetry = SystemTelemetry()
        snap = telemetry.capture()
        self.assertIn("snapshot_id", snap)

    def test_evaluate_success_flow(self):
        result = self.evaluator.evaluate(self.rand_patch, collect_telemetry=True)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)
        self.assertIn("snapshot_id", result.telemetry)

    def test_evaluate_unsafe_sanitizer(self):
        rand_reason = uuid.uuid4().hex
        with patch("skills.patch_evaluator.CodeSanitizer.sanitize", return_value=(self.rand_patch, False)), \
             patch("skills.patch_evaluator.CodeSanitizer.get_reasons", return_value=[rand_reason]):
            
            result = self.evaluator.evaluate(self.rand_patch)
            self.assertFalse(result.is_safe)
            self.assertFalse(result.is_valid)
            self.assertIn(rand_reason, result.reasons)

    def test_evaluate_validator_exception_handling(self):
        with patch("skills.patch_evaluator.CodeValidator.validate", side_effect=Exception(uuid.uuid4().hex)):
            result = self.evaluator.evaluate(self.rand_patch)
            self.assertTrue(result.is_safe)
            self.assertFalse(result.is_valid)

    def test_evaluate_validator_custom_eval_error(self):
        rand_err_msg = uuid.uuid4().hex
        with patch("skills.patch_evaluator.CodeValidator.validate", side_effect=PatchEvaluatorError(rand_err_msg)):
            with self.assertRaises(PatchEvaluatorError) as ctx:
                self.evaluator.evaluate(self.rand_patch)
            self.assertEqual(str(ctx.exception), rand_err_msg)

    def test_evaluate_verifier_failure(self):
        with patch("skills.patch_evaluator.PatchVerifier.verify", return_value=False):
            result = self.evaluator.evaluate(self.rand_patch)
            self.assertTrue(result.is_safe)
            self.assertFalse(result.is_valid)

    def test_evaluate_verifier_exception(self):
        with patch("skills.patch_evaluator.PatchVerifier.verify", side_effect=Exception(uuid.uuid4().hex)):
            result = self.evaluator.evaluate(self.rand_patch)
            self.assertTrue(result.is_safe)
            self.assertFalse(result.is_valid)

    def test_evaluate_with_autocorrect_safe(self):
        with patch("skills.patch_evaluator.CodeSanitizer.sanitize", return_value=(self.rand_patch, True)):
            result = self.evaluator.evaluate_with_autocorrect(self.rand_patch)
            self.assertTrue(result.is_safe)
            self.assertFalse(result.was_corrected)

    def test_evaluate_with_autocorrect_unsafe(self):
        rand_corrected_patch = f"def func_{uuid.uuid4().hex}(): return True\n"
        with patch("skills.patch_evaluator.CodeSanitizer.sanitize", side_effect=[(self.rand_patch, False), (rand_corrected_patch, True)]), \
             patch("skills.patch_evaluator.PatchAutocorrector.correct", return_value=(rand_corrected_patch, True)):
            
            result = self.evaluator.evaluate_with_autocorrect(self.rand_patch)
            self.assertTrue(result.is_safe)
            self.assertTrue(result.was_corrected)

    def test_evaluate_stream(self):
        stream_data = self.rand_patch.encode('utf-8')
        stream = io.BytesIO(stream_data)
        result = self.evaluator.evaluate_stream(stream)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.is_valid)

    def test_functional_helper_patch_evaluator(self):
        res = patch_evaluator(repo_path=self.rand_repo, patch_data=self.rand_patch, target_file=f"{uuid.uuid4().hex}.py")
        self.assertTrue(res.is_safe)
        self.assertTrue(res.is_valid)

    def test_global_exception_translator(self):
        with patch("skills.patch_evaluator.CodeSanitizer.sanitize", side_effect=RuntimeError(uuid.uuid4().hex)):
            with self.assertRaises(PatchEvaluatorError):
                self.evaluator.evaluate(self.rand_patch)