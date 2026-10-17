import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.patch_pipeline_runner import PatchPipelineRunner, PatchPipelineError


class TestPatchPipelineRunner(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.patch_content = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py\n+print('{uuid.uuid4().hex}')"
        self.target_file = f"{uuid.uuid4().hex}.py"
        self.commit_hash = uuid.uuid4().hex

    def test_pipeline_runner_success(self):
        with patch('skills.patch_pipeline_runner.PatchEvaluator') as mock_evaluator_cls, \
             patch('skills.patch_pipeline_runner.GitInspector') as mock_inspector_cls:

            mock_evaluator = mock_evaluator_cls.return_value
            mock_evaluation_result = MagicMock()
            mock_evaluation_result.is_safe = True
            mock_evaluation_result.is_valid = True
            mock_evaluator.evaluate.return_value = mock_evaluation_result

            mock_inspector = mock_inspector_cls.return_value
            expected_history = [{uuid.uuid4().hex: uuid.uuid4().hex}]
            mock_inspector.get_commit_history.return_value = expected_history

            runner = PatchPipelineRunner(repo_path=self.repo_path)
            result = runner.run_pipeline(patch_content=self.patch_content, target_file=self.target_file)

            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("commit_history"), expected_history)
            mock_evaluator.evaluate.assert_called_once_with(
                patch_content=self.patch_content,
                collect_telemetry=True,
                target_file=self.target_file
            )
            mock_inspector.get_commit_history.assert_called_once()

    def test_pipeline_runner_unsafe_patch(self):
        with patch('skills.patch_pipeline_runner.PatchEvaluator') as mock_evaluator_cls, \
             patch('skills.patch_pipeline_runner.GitInspector') as mock_inspector_cls:

            mock_evaluator = mock_evaluator_cls.return_value
            mock_evaluation_result = MagicMock()
            mock_evaluation_result.is_safe = False
            mock_evaluation_result.is_valid = True
            mock_evaluator.evaluate.return_value = mock_evaluation_result

            runner = PatchPipelineRunner(repo_path=self.repo_path)
            
            with self.assertRaises(PatchPipelineError):
                runner.run_pipeline(patch_content=self.patch_content, target_file=self.target_file)

            mock_inspector_cls.return_value.get_commit_history.assert_not_called()

    def test_pipeline_runner_invalid_patch(self):
        with patch('skills.patch_pipeline_runner.PatchEvaluator') as mock_evaluator_cls, \
             patch('skills.patch_pipeline_runner.GitInspector') as mock_inspector_cls:

            mock_evaluator = mock_evaluator_cls.return_value
            mock_evaluation_result = MagicMock()
            mock_evaluation_result.is_safe = True
            mock_evaluation_result.is_valid = False
            mock_evaluator.evaluate.return_value = mock_evaluation_result

            runner = PatchPipelineRunner(repo_path=self.repo_path)
            
            with self.assertRaises(PatchPipelineError):
                runner.run_pipeline(patch_content=self.patch_content, target_file=self.target_file)

    def test_pipeline_runner_inspection_failure(self):
        with patch('skills.patch_pipeline_runner.PatchEvaluator') as mock_evaluator_cls, \
             patch('skills.patch_pipeline_runner.GitInspector') as mock_inspector_cls:

            mock_evaluator = mock_evaluator_cls.return_value
            mock_evaluation_result = MagicMock()
            mock_evaluation_result.is_safe = True
            mock_evaluation_result.is_valid = True
            mock_evaluator.evaluate.return_value = mock_evaluation_result

            mock_inspector = mock_inspector_cls.return_value
            mock_inspector.get_commit_history.side_effect = Exception(uuid.uuid4().hex)

            runner = PatchPipelineRunner(repo_path=self.repo_path)
            
            with self.assertRaises(PatchPipelineError):
                runner.run_pipeline(patch_content=self.patch_content, target_file=self.target_file)


if __name__ == '__main__':
    unittest.main()