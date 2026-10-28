import unittest
from unittest.mock import patch, MagicMock
import io
import os
import uuid
import random
import string

from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch


class TestPatchCheckerInquisition(unittest.TestCase):

    def setUp(self):
        self.random_repo = f"/tmp/repo_{uuid.uuid4().hex}"
        self.random_patch = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n+print('{uuid.uuid4().hex}')"
        self.random_target = f"{uuid.uuid4().hex}.py"

    @patch('skills.patch_checker.PatchEvaluator')
    @patch('skills.patch_checker.PatchAnalyzer')
    def test_check_patch_success(self, mock_analyzer_cls, mock_evaluator_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value

        risk_val = random.random()
        mock_analyzer.analyze.return_value = {
            "risk_score": risk_val,
            "syntax_risks": []
        }

        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = True
        eval_result.metrics = {"complexity": random.randint(1, 10)}
        eval_result.reasons = [uuid.uuid4().hex]
        eval_result.telemetry = {"time": random.random()}
        eval_result.was_corrected = False
        mock_evaluator.evaluate.return_value = eval_result

        checker = PatchChecker(repo_path=self.random_repo, policy={"strict_safety": True})
        result = checker.check_patch(patch_content=self.random_patch, target_file=self.random_target)

        self.assertTrue(result["is_safe"])
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["risk_score"], risk_val)
        self.assertEqual(result["evaluation"]["metrics"], eval_result.metrics)
        self.assertEqual(result["evaluation"]["reasons"], eval_result.reasons)
        self.assertEqual(result["policy_verdict"], {})
        mock_analyzer.analyze.assert_called_once_with(self.random_patch)
        mock_evaluator.evaluate.assert_called_once_with(patch_content=self.random_patch, target_file=self.random_target)

    @patch('skills.patch_checker.PatchEvaluator')
    @patch('skills.patch_checker.PatchAnalyzer')
    def test_check_patch_empty_raises(self, mock_analyzer_cls, mock_evaluator_cls):
        checker = PatchChecker()
        empty_strings = ["", "   ", "\n\t "]
        for empty_str in empty_strings:
            with self.subTest(empty_str=empty_str):
                with self.assertRaises(PatchCheckerError):
                    checker.check_patch(patch_content=empty_str)

    @patch('skills.patch_checker.PatchEvaluator')
    @patch('skills.patch_checker.PatchAnalyzer')
    def test_check_patch_analyzer_error(self, mock_analyzer_cls, mock_evaluator_cls):
        from skills.patch_analyzer import PatchAnalyzerError
        mock_analyzer = mock_analyzer_cls.return_value
        err_msg = uuid.uuid4().hex
        mock_analyzer.analyze.side_effect = PatchAnalyzerError(err_msg)

        checker = PatchChecker()
        with self.assertRaises(PatchCheckerError) as ctx:
            checker.check_patch(patch_content=self.random_patch)
        self.assertIn(err_msg, str(ctx.exception))

    @patch('skills.patch_checker.PatchEvaluator')
    @patch('skills.patch_checker.PatchAnalyzer')
    def test_check_patch_evaluator_error(self, mock_analyzer_cls, mock_evaluator_cls):
        from skills.patch_evaluator import PatchEvaluatorError
        mock_analyzer = mock_analyzer_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value
        mock_analyzer.analyze.return_value = {"risk_score": 0.1}
        err_msg = uuid.uuid4().hex
        mock_evaluator.evaluate.side_effect = PatchEvaluatorError(err_msg)

        checker = PatchChecker()
        with self.assertRaises(PatchCheckerError) as ctx:
            checker.check_patch(patch_content=self.random_patch)
        self.assertIn(err_msg, str(ctx.exception))

    @patch('skills.patch_checker.PatchEvaluator')
    @patch('skills.patch_checker.PatchAnalyzer')
    def test_policy_violations(self, mock_analyzer_cls, mock_evaluator_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value

        mock_analyzer.analyze.return_value = {
            "risk_score": 0.9,
            "syntax_risks": [uuid.uuid4().hex]
        }

        eval_result = MagicMock()
        eval_result.is_safe = False
        eval_result.is_valid = True
        mock_evaluator.evaluate.return_value = eval_result

        policy = {
            "strict_safety": True,
            "disallow_syntax_risks": True
        }
        checker = PatchChecker(policy=policy)
        result = checker.check_patch(patch_content=self.random_patch)

        self.assertIn("disallowed_risks", result["policy_verdict"])

    @patch('skills.patch_checker.PatchEvaluator')
    @patch('skills.patch_checker.PatchAnalyzer')
    def test_check_file(self, mock_analyzer_cls, mock_evaluator_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"risk_score": 0.0}
        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = True
        eval_result.metrics = {}
        eval_result.reasons = []
        eval_result.telemetry = {}
        eval_result.was_corrected = False
        mock_evaluator_cls.return_value.evaluate.return_value = eval_result

        random_file_path = f"/tmp/{uuid.uuid4().hex}.diff"
        file_content = f"content_{uuid.uuid4().hex}"

        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", unittest.mock.mock_open(read_data=file_content)):

            checker = PatchChecker()
            result = checker.check_file(random_file_path, target_file=self.random_target)
            self.assertTrue(result["is_safe"])

    @patch('skills.patch_checker.PatchEvaluator')
    @patch('skills.patch_checker.PatchAnalyzer')
    def test_check_file_not_found(self, mock_analyzer_cls, mock_evaluator_cls):
        random_file_path = f"/tmp/{uuid.uuid4().hex}.diff"
        with patch("os.path.exists", return_value=False):
            checker = PatchChecker()
            with self.assertRaises(PatchCheckerError):
                checker.check_file(random_file_path)

    @patch('skills.patch_checker.PatchEvaluator')
    @patch('skills.patch_checker.PatchAnalyzer')
    def test_check_stream(self, mock_analyzer_cls, mock_evaluator_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"risk_score": 0.0}
        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = True
        eval_result.metrics = {}
        eval_result.reasons = []
        eval_result.telemetry = {}
        eval_result.was_corrected = False
        mock_evaluator_cls.return_value.evaluate.return_value = eval_result

        stream_content = f"stream_diff_{uuid.uuid4().hex}"
        stream = io.StringIO(stream_content)

        checker = PatchChecker()
        result = checker.check_stream(stream, target_file=self.random_target)
        self.assertTrue(result["is_safe"])

    @patch('skills.patch_checker.PatchEvaluator')
    @patch('skills.patch_checker.PatchAnalyzer')
    def test_check_method_dynamic_repo(self, mock_analyzer_cls, mock_evaluator_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"risk_score": 0.0}
        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = True
        eval_result.metrics = {"metric_key": uuid.uuid4().hex}
        eval_result.reasons = []
        eval_result.telemetry = {}
        eval_result.was_corrected = False
        mock_evaluator_cls.return_value.evaluate.return_value = eval_result

        new_repo = f"/tmp/new_repo_{uuid.uuid4().hex}"
        checker = PatchChecker(repo_path=self.random_repo)

        result = checker.check(patch_content=self.random_patch, repo_path=new_repo, target_file=self.random_target)

        self.assertEqual(checker.repo_path, new_repo)
        self.assertIn("metric_key", result)

    @patch('skills.patch_checker.PatchChecker.check_patch')
    def test_functional_check_patch(self, mock_check_patch):
        expected_dict = {"status": uuid.uuid4().hex}
        mock_check_patch.return_value = expected_dict

        res = check_patch(patch_content=self.random_patch, repo_path=self.random_repo, target_file=self.random_target, policy={})
        self.assertEqual(res, expected_dict)


if __name__ == '__main__':
    unittest.main()