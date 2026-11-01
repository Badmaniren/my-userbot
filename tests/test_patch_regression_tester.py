import unittest
from unittest.mock import patch
import uuid
import random
import io

from skills.patch_regression_tester import (
    start_new,
    PatchEvaluator,
    GitInspector,
    PatchSanitizer,
    PatchRegressionTester,
    patch_regression_tester
)

class TestPatchRegressionTesterInquisition(unittest.TestCase):

    def setUp(self):
        self.random_patch_id = uuid.uuid4().hex
        self.random_tolerance = round(random.uniform(0.1, 0.9), 2)
        self.random_stream_data = uuid.uuid4().bytes

    def test_start_new_raises_type_error(self):
        invalid_data = uuid.uuid4().hex
        with self.assertRaises(TypeError):
            start_new(invalid_data)

    def test_start_new_stable_branch(self):
        payload = {
            "patch_id": self.random_patch_id,
            "tolerance": self.random_tolerance
        }
        with patch("skills.patch_regression_tester.PatchEvaluator.evaluate") as mock_eval, \
             patch("skills.patch_regression_tester.GitInspector.analyze_repository") as mock_analyze:
            
            mock_eval.return_value = {}
            mock_analyze.return_value = True

            res = start_new(payload)
            self.assertEqual(res["status"], "stable")
            self.assertEqual(res["verified_patch"], self.random_patch_id)
            self.assertEqual(res["score"], self.random_tolerance)

    def test_start_new_with_stream_ref(self):
        stream = io.BytesIO(self.random_stream_data)
        payload = {
            "stream_ref": stream,
            "patch_id": self.random_patch_id,
            "tolerance": self.random_tolerance
        }
        with patch("skills.patch_regression_tester.PatchSanitizer.sanitize_stream") as mock_sanitize, \
             patch("skills.patch_regression_tester.GitInspector.analyze_repository") as mock_analyze, \
             patch("skills.patch_regression_tester.PatchEvaluator.evaluate") as mock_eval:
            
            mock_eval.return_value = {}
            mock_analyze.return_value = True

            res = start_new(payload)
            mock_sanitize.assert_called_once_with(stream)
            self.assertEqual(res["verified_patch"], self.random_patch_id)

    def test_start_new_evaluator_returns_data(self):
        custom_key = uuid.uuid4().hex
        custom_val = uuid.uuid4().hex
        payload = {
            "patch_id": self.random_patch_id,
            custom_key: custom_val
        }
        with patch("skills.patch_regression_tester.PatchEvaluator.evaluate") as mock_eval, \
             patch("skills.patch_regression_tester.GitInspector.analyze_repository") as mock_analyze:
            
            mock_eval.return_value = {custom_key: custom_val}
            mock_analyze.return_value = True

            res = start_new(payload)
            self.assertEqual(res.get(custom_key), custom_val)
            self.assertNotIn("status", res)

    def test_git_inspector_methods(self):
        repo_path_mock = uuid.uuid4().hex
        inspector = GitInspector(repo_path=repo_path_mock)
        self.assertEqual(inspector.repo_path, repo_path_mock)
        self.assertTrue(inspector.analyze_repository())
        self.assertEqual(inspector.get_commit_history(), [])

    def test_patch_evaluator_default(self):
        evaluator = PatchEvaluator()
        self.assertEqual(evaluator.evaluate({}), {})

    def test_patch_sanitizer_identity(self):
        sanitizer = PatchSanitizer()
        stream = io.BytesIO(self.random_stream_data)
        self.assertEqual(sanitizer.sanitize_stream(stream), stream)

    def test_regression_tester_instance(self):
        self.assertIsInstance(patch_regression_tester, PatchRegressionTester)

if __name__ == "__main__":
    unittest.main()