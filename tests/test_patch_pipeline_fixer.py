import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io


class TestPatchPipelineFixer(unittest.TestCase):
    def setUp(self):
        self.random_token = uuid.uuid4().hex
        self.repo_path = f"/tmp/repo_{self.random_token}"
        self.target_file = f"src/module_{uuid.uuid4().hex[:8]}.py"
        self.patch_content = (
            f"--- a/{self.target_file}\n"
            f"+++ b/{self.target_file}\n"
            f"@@ -1,3 +1,4 @@\n"
            f"+# Patch ID: {self.random_token}\n"
            f" def execute():\n"
            f"-    pass\n"
            f"+    return '{self.random_token}'\n"
        )

    def _get_module(self):
        try:
            import skills.patch_pipeline_fixer as fixer_mod
        except ImportError:
            import patch_pipeline_fixer as fixer_mod
        return fixer_mod

    def test_module_exports_and_composition_structure(self):
        mod = self._get_module()
        self.assertTrue(
            hasattr(mod, "PatchPipelineFixer") or hasattr(mod, "fix_patch_pipeline") or hasattr(mod, "apply_safe_patch"),
            "Module must provide PatchPipelineFixer class or main pipeline function"
        )
        self.assertTrue(
            hasattr(mod, "PatchPipelineFixerError"),
            "Module must define PatchPipelineFixerError for strict error handling"
        )

    def test_successful_patch_evaluation_and_check(self):
        mod = self._get_module()
        fixer_cls = getattr(mod, "PatchPipelineFixer", None)
        fixer_fn = getattr(mod, "fix_patch_pipeline", None) or getattr(mod, "apply_safe_patch", None)

        expected_metric_val = random.randint(10, 100)
        eval_result_mock = MagicMock()
        eval_result_mock.is_safe = True
        eval_result_mock.is_valid = True
        eval_result_mock.reasons = []
        eval_result_mock.metrics = {"complexity": expected_metric_val, "token": self.random_token}
        eval_result_mock.was_corrected = False

        checker_result_mock = {
            "success": True,
            "status": "passed",
            "diagnostics": {"token": self.random_token},
            "applied": True
        }

        with patch("skills.patch_evaluator.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_checker.PatchChecker") as mock_checker_cls:

            evaluator_inst = MagicMock()
            evaluator_inst.evaluate.return_value = eval_result_mock
            evaluator_inst.evaluate_with_autocorrect.return_value = eval_result_mock
            mock_evaluator_cls.return_value = evaluator_inst

            checker_inst = MagicMock()
            checker_inst.check_patch.return_value = checker_result_mock
            mock_checker_cls.return_value = checker_inst

            if fixer_cls:
                instance = fixer_cls(repo_path=self.repo_path)
                if hasattr(instance, "process_patch"):
                    res = instance.process_patch(patch_content=self.patch_content, target_file=self.target_file)
                elif hasattr(instance, "run"):
                    res = instance.run(patch_content=self.patch_content, target_file=self.target_file)
                elif hasattr(instance, "fix_and_apply"):
                    res = instance.fix_and_apply(patch_content=self.patch_content, target_file=self.target_file)
                else:
                    res = instance.apply_patch(patch_content=self.patch_content, target_file=self.target_file)
            else:
                res = fixer_fn(
                    repo_path=self.repo_path,
                    patch_content=self.patch_content,
                    target_file=self.target_file
                )

            self.assertIsNotNone(res)
            if isinstance(res, dict):
                self.assertTrue(res.get("success", False) or res.get("is_safe", False) or res.get("applied", False))
                if "metrics" in res:
                    self.assertEqual(res["metrics"]["complexity"], expected_metric_val)
            else:
                self.assertTrue(getattr(res, "is_safe", False) or getattr(res, "success", False))

            self.assertTrue(evaluator_inst.evaluate.called or evaluator_inst.evaluate_with_autocorrect.called)
            self.assertTrue(checker_inst.check_patch.called or checker_inst.check.called)

    def test_unsafe_patch_rejection_without_swallowing_errors(self):
        mod = self._get_module()
        fixer_cls = getattr(mod, "PatchPipelineFixer", None)
        fixer_fn = getattr(mod, "fix_patch_pipeline", None) or getattr(mod, "apply_safe_patch", None)
        error_cls = getattr(mod, "PatchPipelineFixerError")

        rejection_reason = f"Security Violation: {uuid.uuid4().hex}"
        eval_result_mock = MagicMock()
        eval_result_mock.is_safe = False
        eval_result_mock.is_valid = False
        eval_result_mock.reasons = [rejection_reason]
        eval_result_mock.metrics = {}
        eval_result_mock.was_corrected = False

        with patch("skills.patch_evaluator.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_checker.PatchChecker") as mock_checker_cls:

            evaluator_inst = MagicMock()
            evaluator_inst.evaluate.return_value = eval_result_mock
            evaluator_inst.evaluate_with_autocorrect.return_value = eval_result_mock
            mock_evaluator_cls.return_value = evaluator_inst

            checker_inst = MagicMock()
            mock_checker_cls.return_value = checker_inst

            if fixer_cls:
                instance = fixer_cls(repo_path=self.repo_path)
                method = (
                    getattr(instance, "process_patch", None) or
                    getattr(instance, "run", None) or
                    getattr(instance, "fix_and_apply", None) or
                    getattr(instance, "apply_patch", None)
                )
                try:
                    res = method(patch_content=self.patch_content, target_file=self.target_file)
                    if isinstance(res, dict):
                        self.assertFalse(res.get("success", True) and res.get("is_safe", True))
                        self.assertIn(rejection_reason, str(res.get("reasons", [])) + str(res.get("errors", [])))
                    else:
                        self.assertFalse(getattr(res, "is_safe", True))
                except error_cls as exc:
                    self.assertIn(rejection_reason, str(exc))
            else:
                try:
                    res = fixer_fn(
                        repo_path=self.repo_path,
                        patch_content=self.patch_content,
                        target_file=self.target_file
                    )
                    self.assertFalse(res.get("success", True) and res.get("is_safe", True))
                except error_cls as exc:
                    self.assertIn(rejection_reason, str(exc))

            self.assertFalse(checker_inst.check_patch.called and checker_inst.check_patch.call_count > 1)

    def test_autocorrect_flow_when_initial_evaluation_fails(self):
        mod = self._get_module()
        fixer_cls = getattr(mod, "PatchPipelineFixer", None)
        fixer_fn = getattr(mod, "fix_patch_pipeline", None) or getattr(mod, "apply_safe_patch", None)

        corrected_patch_token = f"corrected_{uuid.uuid4().hex}"
        corrected_eval_result = MagicMock()
        corrected_eval_result.is_safe = True
        corrected_eval_result.is_valid = True
        corrected_eval_result.was_corrected = True
        corrected_eval_result.reasons = ["Auto-corrected syntax"]
        corrected_eval_result.metrics = {"token": corrected_patch_token}

        checker_result = {
            "success": True,
            "status": "passed",
            "token": corrected_patch_token
        }

        with patch("skills.patch_evaluator.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_checker.PatchChecker") as mock_checker_cls:

            evaluator_inst = MagicMock()
            evaluator_inst.evaluate.return_value = MagicMock(is_safe=False, is_valid=False, reasons=["syntax error"])
            evaluator_inst.evaluate_with_autocorrect.return_value = corrected_eval_result
            mock_evaluator_cls.return_value = evaluator_inst

            checker_inst = MagicMock()
            checker_inst.check_patch.return_value = checker_result
            mock_checker_cls.return_value = checker_inst

            if fixer_cls:
                instance = fixer_cls(repo_path=self.repo_path)
                method = (
                    getattr(instance, "process_patch", None) or
                    getattr(instance, "run", None) or
                    getattr(instance, "fix_and_apply", None) or
                    getattr(instance, "apply_patch", None)
                )
                res = method(patch_content=self.patch_content, target_file=self.target_file)
            else:
                res = fixer_fn(repo_path=self.repo_path, patch_content=self.patch_content, target_file=self.target_file)

            if isinstance(res, dict):
                self.assertTrue(res.get("success", False) or res.get("is_safe", False))
                self.assertTrue(res.get("was_corrected", False) or "corrected" in str(res))
            else:
                self.assertTrue(getattr(res, "was_corrected", False) or getattr(res, "is_safe", False))

    def test_evaluator_exception_propagation_or_wrapping(self):
        mod = self._get_module()
        fixer_cls = getattr(mod, "PatchPipelineFixer", None)
        fixer_fn = getattr(mod, "fix_patch_pipeline", None) or getattr(mod, "apply_safe_patch", None)
        fixer_error_cls = getattr(mod, "PatchPipelineFixerError")

        try:
            from skills.patch_evaluator import PatchEvaluatorError
        except ImportError:
            from patch_evaluator import PatchEvaluatorError

        unique_eval_err = f"FatalEvalIssue_{uuid.uuid4().hex}"

        with patch("skills.patch_evaluator.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_checker.PatchChecker"):

            evaluator_inst = MagicMock()
            evaluator_inst.evaluate.side_effect = PatchEvaluatorError(unique_eval_err)
            evaluator_inst.evaluate_with_autocorrect.side_effect = PatchEvaluatorError(unique_eval_err)
            mock_evaluator_cls.return_value = evaluator_inst

            with self.assertRaises((PatchEvaluatorError, fixer_error_cls)) as ctx:
                if fixer_cls:
                    instance = fixer_cls(repo_path=self.repo_path)
                    method = (
                        getattr(instance, "process_patch", None) or
                        getattr(instance, "run", None) or
                        getattr(instance, "fix_and_apply", None) or
                        getattr(instance, "apply_patch", None)
                    )
                    method(patch_content=self.patch_content, target_file=self.target_file)
                else:
                    fixer_fn(repo_path=self.repo_path, patch_content=self.patch_content, target_file=self.target_file)

            self.assertIn(unique_eval_err, str(ctx.exception))

    def test_checker_exception_propagation_or_wrapping(self):
        mod = self._get_module()
        fixer_cls = getattr(mod, "PatchPipelineFixer", None)
        fixer_fn = getattr(mod, "fix_patch_pipeline", None) or getattr(mod, "apply_safe_patch", None)
        fixer_error_cls = getattr(mod, "PatchPipelineFixerError")

        try:
            from skills.patch_checker import PatchCheckerError
        except ImportError:
            from patch_checker import PatchCheckerError

        unique_checker_err = f"FatalCheckerIssue_{uuid.uuid4().hex}"

        eval_result_mock = MagicMock(is_safe=True, is_valid=True, reasons=[], metrics={}, was_corrected=False)

        with patch("skills.patch_evaluator.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_checker.PatchChecker") as mock_checker_cls:

            evaluator_inst = MagicMock()
            evaluator_inst.evaluate.return_value = eval_result_mock
            evaluator_inst.evaluate_with_autocorrect.return_value = eval_result_mock
            mock_evaluator_cls.return_value = evaluator_inst

            checker_inst = MagicMock()
            checker_inst.check_patch.side_effect = PatchCheckerError(unique_checker_err)
            checker_inst.check.side_effect = PatchCheckerError(unique_checker_err)
            mock_checker_cls.return_value = checker_inst

            with self.assertRaises((PatchCheckerError, fixer_error_cls)) as ctx:
                if fixer_cls:
                    instance = fixer_cls(repo_path=self.repo_path)
                    method = (
                        getattr(instance, "process_patch", None) or
                        getattr(instance, "run", None) or
                        getattr(instance, "fix_and_apply", None) or
                        getattr(instance, "apply_patch", None)
                    )
                    method(patch_content=self.patch_content, target_file=self.target_file)
                else:
                    fixer_fn(repo_path=self.repo_path, patch_content=self.patch_content, target_file=self.target_file)

            self.assertIn(unique_checker_err, str(ctx.exception))

    def test_stream_input_handling(self):
        mod = self._get_module()
        fixer_cls = getattr(mod, "PatchPipelineFixer", None)
        stream_token = f"STREAM_{uuid.uuid4().hex}"
        stream_content = f"--- stream\n+++ stream\n+{stream_token}\n".encode("utf-8")
        byte_stream = io.BytesIO(stream_content)

        eval_result_mock = MagicMock(is_safe=True, is_valid=True, metrics={"stream_token": stream_token}, reasons=[])
        checker_result = {"success": True, "token": stream_token}

        with patch("skills.patch_evaluator.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_checker.PatchChecker") as mock_checker_cls:

            evaluator_inst = MagicMock()
            evaluator_inst.evaluate_stream.return_value = eval_result_mock
            evaluator_inst.evaluate.return_value = eval_result_mock
            mock_evaluator_cls.return_value = evaluator_inst

            checker_inst = MagicMock()
            checker_inst.check_stream.return_value = checker_result
            checker_inst.check_patch.return_value = checker_result
            mock_checker_cls.return_value = checker_inst

            if fixer_cls:
                instance = fixer_cls(repo_path=self.repo_path)
                if hasattr(instance, "process_stream"):
                    res = instance.process_stream(stream=byte_stream, target_file=self.target_file)
                    self.assertIsNotNone(res)
                    self.assertTrue(evaluator_inst.evaluate_stream.called or evaluator_inst.evaluate.called)
                elif hasattr(instance, "process_patch"):
                    byte_stream.seek(0)
                    res = instance.process_patch(patch_content=byte_stream, target_file=self.target_file)
                    self.assertIsNotNone(res)

    def test_invalid_types_raise_proper_exceptions(self):
        mod = self._get_module()
        fixer_cls = getattr(mod, "PatchPipelineFixer", None)
        fixer_fn = getattr(mod, "fix_patch_pipeline", None) or getattr(mod, "apply_safe_patch", None)
        fixer_error = getattr(mod, "PatchPipelineFixerError")

        with patch("skills.patch_evaluator.PatchEvaluator"), patch("skills.patch_checker.PatchChecker"):
            if fixer_cls:
                instance = fixer_cls(repo_path=self.repo_path)
                method = (
                    getattr(instance, "process_patch", None) or
                    getattr(instance, "run", None) or
                    getattr(instance, "fix_and_apply", None) or
                    getattr(instance, "apply_patch", None)
                )
                with self.assertRaises((TypeError, ValueError, fixer_error)):
                    method(patch_content=None, target_file=self.target_file)

                with self.assertRaises((TypeError, ValueError, fixer_error)):
                    method(patch_content=self.patch_content, target_file=random.choice([None, 12345, []]))
            else:
                with self.assertRaises((TypeError, ValueError, fixer_error)):
                    fixer_fn(repo_path=self.repo_path, patch_content=None, target_file=self.target_file)


if __name__ == "__main__":
    unittest.main()