import io
import os
import unittest
import uuid
import random
from unittest.mock import patch, MagicMock

from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch
from skills.patch_analyzer import PatchAnalyzerError
from skills.patch_evaluator import PatchEvaluatorError


class TestPatchCheckerInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path_val = uuid.uuid4().hex
        self.patch_content_val = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py\n+print('{uuid.uuid4().hex}')"
        self.target_file_val = f"{uuid.uuid4().hex}.py"

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_patch_success(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        expected_risk = round(random.uniform(0.0, 1.0), 2)
        mock_analyzer.analyze.return_value = {
            "risk_score": expected_risk,
            "syntax_risks": []
        }

        mock_evaluator = mock_evaluator_cls.return_value
        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = True
        eval_result.metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        eval_result.reasons = [uuid.uuid4().hex]
        eval_result.telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}
        eval_result.was_corrected = False
        mock_evaluator.evaluate.return_value = eval_result

        checker = PatchChecker(repo_path=self.repo_path_val)
        result = checker.check_patch(patch_content=self.patch_content_val, target_file=self.target_file_val)

        self.assertTrue(result["is_safe"])
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["risk_score"], expected_risk)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)
        self.assertEqual(result["evaluation"]["reasons"][0], eval_result.reasons[0])

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_patch_empty_content(self, mock_evaluator_cls, mock_analyzer_cls):
        checker = PatchChecker(repo_path=self.repo_path_val)
        with self.assertRaises(PatchCheckerError):
            checker.check_patch(patch_content="   ", target_file=self.target_file_val)

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_patch_analyzer_error(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.side_effect = PatchAnalyzerError(uuid.uuid4().hex)

        checker = PatchChecker(repo_path=self.repo_path_val)
        with self.assertRaises(PatchCheckerError):
            checker.check_patch(patch_content=self.patch_content_val)

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_patch_evaluator_error(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"risk_score": 0.1}

        mock_evaluator = mock_evaluator_cls.return_value
        mock_evaluator.evaluate.side_effect = PatchEvaluatorError(uuid.uuid4().hex)

        checker = PatchChecker(repo_path=self.repo_path_val)
        with self.assertRaises(PatchCheckerError):
            checker.check_patch(patch_content=self.patch_content_val)

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_policy_strict_safety_violation(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"risk_score": 0.9}

        mock_evaluator = mock_evaluator_cls.return_value
        eval_result = MagicMock()
        eval_result.is_safe = False
        eval_result.is_valid = True
        mock_evaluator.evaluate.return_value = eval_result

        policy = {"strict_safety": True}
        checker = PatchChecker(repo_path=self.repo_path_val, policy=policy)
        result = checker.check_patch(patch_content=self.patch_content_val)

        self.assertFalse(result["is_safe"])
        self.assertIn("disallowed_risks", result["policy_verdict"])

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_policy_disallow_syntax_risks(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {
            "risk_score": 0.2,
            "syntax_risks": [uuid.uuid4().hex]
        }

        mock_evaluator = mock_evaluator_cls.return_value
        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = True
        mock_evaluator.evaluate.return_value = eval_result

        policy = {"disallow_syntax_risks": True}
        checker = PatchChecker(repo_path=self.repo_path_val, policy=policy)
        result = checker.check_patch(patch_content=self.patch_content_val)

        self.assertIn("disallowed_risks", result["policy_verdict"])

    @patch("skills.patch_checker.os.path.exists")
    @patch("skills.patch_checker.open", create=True)
    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_file_success(self, mock_evaluator_cls, mock_analyzer_cls, mock_open, mock_exists):
        mock_exists.return_value = True
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.read.return_value = self.patch_content_val

        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"risk_score": 0.0}

        mock_evaluator = mock_evaluator_cls.return_value
        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = True
        mock_evaluator.evaluate.return_value = eval_result

        file_path_val = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.patch"
        checker = PatchChecker(repo_path=self.repo_path_val)
        result = checker.check_file(file_path_val, target_file=self.target_file_val)

        self.assertTrue(result["is_safe"])

    @patch("skills.patch_checker.os.path.exists")
    def test_check_file_not_found(self, mock_exists):
        mock_exists.return_value = False
        file_path_val = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.patch"
        checker = PatchChecker(repo_path=self.repo_path_val)
        with self.assertRaises(PatchCheckerError):
            checker.check_file(file_path_val)

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_stream_success(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"risk_score": 0.0}

        mock_evaluator = mock_evaluator_cls.return_value
        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = True
        mock_evaluator.evaluate.return_value = eval_result

        stream = io.StringIO(self.patch_content_val)
        checker = PatchChecker(repo_path=self.repo_path_val)
        result = checker.check_stream(stream, target_file=self.target_file_val)

        self.assertTrue(result["is_safe"])

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_integration_method(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"risk_score": 0.0}

        mock_evaluator = mock_evaluator_cls.return_value
        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = True
        eval_result.metrics = {uuid.uuid4().hex: random.randint(1, 10)}
        mock_evaluator.evaluate.return_value = eval_result

        new_repo_path = uuid.uuid4().hex
        checker = PatchChecker(repo_path=self.repo_path_val)
        result = checker.check(patch_content=self.patch_content_val, repo_path=new_repo_path, target_file=self.target_file_val)

        self.assertEqual(checker.repo_path, new_repo_path)
        self.assertIn("metrics", result)

    @patch("skills.patch_checker.PatchChecker.check_patch")
    def test_module_level_check_patch(self, mock_check_patch):
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_check_patch.return_value = expected_dict

        policy_val = {uuid.uuid4().hex: True}
        res = check_patch(patch_content=self.patch_content_val, repo_path=self.repo_path_val, target_file=self.target_file_val, policy=policy_val)
        self.assertEqual(res, expected_dict)