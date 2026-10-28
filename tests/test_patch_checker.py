import io
import os
import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch
from skills.patch_analyzer import PatchAnalyzerError
from skills.patch_evaluator import PatchEvaluatorError


class TestPatchCheckerInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path_val = f"/tmp/{uuid.uuid4().hex}"
        self.target_file_val = f"src/{uuid.uuid4().hex}.py"
        self.patch_content_val = f"diff --git a/{self.target_file_val} b/{self.target_file_val}\n--- a/{self.target_file_val}\n+++ b/{self.target_file_val}\n@@ -1,1 +1,15 @@\n-print('{uuid.uuid4().hex}')\n+print('{uuid.uuid4().hex}')"
        self.policy_val = {
            "strict_safety": random.choice([True, False]),
            "disallow_syntax_risks": random.choice([True, False])
        }

    @patch("skills.patch_checker.PatchEvaluator")
    @patch("skills.patch_checker.PatchAnalyzer")
    def test_check_patch_success(self, mock_analyzer_cls, mock_evaluator_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        expected_risk = round(random.uniform(0.0, 1.0), 2)
        expected_syntax_risk = random.choice([True, False])
        mock_analyzer.analyze.return_value = {
            "risk_score": expected_risk,
            "syntax_risks": expected_syntax_risk
        }

        mock_evaluator = mock_evaluator_cls.return_value
        eval_res = MagicMock()
        eval_res.is_safe = True
        eval_res.is_valid = True
        eval_res.metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        eval_res.reasons = [uuid.uuid4().hex]
        eval_res.telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}
        eval_res.was_corrected = random.choice([True, False])
        mock_evaluator.evaluate.return_value = eval_res

        checker = PatchChecker(repo_path=self.repo_path_val, policy=self.policy_val)
        result = checker.check_patch(patch_content=self.patch_content_val, target_file=self.target_file_val)

        self.assertIn("is_safe", result)
        self.assertIn("is_valid", result)
        self.assertEqual(result["risk_score"], expected_risk)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)
        self.assertIn("policy_verdict", result)

    def test_check_patch_empty_content(self):
        checker = PatchChecker(repo_path=self.repo_path_val)
        empty_strings = ["", "   ", "\n\t "]
        for empty_str in empty_strings:
            with self.assertRaises(PatchCheckerError):
                checker.check_patch(patch_content=empty_str)

    @patch("skills.patch_checker.PatchAnalyzer")
    def test_check_patch_analyzer_error(self, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        error_msg = uuid.uuid4().hex
        mock_analyzer.analyze.side_effect = PatchAnalyzerError(error_msg)

        checker = PatchChecker(repo_path=self.repo_path_val)
        with self.assertRaises(PatchCheckerError) as ctx:
            checker.check_patch(patch_content=self.patch_content_val)
        self.assertIn("Ошибка анализатора", str(ctx.exception))

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_patch_evaluator_error(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"risk_score": 0.1, "syntax_risks": False}

        mock_evaluator = mock_evaluator_cls.return_value
        error_msg = uuid.uuid4().hex
        mock_evaluator.evaluate.side_effect = PatchEvaluatorError(error_msg)

        checker = PatchChecker(repo_path=self.repo_path_val)
        with self.assertRaises(PatchCheckerError) as ctx:
            checker.check_patch(patch_content=self.patch_content_val)
        self.assertIn("Ошибка оценщика", str(ctx.exception))

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_file_success(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"risk_score": 0.2, "syntax_risks": False}

        mock_evaluator = mock_evaluator_cls.return_value
        eval_res = MagicMock()
        eval_res.is_safe = True
        eval_res.is_valid = True
        eval_res.metrics = {}
        eval_res.reasons = []
        eval_res.telemetry = {}
        eval_res.was_corrected = False
        mock_evaluator.evaluate.return_value = eval_res

        temp_file_path = f"/tmp/{uuid.uuid4().hex}.patch"
        file_content = f"content_{uuid.uuid4().hex}"

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", unittest.mock.mock_open(read_data=file_content)):
            checker = PatchChecker(repo_path=self.repo_path_val)
            res = checker.check_file(file_path=temp_file_path, target_file=self.target_file_val)
            self.assertIn("is_safe", res)

    def test_check_file_not_found(self):
        missing_file = f"/tmp/{uuid.uuid4().hex}_missing.patch"
        with patch("os.path.exists", return_value=False):
            checker = PatchChecker(repo_path=self.repo_path_val)
            with self.assertRaises(PatchCheckerError):
                checker.check_file(file_path=missing_file)

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_stream_success(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"risk_score": 0.0, "syntax_risks": False}

        mock_evaluator = mock_evaluator_cls.return_value
        eval_res = MagicMock()
        eval_res.is_safe = True
        eval_res.is_valid = True
        eval_res.metrics = {}
        eval_res.reasons = []
        eval_res.telemetry = {}
        eval_res.was_corrected = False
        mock_evaluator.evaluate.return_value = eval_res

        stream_content = f"stream_patch_{uuid.uuid4().hex}"
        stream = io.StringIO(stream_content)

        checker = PatchChecker(repo_path=self.repo_path_val)
        res = checker.check_stream(stream=stream, target_file=self.target_file_val)
        self.assertIn("is_safe", res)

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_method_dynamic_repo(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"risk_score": 0.5, "syntax_risks": False}

        mock_evaluator = mock_evaluator_cls.return_value
        eval_res = MagicMock()
        eval_res.is_safe = True
        eval_res.is_valid = True
        eval_res.metrics = {uuid.uuid4().hex: 10}
        eval_res.reasons = []
        eval_res.telemetry = {}
        eval_res.was_corrected = False
        mock_evaluator.evaluate.return_value = eval_res

        initial_repo = f"/tmp/{uuid.uuid4().hex}"
        new_repo = f"/tmp/{uuid.uuid4().hex}"

        checker = PatchChecker(repo_path=initial_repo)
        res = checker.check(patch_content=self.patch_content_val, repo_path=new_repo)

        self.assertEqual(checker.repo_path, new_repo)
        self.assertIn("metrics", res)

    @patch("skills.patch_checker.PatchChecker.check_patch")
    def test_functional_check_patch_wrapper(self, mock_check_patch):
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_check_patch.return_value = expected_dict

        res = check_patch(
            patch_content=self.patch_content_val,
            repo_path=self.repo_path_val,
            target_file=self.target_file_val,
            policy=self.policy_val
        )
        self.assertEqual(res, expected_dict)


if __name__ == "__main__":
    unittest.main()