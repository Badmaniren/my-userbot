import unittest
from unittest.mock import patch, MagicMock
import io
import os
import uuid
import random
import string

from skills.patch_checker import (
    PatchChecker,
    PatchCheckerError,
    check_patch,
    _get_val
)
from skills.patch_analyzer import PatchAnalyzerError
from skills.patch_evaluator import PatchEvaluatorError


class TestPatchCheckerInquisition(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/{uuid.uuid4().hex}"
        self.rand_file = f"{uuid.uuid4().hex}.py"
        self.rand_content = f"class Class_{uuid.uuid4().hex[:8]}:\n    pass\n"
        self.checker = PatchChecker(repo_path=self.rand_repo)

    def test_get_val_helper(self):
        key = uuid.uuid4().hex
        val = uuid.uuid4().hex
        fallback = uuid.uuid4().hex

        d = {key: val}
        self.assertEqual(_get_val(d, key, fallback), val)
        self.assertEqual(_get_val(d, "nonexistent", fallback), fallback)

        class Dummy:
            def __init__(self, k, v):
                setattr(self, k, v)

        obj = Dummy(key, val)
        self.assertEqual(_get_val(obj, key, fallback), val)
        self.assertEqual(_get_val(obj, "nonexistent", fallback), fallback)

    def test_check_patch_empty_content(self):
        for empty_val in ["", "   ", None]:
            with self.subTest(empty_val=empty_val):
                with self.assertRaises(PatchCheckerError) as ctx:
                    self.checker.check_patch(patch_content=empty_val)
                self.assertIn("Пустой патч", str(ctx.exception))

    @patch("skills.patch_checker.PatchAnalyzer.analyze")
    def test_check_patch_analyzer_error(self, mock_analyze):
        err_msg = uuid.uuid4().hex
        mock_analyze.side_effect = PatchAnalyzerError(err_msg)

        with self.assertRaises(PatchCheckerError) as ctx:
            self.checker.check_patch(patch_content=self.rand_content)
        self.assertIn("Ошибка анализатора", str(ctx.exception))

    @patch("skills.patch_checker.PatchEvaluator.evaluate")
    @patch("skills.patch_checker.PatchAnalyzer.analyze")
    def test_check_patch_evaluator_error(self, mock_analyze, mock_evaluate):
        mock_analyze.return_value = {"risk_score": 0.1, "syntax_risks": []}
        err_msg = uuid.uuid4().hex
        mock_evaluate.side_effect = PatchEvaluatorError(err_msg)

        with self.assertRaises(PatchCheckerError) as ctx:
            self.checker.check_patch(patch_content=self.rand_content)
        self.assertIn("Ошибка оценщика", str(ctx.exception))

    @patch("skills.patch_checker.PatchEvaluator.evaluate")
    @patch("skills.patch_checker.PatchAnalyzer.analyze")
    def test_check_patch_success_flow(self, mock_analyze, mock_evaluate):
        risk_score_val = round(random.uniform(0.0, 1.0), 2)
        mock_analyze.return_value = {
            "risk_score": risk_score_val,
            "syntax_risks": []
        }

        mock_eval_res = MagicMock()
        mock_eval_res.is_safe = True
        mock_eval_res.is_valid = True
        mock_eval_res.metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        mock_eval_res.reasons = [uuid.uuid4().hex]
        mock_eval_res.telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_eval_res.was_corrected = False

        mock_evaluate.return_value = mock_eval_res

        res = self.checker.check_patch(patch_content=self.rand_content, target_file=self.rand_file)

        self.assertTrue(res["is_safe"])
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["risk_score"], risk_score_val)
        self.assertIn("analysis", res)
        self.assertIn("evaluation", res)
        self.assertEqual(res["evaluation"]["reasons"], mock_eval_res.reasons)

    @patch("skills.patch_checker.PatchEvaluator.evaluate")
    @patch("skills.patch_checker.PatchAnalyzer.analyze")
    def test_policy_strict_safety_violation(self, mock_analyze, mock_evaluate):
        policy = {"strict_safety": True}
        checker_with_policy = PatchChecker(repo_path=self.rand_repo, policy=policy)

        mock_analyze.return_value = {"risk_score": 0.8, "syntax_risks": ["bad_ast"]}

        mock_eval_res = {
            "is_safe": False,
            "is_valid": True,
            "metrics": {},
            "reasons": ["unsafe"],
            "telemetry": {},
            "was_corrected": False
        }
        mock_evaluate.return_value = mock_eval_res

        res = checker_with_policy.check_patch(patch_content=self.rand_content)
        self.assertFalse(res["is_safe"])
        self.assertIn("disallowed_risks", res["policy_verdict"])

    @patch("skills.patch_checker.os.path.exists")
    def test_check_file_not_found(self, mock_exists):
        mock_exists.return_value = False
        nonexistent_path = f"/tmp/{uuid.uuid4().hex}"

        with self.assertRaises(PatchCheckerError) as ctx:
            self.checker.check_file(nonexistent_path)
        self.assertIn("Файл не найден", str(ctx.exception))

    @patch("skills.patch_checker.PatchChecker.check_patch")
    @patch("skills.patch_checker.open", create=True)
    @patch("skills.patch_checker.os.path.exists")
    def test_check_file_success(self, mock_exists, mock_open, mock_check_patch):
        mock_exists.return_value = True
        mock_file = MagicMock()
        mock_file.read.return_value = self.rand_content
        mock_open.return_value.__enter__.return_value = mock_file

        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_check_patch.return_value = expected_dict

        res = self.checker.check_file(self.rand_file, target_file=self.rand_file)
        self.assertEqual(res, expected_dict)
        mock_check_patch.assert_called_once_with(patch_content=self.rand_content, target_file=self.rand_file)

    def test_check_stream_success(self):
        stream_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"
        stream = io.StringIO(stream_content)

        with patch.object(self.checker, "check_patch") as mock_check_patch:
            expected_ret = {uuid.uuid4().hex: True}
            mock_check_patch.return_value = expected_ret

            res = self.checker.check_stream(stream, target_file=self.rand_file)
            self.assertEqual(res, expected_ret)
            mock_check_patch.assert_called_once_with(patch_content=stream_content, target_file=self.rand_file)

    @patch("skills.patch_checker.PatchChecker.check_patch")
    def test_check_integration_method(self, mock_check_patch):
        new_repo = f"/tmp/{uuid.uuid4().hex}"
        new_policy = {uuid.uuid4().hex: uuid.uuid4().hex}
        metrics_dict = {uuid.uuid4().hex: random.randint(1, 50)}

        mock_check_patch.return_value = {
            "evaluation": {
                "metrics": metrics_dict
            }
        }

        res = self.checker.check(
            patch_content=self.rand_content,
            repo_path=new_repo,
            target_file=self.rand_file,
            policy=new_policy
        )

        self.assertEqual(self.checker.repo_path, new_repo)
        self.assertEqual(self.checker.policy, new_policy)
        self.assertIn("metrics", res)
        self.assertEqual(res["metrics"], metrics_dict)

    @patch("skills.patch_checker.PatchChecker.check_patch")
    def test_module_level_check_patch_wrapper(self, mock_check_patch):
        expected_ret = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_check_patch.return_value = expected_ret

        res = check_patch(
            patch_content=self.rand_content,
            repo_path=self.rand_repo,
            target_file=self.rand_file,
            policy={"test": True}
        )
        self.assertEqual(res, expected_ret)


if __name__ == "__main__":
    unittest.main()