import unittest
from unittest.mock import patch, MagicMock
import io
import os
import uuid
import random
import string

from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch
from skills.patch_analyzer import PatchAnalyzerError
from skills.patch_evaluator import PatchEvaluatorError


class TestPatchCheckerInquisition(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/{uuid.uuid4().hex}"
        self.rand_file = f"/tmp/{uuid.uuid4().hex}.py"
        self.rand_content = f"class {uuid.uuid4().hex[:8]}:\n    pass\n"

    def test_patch_checker_empty_content_raises(self):
        checker = PatchChecker(repo_path=self.rand_repo)
        for empty in ["", "   ", "\n\t "]:
            with self.subTest(empty=empty):
                with self.assertRaises(PatchCheckerError):
                    checker.check_patch(empty)

    @patch("skills.patch_checker.PatchAnalyzer.analyze")
    @patch("skills.patch_checker.PatchEvaluator.evaluate")
    def test_patch_checker_analyzer_error(self, mock_evaluate, mock_analyze):
        mock_analyze.side_effect = PatchAnalyzerError(uuid.uuid4().hex)
        checker = PatchChecker(repo_path=self.rand_repo)
        with self.assertRaises(PatchCheckerError):
            checker.check_patch(self.rand_content)

    @patch("skills.patch_checker.PatchAnalyzer.analyze")
    @patch("skills.patch_checker.PatchEvaluator.evaluate")
    def test_patch_checker_evaluator_error(self, mock_evaluate, mock_analyze):
        mock_analyze.return_value = {"risk_score": 0.1, "syntax_risks": []}
        mock_evaluate.side_effect = PatchEvaluatorError(uuid.uuid4().hex)
        checker = PatchChecker(repo_path=self.rand_repo)
        with self.assertRaises(PatchCheckerError):
            checker.check_patch(self.rand_content)

    @patch("skills.patch_checker.PatchAnalyzer.analyze")
    @patch("skills.patch_checker.PatchEvaluator.evaluate")
    def test_patch_checker_success_flow(self, mock_evaluate, mock_analyze):
        risk = round(random.uniform(0.0, 1.0), 2)
        mock_analyze.return_value = {"risk_score": risk, "syntax_risks": []}

        eval_res = MagicMock()
        eval_res.is_safe = True
        eval_res.is_valid = True
        eval_res.metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        eval_res.reasons = [uuid.uuid4().hex]
        eval_res.telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}
        eval_res.was_corrected = False
        mock_evaluate.return_value = eval_res

        checker = PatchChecker(repo_path=self.rand_repo)
        res = checker.check_patch(self.rand_content)

        self.assertTrue(res["is_safe"])
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["risk_score"], risk)
        self.assertEqual(res["evaluation"]["reasons"], eval_res.reasons)
        self.assertEqual(res["evaluation"]["metrics"], eval_res.metrics)

    @patch("skills.patch_checker.PatchAnalyzer.analyze")
    @patch("skills.patch_checker.PatchEvaluator.evaluate")
    def test_patch_checker_policy_violations(self, mock_evaluate, mock_analyze):
        mock_analyze.return_value = {"risk_score": 0.9, "syntax_risks": [uuid.uuid4().hex]}

        eval_res = MagicMock()
        eval_res.is_safe = False
        eval_res.is_valid = False
        eval_res.metrics = {}
        eval_res.reasons = []
        eval_res.telemetry = {}
        eval_res.was_corrected = True
        mock_evaluate.return_value = eval_res

        policy = {"strict_safety": True, "disallow_syntax_risks": True}
        checker = PatchChecker(repo_path=self.rand_repo, policy=policy)
        res = checker.check_patch(self.rand_content)

        self.assertIn("disallowed_risks", res["policy_verdict"])

    @patch("os.path.exists")
    def test_check_file_not_found(self, mock_exists):
        mock_exists.return_value = False
        checker = PatchChecker(repo_path=self.rand_repo)
        with self.assertRaises(PatchCheckerError):
            checker.check_file(self.rand_file)

    @patch("os.path.exists")
    @patch("builtins.open")
    @patch("skills.patch_checker.PatchChecker.check_patch")
    def test_check_file_success(self, mock_check_patch, mock_open_func, mock_exists):
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_file.read.return_value = self.rand_content
        mock_open_func.return_value.__enter__.return_value = mock_file
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_check_patch.return_value = expected_dict

        checker = PatchChecker(repo_path=self.rand_repo)
        target = uuid.uuid4().hex
        res = checker.check_file(self.rand_file, target_file=target)

        self.assertEqual(res, expected_dict)
        mock_check_patch.assert_called_once_with(patch_content=self.rand_content, target_file=target)

    @patch("skills.patch_checker.PatchChecker.check_patch")
    def test_check_stream_success(self, mock_check_patch):
        stream = io.StringIO(self.rand_content)
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_check_patch.return_value = expected_dict

        checker = PatchChecker(repo_path=self.rand_repo)
        target = uuid.uuid4().hex
        res = checker.check_stream(stream, target_file=target)

        self.assertEqual(res, expected_dict)
        mock_check_patch.assert_called_once_with(patch_content=self.rand_content, target_file=target)

    def test_check_stream_exception_raises(self):
        bad_stream = MagicMock()
        bad_stream.read.side_effect = Exception(uuid.uuid4().hex)
        checker = PatchChecker(repo_path=self.rand_repo)
        with self.assertRaises(PatchCheckerError):
            checker.check_stream(bad_stream)

    @patch("skills.patch_checker.PatchChecker.check_patch")
    def test_check_integration_method(self, mock_check_patch):
        metrics_dict = {uuid.uuid4().hex: random.randint(10, 50)}
        mock_check_patch.return_value = {
            "is_safe": True,
            "evaluation": {
                "metrics": metrics_dict
            }
        }

        new_repo = f"/tmp/{uuid.uuid4().hex}"
        checker = PatchChecker(repo_path=self.rand_repo)
        target = uuid.uuid4().hex
        res = checker.check(patch_content=self.rand_content, repo_path=new_repo, target_file=target)

        self.assertEqual(checker.repo_path, new_repo)
        self.assertIn("metrics", res)
        self.assertEqual(res["metrics"], metrics_dict)

    @patch("skills.patch_checker.PatchChecker.check_patch")
    def test_functional_check_patch_wrapper(self, mock_check_patch):
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_check_patch.return_value = expected_dict

        policy = {uuid.uuid4().hex: True}
        target = uuid.uuid4().hex

        with patch("skills.patch_checker.PatchChecker.__init__", return_value=None) as mock_init:
            with patch("skills.patch_checker.PatchChecker.check_patch", return_value=expected_dict) as mock_cp:
                res = check_patch(patch_content=self.rand_content, repo_path=self.rand_repo, target_file=target, policy=policy)
                self.assertEqual(res, expected_dict)
                mock_init.assert_called_once_with(repo_path=self.rand_repo, policy=policy)
                mock_cp.assert_called_once_with(patch_content=self.rand_content, target_file=target)