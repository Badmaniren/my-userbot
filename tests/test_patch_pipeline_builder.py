import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import sys

from skills.patch_pipeline_builder import PatchPipelineBuilder, PatchPipelineBuilderError

class TestPatchPipelineBuilder(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.patch_content = f"diff --git a/test.py b/test.py\n+{uuid.uuid4().hex}"
        self.target_file = f"src/{uuid.uuid4().hex}.py"

    @patch('skills.patch_pipeline_builder.PatchEvaluator')
    @patch('skills.patch_pipeline_builder.PatchVerifier')
    def test_pipeline_builder_initialization(self, mock_verifier_cls, mock_evaluator_cls):
        builder = PatchPipelineBuilder(repo_path=self.repo_path)
        mock_evaluator_cls.assert_called_once_with(repo_path=self.repo_path)
        mock_verifier_cls.assert_called_once()
        self.assertEqual(builder.repo_path, self.repo_path)

    @patch('skills.patch_pipeline_builder.PatchEvaluator')
    @patch('skills.patch_pipeline_builder.PatchVerifier')
    def test_run_pipeline_success(self, mock_verifier_cls, mock_evaluator_cls):
        evaluator_instance = mock_evaluator_cls.return_value
        verifier_instance = mock_verifier_cls.return_value

        expected_metric_key = uuid.uuid4().hex
        expected_metric_val = random.randint(1, 100)
        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = True
        eval_result.metrics = {expected_metric_key: expected_metric_val}
        evaluator_instance.evaluate.return_value = eval_result
        verifier_instance.verify_and_apply.return_value = True

        builder = PatchPipelineBuilder(repo_path=self.repo_path)
        result = builder.run_pipeline(self.patch_content, self.target_file)

        self.assertTrue(result["success"])
        self.assertTrue(result["evaluation"].is_safe)
        self.assertTrue(result["verification"])
        self.assertEqual(result["evaluation"].metrics[expected_metric_key], expected_metric_val)
        evaluator_instance.evaluate.assert_called_once_with(self.patch_content, collect_telemetry=True, target_file=self.target_file)
        verifier_instance.verify_and_apply.assert_called_once_with({"content": self.patch_content, "target_file": self.target_file})

    @patch('skills.patch_pipeline_builder.PatchEvaluator')
    @patch('skills.patch_pipeline_builder.PatchVerifier')
    def test_run_pipeline_unsafe_patch(self, mock_verifier_cls, mock_evaluator_cls):
        evaluator_instance = mock_evaluator_cls.return_value
        verifier_instance = mock_verifier_cls.return_value

        eval_result = MagicMock()
        eval_result.is_safe = False
        eval_result.is_valid = True
        evaluator_instance.evaluate.return_value = eval_result

        builder = PatchPipelineBuilder(repo_path=self.repo_path)
        result = builder.run_pipeline(self.patch_content, self.target_file)

        self.assertFalse(result["success"])
        self.assertFalse(result["evaluation"].is_safe)
        verifier_instance.verify_and_apply.assert_not_called()

    @patch('skills.patch_pipeline_builder.PatchEvaluator')
    @patch('skills.patch_pipeline_builder.PatchVerifier')
    def test_run_pipeline_verification_failure(self, mock_verifier_cls, mock_evaluator_cls):
        evaluator_instance = mock_evaluator_cls.return_value
        verifier_instance = mock_verifier_cls.return_value

        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = True
        evaluator_instance.evaluate.return_value = eval_result
        verifier_instance.verify_and_apply.return_value = False

        builder = PatchPipelineBuilder(repo_path=self.repo_path)
        result = builder.run_pipeline(self.patch_content, self.target_file)

        self.assertFalse(result["success"])
        self.assertTrue(result["evaluation"].is_safe)
        self.assertFalse(result["verification"])
        verifier_instance.verify_and_apply.assert_called_once_with({"content": self.patch_content, "target_file": self.target_file})

    @patch('skills.patch_pipeline_builder.PatchEvaluator')
    @patch('skills.patch_pipeline_builder.PatchVerifier')
    def test_run_pipeline_evaluator_exception_raises_builder_error(self, mock_verifier_cls, mock_evaluator_cls):
        evaluator_instance = mock_evaluator_cls.return_value
        evaluator_instance.evaluate.side_effect = Exception(uuid.uuid4().hex)

        builder = PatchPipelineBuilder(repo_path=self.repo_path)
        with self.assertRaises(PatchPipelineBuilderError):
            builder.run_pipeline(self.patch_content, self.target_file)

    @patch('skills.patch_pipeline_builder.PatchEvaluator')
    @patch('skills.patch_pipeline_builder.PatchVerifier')
    def test_stream_pipeline_processing(self, mock_verifier_cls, mock_evaluator_cls):
        evaluator_instance = mock_evaluator_cls.return_value
        verifier_instance = mock_verifier_cls.return_value

        stream_data = io.BytesIO(self.patch_content.encode('utf-8'))
        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = True
        evaluator_instance.evaluate_stream.return_value = eval_result
        verifier_instance.verify_and_apply.return_value = True

        builder = PatchPipelineBuilder(repo_path=self.repo_path)
        result = builder.run_stream_pipeline(stream_data)

        self.assertTrue(result["success"])
        evaluator_instance.evaluate_stream.assert_called_once_with(stream_data)
        verifier_instance.verify_and_apply.assert_called_once()

if __name__ == '__main__':
    unittest.main()