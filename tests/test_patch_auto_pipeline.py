import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
from typing import Dict, Any, Tuple, List

from skills.patch_auto_pipeline import (
    PatchAutoPipeline,
    PatchAutoPipelineError,
    PipelineResult
)

class TestPatchAutoPipeline(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.patch_content = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py\n+print('{uuid.uuid4().hex}')"
        self.target_file = f"{uuid.uuid4().hex}.py"

    @patch('skills.patch_auto_pipeline.PatchEvaluator')
    @patch('skills.patch_auto_pipeline.PatchVerifier')
    def test_pipeline_success_execution(self, mock_verifier_cls, mock_evaluator_cls):
        eval_result_mock = MagicMock()
        eval_result_mock.is_safe = True
        eval_result_mock.is_valid = True
        eval_result_mock.was_corrected = False
        eval_result_mock.metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        eval_result_mock.reasons = [uuid.uuid4().hex]
        eval_result_mock.telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}

        eval_instance = mock_evaluator_cls.return_value
        eval_instance.evaluate.return_value = eval_result_mock

        verifier_instance = mock_verifier_cls.return_value
        verifier_instance.verify_and_apply.return_value = True

        pipeline = PatchAutoPipeline(repo_path=self.repo_path)
        result = pipeline.run(self.patch_content, target_file=self.target_file)

        mock_evaluator_cls.assert_called_once_with(repo_path=self.repo_path)
        eval_instance.evaluate.assert_called_once_with(
            patch_content=self.patch_content,
            collect_telemetry=True,
            target_file=self.target_file
        )
        verifier_instance.verify_and_apply.assert_called_once_with(self.patch_content)

        self.assertIsInstance(result, PipelineResult)
        self.assertTrue(result.success)
        self.assertTrue(result.evaluation.is_safe)
        self.assertTrue(result.evaluation.is_valid)

    @patch('skills.patch_auto_pipeline.PatchEvaluator')
    @patch('skills.patch_auto_pipeline.PatchVerifier')
    def test_pipeline_evaluation_fails_safety(self, mock_verifier_cls, mock_evaluator_cls):
        eval_result_mock = MagicMock()
        eval_result_mock.is_safe = False
        eval_result_mock.is_valid = True
        eval_result_mock.was_corrected = False
        eval_result_mock.reasons = [uuid.uuid4().hex]

        eval_instance = mock_evaluator_cls.return_value
        eval_instance.evaluate.return_value = eval_result_mock

        verifier_instance = mock_verifier_cls.return_value

        pipeline = PatchAutoPipeline(repo_path=self.repo_path)
        result = pipeline.run(self.patch_content, target_file=self.target_file)

        eval_instance.evaluate.assert_called_once()
        verifier_instance.verify_and_apply.assert_not_called()

        self.assertFalse(result.success)
        self.assertFalse(result.evaluation.is_safe)

    @patch('skills.patch_auto_pipeline.PatchEvaluator')
    @patch('skills.patch_auto_pipeline.PatchVerifier')
    def test_pipeline_verification_fails(self, mock_verifier_cls, mock_evaluator_cls):
        eval_result_mock = MagicMock()
        eval_result_mock.is_safe = True
        eval_result_mock.is_valid = True
        eval_result_mock.was_corrected = False

        eval_instance = mock_evaluator_cls.return_value
        eval_instance.evaluate.return_value = eval_result_mock

        verifier_instance = mock_verifier_cls.return_value
        verifier_instance.verify_and_apply.return_value = False

        pipeline = PatchAutoPipeline(repo_path=self.repo_path)
        result = pipeline.run(self.patch_content, target_file=self.target_file)

        eval_instance.evaluate.assert_called_once()
        verifier_instance.verify_and_apply.assert_called_once_with(self.patch_content)

        self.assertFalse(result.success)
        self.assertTrue(result.evaluation.is_safe)

    @patch('skills.patch_auto_pipeline.PatchEvaluator')
    @patch('skills.patch_auto_pipeline.PatchVerifier')
    def test_pipeline_with_autocorrect_flow(self, mock_verifier_cls, mock_evaluator_cls):
        eval_result_mock = MagicMock()
        eval_result_mock.is_safe = True
        eval_result_mock.is_valid = True
        eval_result_mock.was_corrected = True

        eval_instance = mock_evaluator_cls.return_value
        eval_instance.evaluate_with_autocorrect.return_value = eval_result_mock

        verifier_instance = mock_verifier_cls.return_value
        verifier_instance.verify_and_apply.return_value = True

        pipeline = PatchAutoPipeline(repo_path=self.repo_path)
        result = pipeline.run(self.patch_content, target_file=self.target_file, use_autocorrect=True)

        eval_instance.evaluate_with_autocorrect.assert_called_once_with(self.patch_content)
        verifier_instance.verify_and_apply.assert_called_once_with(self.patch_content)

        self.assertTrue(result.success)
        self.assertTrue(result.evaluation.was_corrected)

    @patch('skills.patch_auto_pipeline.PatchEvaluator')
    @patch('skills.patch_auto_pipeline.PatchVerifier')
    def test_pipeline_raises_custom_exception_on_error(self, mock_verifier_cls, mock_evaluator_cls):
        eval_instance = mock_evaluator_cls.return_value
        eval_instance.evaluate.side_effect = Exception(uuid.uuid4().hex)

        pipeline = PatchAutoPipeline(repo_path=self.repo_path)
        with self.assertRaises(PatchAutoPipelineError):
            pipeline.run(self.patch_content, target_file=self.target_file)

    @patch('skills.patch_auto_pipeline.PatchEvaluator')
    @patch('skills.patch_auto_pipeline.PatchVerifier')
    def test_pipeline_stream_processing(self, mock_verifier_cls, mock_evaluator_cls):
        stream_data = io.BytesIO(self.patch_content.encode('utf-8'))

        eval_result_mock = MagicMock()
        eval_result_mock.is_safe = True
        eval_result_mock.is_valid = True

        eval_instance = mock_evaluator_cls.return_value
        eval_instance.evaluate_stream.return_value = eval_result_mock

        verifier_instance = mock_verifier_cls.return_value
        verifier_instance.verify_and_apply.return_value = True

        pipeline = PatchAutoPipeline(repo_path=self.repo_path)
        result = pipeline.run_stream(stream_data)

        eval_instance.evaluate_stream.assert_called_once_with(stream_data)
        verifier_instance.verify_and_apply.assert_called_once()
        self.assertTrue(result.success)