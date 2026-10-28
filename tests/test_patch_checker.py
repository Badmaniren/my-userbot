import unittest
from unittest.mock import patch, MagicMock
import io
import os
import uuid
import random
import string

from skills.patch_checker import PatchChecker, PatchCheckerError, check_patch
from skills.patch_analyzer import PatchAnalyzerError
from skills.patch_evaluator import PatchEvaluationResult, PatchEvaluatorError


class TestPatchChecker(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/{uuid.uuid4().hex}"
        self.rand_patch = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\nindex {uuid.uuid4().hex[:8]}..{uuid.uuid4().hex[:8]}\n--- a/file\n+++ b/file\n@@ -1,1 +1,1 @@\n-{uuid.uuid4().hex}\n+{uuid.uuid4().hex}"
        self.rand_file_path = f"/tmp/{uuid.uuid4().hex}.patch"

    def tearDown(self):
        if os.path.exists(self.rand_file_path):
            try:
                os.remove(self.rand_file_path)
            except OSError:
                pass

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_patch_success(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value

        risk_val = round(random.uniform(0.0, 1.0), 2)
        mock_analyzer.analyze.return_value = {
            "syntax_risks": [],
            "risk_score": risk_val
        }

        eval_res = MagicMock()
        eval_res.is_safe = True
        eval_res.is_valid = True
        eval_res.metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        eval_res.reasons = [uuid.uuid4().hex]
        eval_res.telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}
        eval_res.was_corrected = False
        mock_evaluator.evaluate.return_value = eval_res

        checker = PatchChecker(repo_path=self.rand_repo)
        result = checker.check_patch(self.rand_patch)

        self.assertTrue(result["is_safe"])
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["risk_score"], risk_val)
        self.assertIn("analysis", result)
        self.assertIn("evaluation", result)

    def test_check_patch_empty_content(self):
        checker = PatchChecker(repo_path=self.rand_repo)
        for empty_val in ["", "   ", "\n\t "]:
            with self.subTest(empty_val=empty_val):
                with self.assertRaises(PatchCheckerError):
                    checker.check_patch(empty_val)

    @patch("skills.patch_checker.PatchAnalyzer")
    def test_check_patch_analyzer_error(self, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        err_msg = uuid.uuid4().hex
        mock_analyzer.analyze.side_effect = PatchAnalyzerError(err_msg)

        checker = PatchChecker(repo_path=self.rand_repo)
        with self.assertRaises(PatchCheckerError) as ctx:
            checker.check_patch(self.rand_patch)
        self.assertIn(err_msg, str(ctx.exception))

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_patch_evaluator_error(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value

        mock_analyzer.analyze.return_value = {"syntax_risks": [], "risk_score": 0.0}
        err_msg = uuid.uuid4().hex
        mock_evaluator.evaluate.side_effect = PatchEvaluatorError(err_msg)

        checker = PatchChecker(repo_path=self.rand_repo)
        with self.assertRaises(PatchCheckerError) as ctx:
            checker.check_patch(self.rand_patch)
        self.assertIn(err_msg, str(ctx.exception))

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_policy_strict_safety_violation(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value

        mock_analyzer.analyze.return_value = {"syntax_risks": [], "risk_score": 0.9}

        eval_res = MagicMock()
        eval_res.is_safe = False
        eval_res.is_valid = True
        eval_res.metrics = {}
        eval_res.reasons = []
        eval_res.telemetry = {}
        eval_res.was_corrected = False
        mock_evaluator.evaluate.return_value = eval_res

        policy = {"strict_safety": True}
        checker = PatchChecker(repo_path=self.rand_repo, policy=policy)
        result = checker.check_patch(self.rand_patch)

        self.assertIn("disallowed_risks", result["policy_verdict"])

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_policy_disallow_syntax_risks(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value

        mock_analyzer.analyze.return_value = {
            "syntax_risks": [uuid.uuid4().hex],
            "risk_score": 0.5
        }

        eval_res = MagicMock()
        eval_res.is_safe = True
        eval_res.is_valid = True
        eval_res.metrics = {}
        eval_res.reasons = []
        eval_res.telemetry = {}
        eval_res.was_corrected = False
        mock_evaluator.evaluate.return_value = eval_res

        policy = {"disallow_syntax_risks": True}
        checker = PatchChecker(repo_path=self.rand_repo, policy=policy)
        result = checker.check_patch(self.rand_patch)

        self.assertIn("disallowed_risks", result["policy_verdict"])

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_file_success(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value

        mock_analyzer.analyze.return_value = {"syntax_risks": [], "risk_score": 0.1}
        eval_res = MagicMock()
        eval_res.is_safe = True
        eval_res.is_valid = True
        eval_res.metrics = {}
        eval_res.reasons = []
        eval_res.telemetry = {}
        eval_res.was_corrected = False
        mock_evaluator.evaluate.return_value = eval_res

        file_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"
        with open(self.rand_file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        checker = PatchChecker(repo_path=self.rand_repo)
        result = checker.check_file(self.rand_file_path)

        self.assertTrue(result["is_safe"])
        self.assertTrue(result["is_valid"])

    def test_check_file_not_found(self):
        missing_file = f"/tmp/{uuid.uuid4().hex}.patch"
        checker = PatchChecker(repo_path=self.rand_repo)
        with self.assertRaises(PatchCheckerError):
            checker.check_file(missing_file)

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_stream_success(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value

        mock_analyzer.analyze.return_value = {"syntax_risks": [], "risk_score": 0.0}
        eval_res = MagicMock()
        eval_res.is_safe = True
        eval_res.is_valid = True
        eval_res.metrics = {}
        eval_res.reasons = []
        eval_res.telemetry = {}
        eval_res.was_corrected = False
        mock_evaluator.evaluate.return_value = eval_res

        stream_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"
        stream = io.StringIO(stream_content)

        checker = PatchChecker(repo_path=self.rand_repo)
        result = checker.check_stream(stream)

        self.assertTrue(result["is_safe"])

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_check_integration_method(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value

        mock_analyzer.analyze.return_value = {"syntax_risks": [], "risk_score": 0.2}
        metric_key = uuid.uuid4().hex
        metric_val = random.randint(10, 500)
        eval_res = MagicMock()
        eval_res.is_safe = True
        eval_res.is_valid = True
        eval_res.metrics = {metric_key: metric_val}
        eval_res.reasons = []
        eval_res.telemetry = {}
        eval_res.was_corrected = False
        mock_evaluator.evaluate.return_value = eval_res

        new_repo = f"/tmp/{uuid.uuid4().hex}"
        checker = PatchChecker(repo_path=self.rand_repo)
        result = checker.check(patch_content=self.rand_patch, repo_path=new_repo)

        self.assertEqual(checker.repo_path, new_repo)
        self.assertIn("metrics", result)
        self.assertEqual(result["metrics"][metric_key], metric_val)

    @patch("skills.patch_checker.PatchAnalyzer")
    @patch("skills.patch_checker.PatchEvaluator")
    def test_functional_helper_check_patch(self, mock_evaluator_cls, mock_analyzer_cls):
        mock_analyzer = mock_analyzer_cls.return_value
        mock_evaluator = mock_evaluator_cls.return_value

        mock_analyzer.analyze.return_value = {"syntax_risks": [], "risk_score": 0.3}
        eval_res = MagicMock()
        eval_res.is_safe = True
        eval_res.is_valid = True
        eval_res.metrics = {}
        eval_res.reasons = []
        eval_res.telemetry = {}
        eval_res.was_corrected = False
        mock_evaluator.evaluate.return_value = eval_res

        policy = {uuid.uuid4().hex: True}
        result = check_patch(patch_content=self.rand_patch, repo_path=self.rand_repo, policy=policy)

        self.assertTrue(result["is_safe"])
        self.assertTrue(result["is_valid"])


if __name__ == "__main__":
    unittest.main()