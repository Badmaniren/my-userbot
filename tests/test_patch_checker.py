import io
import os
import random
import string
import sys
import tempfile
import unittest
import uuid
from unittest.mock import MagicMock, patch

try:
    import skills.patch_checker as patch_checker_module
    from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch
except ImportError:
    import patch_checker as patch_checker_module
    from patch_checker import PatchChecker, PatchCheckerError, check_patch

try:
    from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError
except ImportError:
    from patch_analyzer import PatchAnalyzer, PatchAnalyzerError

try:
    from skills.patch_evaluator import PatchEvaluationResult, PatchEvaluator, PatchEvaluatorError
except ImportError:
    from patch_evaluator import PatchEvaluationResult, PatchEvaluator, PatchEvaluatorError


def _generate_random_token(length=12):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def _generate_random_diff():
    filename = f"{_generate_random_token(6)}/{_generate_random_token(8)}.py"
    token_old = uuid.uuid4().hex
    token_new = uuid.uuid4().hex
    diff = (
        f"--- a/{filename}\n"
        f"+++ b/{filename}\n"
        f"@@ -1,3 +1,4 @@\n"
        f" def sample_func():\n"
        f"-    value = '{token_old}'\n"
        f"+    value = '{token_new}'\n"
        f"+    return value\n"
    )
    return diff, filename, token_new


class TestPatchCheckerInitialization(unittest.TestCase):

    def test_init_default_components(self):
        with patch.object(patch_checker_module, "PatchAnalyzer") as mock_analyzer_cls, \
             patch.object(patch_checker_module, "PatchEvaluator") as mock_evaluator_cls:

            checker = PatchChecker()

            mock_analyzer_cls.assert_called_once_with()
            mock_evaluator_cls.assert_called_once_with(repo_path=None)
            self.assertIsNotNone(checker.analyzer)
            self.assertIsNotNone(checker.evaluator)

    def test_init_custom_repo_and_policy(self):
        rand_repo = f"/tmp/{uuid.uuid4().hex}/repo"
        rand_policy_key = f"rule_{uuid.uuid4().hex[:6]}"
        rand_policy_val = random.randint(1, 100)
        custom_policy = {rand_policy_key: rand_policy_val}

        with patch.object(patch_checker_module, "PatchAnalyzer") as mock_analyzer_cls, \
             patch.object(patch_checker_module, "PatchEvaluator") as mock_evaluator_cls:

            checker = PatchChecker(repo_path=rand_repo, policy=custom_policy)

            mock_analyzer_cls.assert_called_once_with()
            mock_evaluator_cls.assert_called_once_with(repo_path=rand_repo)
            self.assertEqual(checker.policy[rand_policy_key], rand_policy_val)


class TestPatchCheckerExecution(unittest.TestCase):

    def test_check_patch_composition_success(self):
        rand_diff, rand_filename, rand_token = _generate_random_diff()
        rand_risk_score = random.uniform(0.1, 0.9)
        rand_metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        rand_metric_val = random.randint(10, 500)
        rand_reason = f"reason_{uuid.uuid4().hex}"

        mock_analysis_data = {
            "token": rand_token,
            "syntax_risks": [],
            "statistics": {rand_metric_key: rand_metric_val},
            "risk_score": rand_risk_score
        }

        mock_eval_result = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={rand_metric_key: rand_metric_val},
            reasons=[rand_reason],
            telemetry={"run_id": uuid.uuid4().hex},
            was_corrected=False
        )

        with patch.object(patch_checker_module, "PatchAnalyzer") as mock_analyzer_cls, \
             patch.object(patch_checker_module, "PatchEvaluator") as mock_evaluator_cls:

            mock_analyzer_instance = MagicMock()
            mock_analyzer_instance.analyze.return_value = mock_analysis_data
            mock_analyzer_cls.return_value = mock_analyzer_instance

            mock_evaluator_instance = MagicMock()
            mock_evaluator_instance.evaluate.return_value = mock_eval_result
            mock_evaluator_cls.return_value = mock_evaluator_instance

            checker = PatchChecker()
            result = checker.check_patch(patch_content=rand_diff, target_file=rand_filename)

            mock_analyzer_instance.analyze.assert_called_once_with(rand_diff)
            mock_evaluator_instance.evaluate.assert_called_once_with(
                patch_content=rand_diff,
                target_file=rand_filename
            )

            self.assertIsInstance(result, dict)
            self.assertTrue(result["is_safe"])
            self.assertTrue(result["is_valid"])
            self.assertEqual(result["analysis"]["token"], rand_token)
            self.assertIn(rand_reason, result["evaluation"]["reasons"])
            self.assertIn("risk_score", result)

    def test_check_patch_policy_violation_unsafe(self):
        rand_diff, rand_filename, _ = _generate_random_diff()
        rand_reason = f"critical_vulnerability_{uuid.uuid4().hex}"

        mock_analysis_data = {
            "syntax_risks": ["dangerous_eval_call"],
            "statistics": {"added_lines": random.randint(5, 50)},
            "risk_score": 0.85
        }

        mock_eval_result = PatchEvaluationResult(
            is_safe=False,
            is_valid=True,
            metrics={},
            reasons=[rand_reason],
            telemetry={},
            was_corrected=False
        )

        with patch.object(patch_checker_module, "PatchAnalyzer") as mock_analyzer_cls, \
             patch.object(patch_checker_module, "PatchEvaluator") as mock_evaluator_cls:

            mock_analyzer_instance = MagicMock()
            mock_analyzer_instance.analyze.return_value = mock_analysis_data
            mock_analyzer_cls.return_value = mock_analyzer_instance

            mock_evaluator_instance = MagicMock()
            mock_evaluator_instance.evaluate.return_value = mock_eval_result
            mock_evaluator_cls.return_value = mock_evaluator_instance

            checker = PatchChecker(policy={"disallow_syntax_risks": True, "strict_safety": True})
            result = checker.check_patch(patch_content=rand_diff, target_file=rand_filename)

            self.assertFalse(result["is_safe"])
            self.assertIn("disallowed_risks", result["policy_verdict"])
            self.assertIn(rand_reason, result["evaluation"]["reasons"])

    def test_check_file_integration(self):
        rand_diff, rand_filename, rand_token = _generate_random_diff()

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".diff") as tmp_file:
            tmp_file.write(rand_diff)
            tmp_file_path = tmp_file.name

        try:
            with patch.object(patch_checker_module, "PatchAnalyzer") as mock_analyzer_cls, \
                 patch.object(patch_checker_module, "PatchEvaluator") as mock_evaluator_cls:

                mock_analyzer_instance = MagicMock()
                mock_analyzer_instance.analyze.return_value = {"token": rand_token}
                mock_analyzer_cls.return_value = mock_analyzer_instance

                mock_evaluator_instance = MagicMock()
                mock_evaluator_instance.evaluate.return_value = PatchEvaluationResult(
                    is_safe=True,
                    is_valid=True,
                    metrics={},
                    reasons=[],
                    telemetry={},
                    was_corrected=False
                )
                mock_evaluator_cls.return_value = mock_evaluator_instance

                checker = PatchChecker()
                result = checker.check_file(file_path=tmp_file_path, target_file=rand_filename)

                mock_analyzer_instance.analyze.assert_called_once_with(rand_diff)
                self.assertEqual(result["analysis"]["token"], rand_token)
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)

    def test_check_stream_integration(self):
        rand_diff, _, rand_token = _generate_random_diff()
        stream_input = io.StringIO(rand_diff)

        with patch.object(patch_checker_module, "PatchAnalyzer") as mock_analyzer_cls, \
             patch.object(patch_checker_module, "PatchEvaluator") as mock_evaluator_cls:

            mock_analyzer_instance = MagicMock()
            mock_analyzer_instance.analyze.return_value = {"stream_token": rand_token}
            mock_analyzer_cls.return_value = mock_analyzer_instance

            mock_evaluator_instance = MagicMock()
            mock_evaluator_instance.evaluate.return_value = PatchEvaluationResult(
                is_safe=True,
                is_valid=True,
                metrics={},
                reasons=[],
                telemetry={},
                was_corrected=False
            )
            mock_evaluator_cls.return_value = mock_evaluator_instance

            checker = PatchChecker()
            result = checker.check_stream(stream=stream_input)

            mock_analyzer_instance.analyze.assert_called_once_with(rand_diff)
            self.assertEqual(result["analysis"]["stream_token"], rand_token)


class TestPatchCheckerErrorHandling(unittest.TestCase):

    def test_analyzer_error_wrapping(self):
        rand_diff, _, _ = _generate_random_diff()
        rand_error_msg = f"Analyzer failure: {uuid.uuid4().hex}"

        with patch.object(patch_checker_module, "PatchAnalyzer") as mock_analyzer_cls, \
             patch.object(patch_checker_module, "PatchEvaluator") as mock_evaluator_cls:

            mock_analyzer_instance = MagicMock()
            mock_analyzer_instance.analyze.side_effect = PatchAnalyzerError(rand_error_msg)
            mock_analyzer_cls.return_value = mock_analyzer_instance

            checker = PatchChecker()
            with self.assertRaises(PatchCheckerError) as ctx:
                checker.check_patch(patch_content=rand_diff)

            self.assertIn(rand_error_msg, str(ctx.exception))

    def test_evaluator_error_wrapping(self):
        rand_diff, _, _ = _generate_random_diff()
        rand_error_msg = f"Evaluator anomaly: {uuid.uuid4().hex}"

        with patch.object(patch_checker_module, "PatchAnalyzer") as mock_analyzer_cls, \
             patch.object(patch_checker_module, "PatchEvaluator") as mock_evaluator_cls:

            mock_analyzer_instance = MagicMock()
            mock_analyzer_instance.analyze.return_value = {"stats": {}}
            mock_analyzer_cls.return_value = mock_analyzer_instance

            mock_evaluator_instance = MagicMock()
            mock_evaluator_instance.evaluate.side_effect = PatchEvaluatorError(rand_error_msg)
            mock_evaluator_cls.return_value = mock_evaluator_instance

            checker = PatchChecker()
            with self.assertRaises(PatchCheckerError) as ctx:
                checker.check_patch(patch_content=rand_diff)

            self.assertIn(rand_error_msg, str(ctx.exception))

    def test_invalid_input_empty_patch_raises_patch_checker_error(self):
        checker = PatchChecker()
        with self.assertRaises(PatchCheckerError):
            checker.check_patch(patch_content="")

    def test_check_file_non_existent_raises_patch_checker_error(self):
        missing_path = f"/tmp/{uuid.uuid4().hex}_non_existent.diff"
        checker = PatchChecker()
        with self.assertRaises(PatchCheckerError):
            checker.check_file(file_path=missing_path)


class TestPatchCheckerConvenienceFunction(unittest.TestCase):

    def test_convenience_function_delegation(self):
        rand_diff, rand_filename, rand_token = _generate_random_diff()
        rand_repo = f"/tmp/repo_{uuid.uuid4().hex}"

        mock_analysis = {"token": rand_token}
        mock_eval = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={"score": random.randint(1, 100)},
            reasons=[],
            telemetry={},
            was_corrected=False
        )

        with patch.object(patch_checker_module, "PatchAnalyzer") as mock_analyzer_cls, \
             patch.object(patch_checker_module, "PatchEvaluator") as mock_evaluator_cls:

            mock_analyzer_instance = MagicMock()
            mock_analyzer_instance.analyze.return_value = mock_analysis
            mock_analyzer_cls.return_value = mock_analyzer_instance

            mock_evaluator_instance = MagicMock()
            mock_evaluator_instance.evaluate.return_value = mock_eval
            mock_evaluator_cls.return_value = mock_evaluator_instance

            result = check_patch(
                patch_content=rand_diff,
                repo_path=rand_repo,
                target_file=rand_filename
            )

            mock_evaluator_cls.assert_called_once_with(repo_path=rand_repo)
            self.assertEqual(result["analysis"]["token"], rand_token)
            self.assertTrue(result["is_safe"])


if __name__ == "__main__":
    unittest.main()