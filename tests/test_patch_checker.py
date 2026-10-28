import io
import os
import random
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch


class TestPatchCheckerInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path_val = uuid.uuid4().hex
        self.policy_val = {
            "strict_safety": random.choice([True, False]),
            "disallow_syntax_risks": random.choice([True, False])
        }
        self.checker = PatchChecker(repo_path=self.repo_path_val, policy=self.policy_val)

    @patch("skills.patch_checker.PatchEvaluator")
    @patch("skills.patch_checker.PatchAnalyzer")
    def test_check_patch_empty_content(self, mock_analyzer_cls, mock_evaluator_cls):
        empty_content = random.choice(["", "   ", "\n\t "])
        with self.assertRaises(PatchCheckerError) as ctx:
            self.checker.check_patch(empty_content)
        self.assertIn("Пустой патч", str(ctx.exception))

    @patch("skills.patch_checker.PatchEvaluator")
    @patch("skills.patch_checker.PatchAnalyzer")
    def test_check_patch_success(self, mock_analyzer_cls, mock_evaluator_cls):
        checker = PatchChecker(repo_path=self.repo_path_val, policy=self.policy_val)
        mock_analyzer = mock_analyzer_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value

        risk_score_val = random.uniform(0.1, 0.9)
        syntax_risks_val = [uuid.uuid4().hex, uuid.uuid4().hex]
        mock_analyzer.analyze.return_value = {
            "risk_score": risk_score_val,
            "syntax_risks": syntax_risks_val
        }

        mock_eval_result = MagicMock()
        mock_eval_result.is_safe = True
        mock_eval_result.is_valid = True
        mock_eval_result.metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        mock_eval_result.reasons = [uuid.uuid4().hex]
        mock_eval_result.telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_eval_result.was_corrected = random.choice([True, False])
        mock_evaluator.evaluate.return_value = mock_eval_result

        patch_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n+print('{uuid.uuid4().hex}')"
        target_file_val = uuid.uuid4().hex

        result = checker.check_patch(patch_content, target_file=target_file_val)

        self.assertIn("is_safe", result)
        self.assertIn("is_valid", result)
        self.assertEqual(result["risk_score"], risk_score_val)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)
        self.assertIn("policy_verdict", result)
        mock_analyzer.analyze.assert_called_once_with(patch_content)
        mock_evaluator.evaluate.assert_called_once_with(
            patch_content=patch_content,
            target_file=target_file_val
        )

    @patch("skills.patch_checker.PatchEvaluator")
    @patch("skills.patch_checker.PatchAnalyzer")
    def test_check_file_not_found(self, mock_analyzer_cls, mock_evaluator_cls):
        missing_file = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}.patch"
        with self.assertRaises(PatchCheckerError) as ctx:
            self.checker.check_file(missing_file)
        self.assertIn("Файл не найден", str(ctx.exception))

    @patch("skills.patch_checker.PatchEvaluator")
    @patch("skills.patch_checker.PatchAnalyzer")
    def test_check_file_success(self, mock_analyzer_cls, mock_evaluator_cls):
        checker = PatchChecker(repo_path=self.repo_path_val, policy=self.policy_val)
        mock_analyzer = mock_analyzer_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value

        mock_analyzer.analyze.return_value = {"risk_score": 0.0, "syntax_risks": []}
        mock_eval_result = MagicMock()
        mock_eval_result.is_safe = True
        mock_eval_result.is_valid = True
        mock_eval_result.metrics = {}
        mock_eval_result.reasons = []
        mock_eval_result.telemetry = {}
        mock_eval_result.was_corrected = False
        mock_evaluator.evaluate.return_value = mock_eval_result

        file_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"
        file_path = f"/tmp/{uuid.uuid4().hex}.patch"

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", unittest.mock.mock_open(read_data=file_content)):
                res = checker.check_file(file_path)
                self.assertIsInstance(res, dict)

    @patch("skills.patch_checker.PatchEvaluator")
    @patch("skills.patch_checker.PatchAnalyzer")
    def test_check_stream_success(self, mock_analyzer_cls, mock_evaluator_cls):
        checker = PatchChecker(repo_path=self.repo_path_val, policy=self.policy_val)
        mock_analyzer = mock_analyzer_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value

        mock_analyzer.analyze.return_value = {"risk_score": 0.0, "syntax_risks": []}
        mock_eval_result = MagicMock()
        mock_eval_result.is_safe = True
        mock_eval_result.is_valid = True
        mock_eval_result.metrics = {}
        mock_eval_result.reasons = []
        mock_eval_result.telemetry = {}
        mock_eval_result.was_corrected = False
        mock_evaluator.evaluate.return_value = mock_eval_result

        stream_data = f"stream content {uuid.uuid4().hex}"
        stream = io.StringIO(stream_data)

        res = checker.check_stream(stream)
        self.assertIsInstance(res, dict)

    @patch("skills.patch_checker.PatchEvaluator")
    @patch("skills.patch_checker.PatchAnalyzer")
    def test_check_method_with_repo_path_switch(self, mock_analyzer_cls, mock_evaluator_cls):
        checker = PatchChecker(repo_path=self.repo_path_val, policy=self.policy_val)
        mock_analyzer = mock_analyzer_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value

        mock_analyzer.analyze.return_value = {"risk_score": 0.0, "syntax_risks": []}
        mock_eval_result = MagicMock()
        mock_eval_result.is_safe = True
        mock_eval_result.is_valid = True
        mock_eval_result.metrics = {uuid.uuid4().hex: random.randint(10, 50)}
        mock_eval_result.reasons = []
        mock_eval_result.telemetry = {}
        mock_eval_result.was_corrected = False
        mock_evaluator.evaluate.return_value = mock_eval_result

        new_repo_path = uuid.uuid4().hex
        patch_content = f"diff {uuid.uuid4().hex}"

        res = checker.check(patch_content=patch_content, repo_path=new_repo_path)
        self.assertEqual(checker.repo_path, new_repo_path)
        self.assertIn("metrics", res)

    @patch("skills.patch_checker.PatchChecker.check_patch")
    def test_functional_check_patch_helper(self, mock_check_patch):
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_check_patch.return_value = expected_dict

        p_content = uuid.uuid4().hex
        r_path = uuid.uuid4().hex
        t_file = uuid.uuid4().hex
        pol = {uuid.uuid4().hex: uuid.uuid4().hex}

        res = check_patch(patch_content=p_content, repo_path=r_path, target_file=t_file, policy=pol)
        self.assertEqual(res, expected_dict)


if __name__ == "__main__":
    unittest.main()