import io
import os
import random
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch
from skills.patch_analyzer import PatchAnalyzerError
from skills.patch_evaluator import PatchEvaluatorError


class TestPatchChecker(unittest.TestCase):

    def setUp(self):
        self.random_repo = uuid.uuid4().hex
        self.random_file_path = f"test_dir_{uuid.uuid4().hex}/{uuid.uuid4().hex}.patch"
        self.random_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n+{uuid.uuid4().hex}"
        self.random_target = f"{uuid.uuid4().hex}.py"

    def test_check_patch_empty_content(self):
        checker = PatchChecker(repo_path=self.random_repo)
        for empty_val in ["", "   ", "\n\t "]:
            with self.subTest(empty_val=empty_val):
                with self.assertRaises(PatchCheckerError):
                    checker.check_patch(patch_content=empty_val)

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_patch_analyzer_error(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        err_msg = uuid.uuid4().hex
        mock_analyzer.analyze.side_effect = PatchAnalyzerError(err_msg)

        checker = PatchChecker(repo_path=self.random_repo)
        with self.assertRaises(PatchCheckerError) as ctx:
            checker.check_patch(patch_content=self.random_content)
        self.assertIn(err_msg, str(ctx.exception))

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_patch_evaluator_error(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"syntax_risks": [], "risk_score": random.random()}

        mock_evaluator = mock_evaluator_cls.return_value
        err_msg = uuid.uuid4().hex
        mock_evaluator.evaluate.side_effect = PatchEvaluatorError(err_msg)

        checker = PatchChecker(repo_path=self.random_repo)
        with self.assertRaises(PatchCheckerError) as ctx:
            checker.check_patch(patch_content=self.random_content, target_file=self.random_target)
        self.assertIn(err_msg, str(ctx.exception))

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_patch_success_and_policies(self, mock_evaluator_cls, mock_analyzer_cls):
        risk_score = round(random.uniform(0.1, 0.9), 2)
        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {
            "syntax_risks": [uuid.uuid4().hex],
            "risk_score": risk_score
        }

        mock_evaluator = mock_evaluator_cls.return_value
        eval_result = MagicMock()
        eval_result.is_safe = False
        eval_result.is_valid = True
        eval_result.metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        eval_result.reasons = [uuid.uuid4().hex]
        eval_result.telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}
        eval_result.was_corrected = True
        mock_evaluator.evaluate.return_value = eval_result

        policy = {
            "strict_safety": True,
            "disallow_syntax_risks": True
        }
        checker = PatchChecker(repo_path=self.random_repo, policy=policy)
        result = checker.check_patch(patch_content=self.random_content, target_file=self.random_target)

        self.assertFalse(result["is_safe"])
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["risk_score"], risk_score)
        self.assertIn("disallowed_risks", result["policy_verdict"])
        self.assertEqual(result["evaluation"]["was_corrected"], True)
        self.assertEqual(result["evaluation"]["metrics"], eval_result.metrics)

    @patch("os.path.exists")
    def test_check_file_not_found(self, mock_exists):
        mock_exists.return_value = False
        checker = PatchChecker(repo_path=self.random_repo)
        with self.assertRaises(PatchCheckerError):
            checker.check_file(file_path=self.random_file_path)

    @patch("os.path.exists")
    @patch("builtins.open")
    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_file_success(self, mock_evaluator_cls, mock_analyzer_cls, mock_open, mock_exists):
        mock_exists.return_value = True
        file_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"
        mock_file_instance = MagicMock()
        mock_file_instance.__enter__.return_value.read.return_value = file_content
        mock_open.return_value = mock_file_instance

        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"syntax_risks": [], "risk_score": 0.0}
        mock_evaluator = mock_evaluator_cls.return_value
        mock_evaluator.evaluate.return_value = MagicMock(is_safe=True, is_valid=True)

        checker = PatchChecker(repo_path=self.random_repo)
        res = checker.check_file(file_path=self.random_file_path, target_file=self.random_target)
        self.assertTrue(res["is_safe"])
        mock_open.assert_called_once_with(self.random_file_path, "r", encoding="utf-8")

    def test_check_stream_success(self):
        stream_content = f"patch stream content {uuid.uuid4().hex}"
        stream = io.StringIO(stream_content)

        checker = PatchChecker(repo_path=self.random_repo)
        with patch.object(checker, "check_patch") as mock_check_patch:
            mock_check_patch.return_value = {uuid.uuid4().hex: uuid.uuid4().hex}
            res = checker.check_stream(stream=stream, target_file=self.random_target)
            mock_check_patch.assert_called_once_with(patch_content=stream_content, target_file=self.random_target)

    def test_check_stream_error(self):
        bad_stream = MagicMock(spec=io.TextIOBase)
        bad_stream.read.side_effect = IOError(uuid.uuid4().hex)

        checker = PatchChecker(repo_path=self.random_repo)
        with self.assertRaises(PatchCheckerError):
            checker.check_stream(stream=bad_stream)

    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_integration_method(self, mock_evaluator_cls):
        new_repo = uuid.uuid4().hex
        checker = PatchChecker(repo_path=self.random_repo)

        with patch.object(checker, "check_patch") as mock_check_patch:
            expected_metrics = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_check_patch.return_value = {
                "evaluation": {
                    "metrics": expected_metrics
                }
            }
            res = checker.check(patch_content=self.random_content, repo_path=new_repo, target_file=self.random_target)
            self.assertEqual(checker.repo_path, new_repo)
            self.assertEqual(res["metrics"], expected_metrics)
            mock_check_patch.assert_called_once_with(patch_content=self.random_content, target_file=self.random_target)

    @patch("skills.patch_checker.PatchChecker.check_patch")
    def test_module_level_check_patch_function(self, mock_check_patch):
        ret_val = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_check_patch.return_value = ret_val
        policy = {uuid.uuid4().hex: random.random()}

        result = check_patch(
            patch_content=self.random_content,
            repo_path=self.random_repo,
            target_file=self.random_target,
            policy=policy
        )
        self.assertEqual(result, ret_val)


if __name__ == "__main__":
    unittest.main()