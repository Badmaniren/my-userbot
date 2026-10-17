import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import sys
import os

from skills.patch_pipeline_builder import PatchPipelineBuilder, PatchPipelineError

class TestPatchPipelineBuilder(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.patch_content = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py\n+print('{uuid.uuid4().hex}')"
        self.target_file = f"{uuid.uuid4().hex}.py"

    @patch('skills.patch_pipeline_builder.patch_evaluator')
    @patch('skills.patch_pipeline_builder.PatchVerifier')
    def test_pipeline_builder_success(self, mock_verifier_cls, mock_evaluator_func):
        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = True
        eval_result.was_corrected = random.choice([True, False])
        eval_result.metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        eval_result.reasons = [uuid.uuid4().hex]
        eval_result.telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_evaluator_func.return_value = eval_result

        verifier_instance = mock_verifier_cls.return_value
        verifier_instance.verify_and_apply.return_value = True

        builder = PatchPipelineBuilder(repo_path=self.repo_path)
        result = builder.run_pipeline(self.patch_content, self.target_file)

        self.assertTrue(result)
        mock_evaluator_func.assert_called_once_with(self.repo_path, self.patch_content, self.target_file)
        verifier_instance.verify_and_apply.assert_called_once_with(self.patch_content)

    @patch('skills.patch_pipeline_builder.patch_evaluator')
    @patch('skills.patch_pipeline_builder.PatchVerifier')
    def test_pipeline_builder_eval_unsafe(self, mock_verifier_cls, mock_evaluator_func):
        eval_result = MagicMock()
        eval_result.is_safe = False
        eval_result.is_valid = True
        mock_evaluator_func.return_value = eval_result

        verifier_instance = mock_verifier_cls.return_value

        builder = PatchPipelineBuilder(repo_path=self.repo_path)
        result = builder.run_pipeline(self.patch_content, self.target_file)

        self.assertFalse(result)
        verifier_instance.verify_and_apply.assert_not_called()

    @patch('skills.patch_pipeline_builder.patch_evaluator')
    @patch('skills.patch_pipeline_builder.PatchVerifier')
    def test_pipeline_builder_eval_invalid(self, mock_verifier_cls, mock_evaluator_func):
        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = False
        mock_evaluator_func.return_value = eval_result

        verifier_instance = mock_verifier_cls.return_value

        builder = PatchPipelineBuilder(repo_path=self.repo_path)
        result = builder.run_pipeline(self.patch_content, self.target_file)

        self.assertFalse(result)
        verifier_instance.verify_and_apply.assert_not_called()

    @patch('skills.patch_pipeline_builder.patch_evaluator')
    @patch('skills.patch_pipeline_builder.PatchVerifier')
    def test_pipeline_builder_verification_fails(self, mock_verifier_cls, mock_evaluator_func):
        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = True
        mock_evaluator_func.return_value = eval_result

        verifier_instance = mock_verifier_cls.return_value
        verifier_instance.verify_and_apply.return_value = False

        builder = PatchPipelineBuilder(repo_path=self.repo_path)
        result = builder.run_pipeline(self.patch_content, self.target_file)

        self.assertFalse(result)
        verifier_instance.verify_and_apply.assert_called_once_with(self.patch_content)

    @patch('skills.patch_pipeline_builder.patch_evaluator')
    def test_pipeline_builder_evaluator_exception(self, mock_evaluator_func):
        mock_evaluator_func.side_effect = Exception(uuid.uuid4().hex)

        builder = PatchPipelineBuilder(repo_path=self.repo_path)
        
        with self.assertRaises(PatchPipelineError):
            builder.run_pipeline(self.patch_content, self.target_file)

    @patch('skills.patch_pipeline_builder.patch_evaluator')
    @patch('skills.patch_pipeline_builder.PatchVerifier')
    def test_pipeline_builder_verifier_exception(self, mock_verifier_cls, mock_evaluator_func):
        eval_result = MagicMock()
        eval_result.is_safe = True
        eval_result.is_valid = True
        mock_evaluator_func.return_value = eval_result

        verifier_instance = mock_verifier_cls.return_value
        verifier_instance.verify_and_apply.side_effect = Exception(uuid.uuid4().hex)

        builder = PatchPipelineBuilder(repo_path=self.repo_path)
        
        with self.assertRaises(PatchPipelineError):
            builder.run_pipeline(self.patch_content, self.target_file)

    def test_pipeline_builder_stream_processing(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        
        with patch('skills.patch_pipeline_builder.patch_evaluator') as mock_evaluator_func, \
             patch('skills.patch_pipeline_builder.PatchVerifier') as mock_verifier_cls:
            
            eval_result = MagicMock()
            eval_result.is_safe = True
            eval_result.is_valid = True
            mock_evaluator_func.return_value = eval_result

            verifier_instance = mock_verifier_cls.return_value
            verifier_instance.verify_and_apply.return_value = True

            builder = PatchPipelineBuilder(repo_path=self.repo_path)
            result = builder.run_pipeline_stream(stream_data, self.target_file)

            self.assertTrue(result)
            mock_evaluator_func.assert_called_once()
            verifier_instance.verify_and_apply.assert_called_once()

if __name__ == '__main__':
    unittest.main()