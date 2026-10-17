import io
import os
import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.patch_checker import (
    PatchChecker,
    PatchCheckerError,
    check_patch,
)
from skills.patch_analyzer import PatchAnalyzerError
from skills.patch_evaluator import PatchEvaluationResult, PatchEvaluatorError


class TestPatchCheckerInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path_val = f"/tmp/repo_{uuid.uuid4().hex}"
        self.random_policy_key = f"policy_{uuid.uuid4().hex[:6]}"
        self.checker = PatchChecker(repo_path=self.repo_path_val, policy={self.random_policy_key: True, "strict_safety": True})

    def test_init_defaults(self):
        default_checker = PatchChecker()
        self.assertIsNone(default_checker.repo_path)
        self.assertEqual(default_checker.policy, {})
        self.assertIsNotNone(default_checker.analyzer)
        self.assertIsNotNone(default_checker.evaluator)

    def test_check_patch_empty_content(self):
        empty_patches = ["", "   ", "\n\t "]
        for patch_str in empty_patches:
            with self.subTest(patch_str=patch_str):
                with self.assertRaises(PatchCheckerError):
                    self.checker.check_patch(patch_str)

    @patch("skills.patch_checker.PatchAnalyzer.analyze")
    def test_check_patch_analyzer_error(self, mock_analyze):
        err_msg = f"Analyzer failed: {uuid.uuid4().hex}"
        mock_analyze.side_effect = PatchAnalyzerError(err_msg)
        valid_patch_stub = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"

        with self.assertRaises(PatchCheckerError) as ctx:
            self.checker.check_patch(valid_patch_stub)
        self.assertIn(err_msg, str(ctx.exception))

    @patch("skills.patch_checker.PatchEvaluator.evaluate")
    @patch("skills.patch_checker.PatchAnalyzer.analyze")
    def test_check_patch_evaluator_error(self, mock_analyze, mock_evaluate):
        eval_err_msg = f"Evaluator failed: {uuid.uuid4().hex}"
        mock_analyze.return_value = {"risk_score": 0.1, "syntax_risks": []}
        mock_evaluate.side_effect = PatchEvaluatorError(eval_err_msg)
        valid_patch_stub = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"

        with self.assertRaises(PatchCheckerError) as ctx:
            self.checker.check_patch(valid_patch_stub)
        self.assertIn(eval_err_msg, str(ctx.exception))

    @patch("skills.patch_checker.PatchEvaluator.evaluate")
    @patch("skills.patch_checker.PatchAnalyzer.analyze")
    def test_check_patch_success_flow(self, mock_analyze, mock_evaluate):
        rand_risk = round(random.uniform(0.0, 1.0), 2)
        mock_analyze.return_value = {
            "risk_score": rand_risk,
            "syntax_risks": []
        }

        eval_res = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={"loc": random.randint(1, 100)},
            reasons=[uuid.uuid4().hex],
            telemetry={"cpu": random.randint(10, 90)},
            was_corrected=False
        )
        mock_evaluate.return_value = eval_res

        patch_content = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py"
        target_file_arg = f"{uuid.uuid4().hex}.py"

        result = self.checker.check_patch(patch_content, target_file=target_file_arg)

        self.assertTrue(result["is_safe"])
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["risk_score"], rand_risk)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)
        self.assertEqual(result["evaluation"]["metrics"], eval_res.metrics)
        self.assertEqual(result["evaluation"]["reasons"], eval_res.reasons)

    @patch("skills.patch_checker.PatchEvaluator.evaluate")
    @patch("skills.patch_checker.PatchAnalyzer.analyze")
    def test_check_patch_strict_safety_policy_violation(self, mock_analyze, mock_evaluate):
        mock_analyze.return_value = {
            "risk_score": 0.9,
            "syntax_risks": []
        }

        eval_res = PatchEvaluationResult(
            is_safe=False,
            is_valid=True,
            metrics={},
            reasons=[],
            telemetry={},
            was_corrected=False
        )
        mock_evaluate.return_value = eval_res

        patch_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"
        result = self.checker.check_patch(patch_content)

        self.assertFalse(result["is_safe"])
        self.assertIn("policy_verdict", result)
        self.assertEqual(result["policy_verdict"].get("disallowed_risks"), "Strict safety policy violated")

    @patch("skills.patch_checker.PatchEvaluator.evaluate")
    @patch("skills.patch_checker.PatchAnalyzer.analyze")
    def test_check_patch_syntax_risks_policy_violation(self, mock_analyze, mock_evaluate):
        checker_syntax = PatchChecker(policy={"disallow_syntax_risks": True})
        mock_analyze.return_value = {
            "risk_score": 0.5,
            "syntax_risks": [uuid.uuid4().hex]
        }

        eval_res = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={},
            reasons=[],
            telemetry={},
            was_corrected=False
        )
        mock_evaluate.return_value = eval_res

        patch_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"
        result = checker_syntax.check_patch(patch_content)

        self.assertIn("policy_verdict", result)
        self.assertEqual(result["policy_verdict"].get("disallowed_risks"), "Syntax risks detected")

    def test_check_file_not_found(self):
        missing_path = f"/nonexistent_path_{uuid.uuid4().hex}.patch"
        with self.assertRaises(PatchCheckerError) as ctx:
            self.checker.check_file(missing_path)
        self.assertIn("Файл не найден", str(ctx.exception))

    @patch("skills.patch_checker.PatchChecker.check_patch")
    def test_check_file_success(self, mock_check_patch):
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_check_patch.return_value = expected_dict

        file_content = f"diff --content {uuid.uuid4().hex}"
        temp_filename = f"test_patch_{uuid.uuid4().hex}.diff"

        try:
            with open(temp_filename, "w", encoding="utf-8") as f:
                f.write(file_content)

            res = self.checker.check_file(temp_filename, target_file="some_target.py")
            self.assertEqual(res, expected_dict)
            mock_check_patch.assert_called_once_with(patch_content=file_content, target_file="some_target.py")
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    @patch("skills.patch_checker.PatchChecker.check_patch")
    def test_check_stream_success(self, mock_check_patch):
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_check_patch.return_value = expected_dict

        stream_content = f"diff --stream {uuid.uuid4().hex}"
        stream = io.StringIO(stream_content)

        res = self.checker.check_stream(stream, target_file="stream_target.py")
        self.assertEqual(res, expected_dict)
        mock_check_patch.assert_called_once_with(patch_content=stream_content, target_file="stream_target.py")

    @patch("skills.patch_checker.PatchEvaluator")
    @patch("skills.patch_checker.PatchChecker.check_patch")
    def test_check_integration_method(self, mock_check_patch, mock_evaluator_cls):
        metrics_dict = {uuid.uuid4().hex: random.randint(1, 50)}
        mock_check_patch.return_value = {
            "is_safe": True,
            "evaluation": {
                "metrics": metrics_dict
            }
        }

        new_repo_path = f"/repo/path/{uuid.uuid4().hex}"
        patch_text = f"diff --integration {uuid.uuid4().hex}"
        target_f = f"{uuid.uuid4().hex}.py"

        result = self.checker.check(patch_content=patch_text, repo_path=new_repo_path, target_file=target_f)

        self.assertEqual(self.checker.repo_path, new_repo_path)
        self.assertIn("metrics", result)
        self.assertEqual(result["metrics"], metrics_dict)
        mock_check_patch.assert_called_once_with(patch_content=patch_text, target_file=target_f)

    @patch("skills.patch_checker.PatchChecker.check_patch")
    def test_module_level_check_patch(self, mock_check_patch):
        expected_res = {uuid.uuid4().hex: random.random()}
        mock_check_patch.return_value = expected_res

        patch_str = f"diff --module {uuid.uuid4().hex}"
        repo_arg = f"/path/{uuid.uuid4().hex}"
        target_arg = f"file_{uuid.uuid4().hex}.py"
        policy_arg = {uuid.uuid4().hex: True}

        res = check_patch(patch_content=patch_str, repo_path=repo_arg, target_file=target_arg, policy=policy_arg)
        self.assertEqual(res, expected_res)


if __name__ == "__main__":
    unittest.main()