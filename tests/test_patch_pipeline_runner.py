import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.patch_pipeline_runner import PatchPipelineRunner, PatchPipelineError
from skills.patch_evaluator import PatchEvaluationResult


class TestPatchPipelineRunnerInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.runner = PatchPipelineRunner(repo_path=self.repo_path)

    @patch('skills.patch_pipeline_runner.PatchEvaluator')
    @patch('skills.patch_pipeline_runner.GitInspector')
    def test_run_pipeline_success(self, mock_git_inspector_cls, mock_patch_evaluator_cls):
        patch_content = f"print('{uuid.uuid4().hex}')"
        target_file = f"src/{uuid.uuid4().hex}.py"
        expected_history = [{"commit": uuid.uuid4().hex, "message": uuid.uuid4().hex}]

        mock_evaluator_instance = mock_patch_evaluator_cls.return_value
        mock_evaluation_result = MagicMock(spec=PatchEvaluationResult)
        mock_evaluation_result.is_safe = True
        mock_evaluation_result.is_valid = True
        mock_evaluation_result.metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        mock_evaluator_instance.evaluate.return_value = mock_evaluation_result

        mock_inspector_instance = mock_git_inspector_cls.return_value
        mock_inspector_instance.get_commit_history.return_value = expected_history

        runner = PatchPipelineRunner(repo_path=self.repo_path)
        result = runner.run_pipeline(patch_content=patch_content, target_file=target_file)

        mock_evaluator_instance.evaluate.assert_called_once_with(
            patch_content=patch_content,
            collect_telemetry=True,
            target_file=target_file
        )
        mock_inspector_instance.get_commit_history.assert_called_once()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("commit_history"), expected_history)
        self.assertTrue(result["success"])
        self.assertEqual(result["commit_history"], expected_history)
        self.assertEqual(result.metrics, mock_evaluation_result.metrics)

    @patch('skills.patch_pipeline_runner.PatchEvaluator')
    @patch('skills.patch_pipeline_runner.GitInspector')
    def test_run_pipeline_unsafe_patch(self, mock_git_inspector_cls, mock_patch_evaluator_cls):
        patch_content = f"import os; os.system('{uuid.uuid4().hex}')"
        target_file = f"src/{uuid.uuid4().hex}.py"

        mock_evaluator_instance = mock_patch_evaluator_cls.return_value
        mock_evaluation_result = MagicMock(spec=PatchEvaluationResult)
        mock_evaluation_result.is_safe = False
        mock_evaluation_result.is_valid = True
        mock_evaluator_instance.evaluate.return_value = mock_evaluation_result

        runner = PatchPipelineRunner(repo_path=self.repo_path)

        with self.assertRaises(PatchPipelineError) as ctx:
            runner.run_pipeline(patch_content=patch_content, target_file=target_file)

        self.assertIn("Patch is unsafe or invalid", str(ctx.exception))
        mock_git_inspector_cls.return_value.get_commit_history.assert_not_called()

    @patch('skills.patch_pipeline_runner.PatchEvaluator')
    @patch('skills.patch_pipeline_runner.GitInspector')
    def test_run_pipeline_invalid_patch(self, mock_git_inspector_cls, mock_patch_evaluator_cls):
        patch_content = f"def {uuid.uuid4().hex}("
        target_file = f"src/{uuid.uuid4().hex}.py"

        mock_evaluator_instance = mock_patch_evaluator_cls.return_value
        mock_evaluation_result = MagicMock(spec=PatchEvaluationResult)
        mock_evaluation_result.is_safe = True
        mock_evaluation_result.is_valid = False
        mock_evaluator_instance.evaluate.return_value = mock_evaluation_result

        runner = PatchPipelineRunner(repo_path=self.repo_path)

        with self.assertRaises(PatchPipelineError) as ctx:
            runner.run_pipeline(patch_content=patch_content, target_file=target_file)

        self.assertIn("Patch is unsafe or invalid", str(ctx.exception))
        mock_git_inspector_cls.return_value.get_commit_history.assert_not_called()

    @patch('skills.patch_pipeline_runner.PatchEvaluator')
    @patch('skills.patch_pipeline_runner.GitInspector')
    def test_run_pipeline_evaluator_exception(self, mock_git_inspector_cls, mock_patch_evaluator_cls):
        patch_content = f"x = {random.randint(1, 500)}"
        target_file = f"src/{uuid.uuid4().hex}.py"
        error_msg = f"Error code {uuid.uuid4().hex}"

        mock_evaluator_instance = mock_patch_evaluator_cls.return_value
        mock_evaluator_instance.evaluate.side_effect = Exception(error_msg)

        runner = PatchPipelineRunner(repo_path=self.repo_path)

        with self.assertRaises(PatchPipelineError) as ctx:
            runner.run_pipeline(patch_content=patch_content, target_file=target_file)

        self.assertIn(error_msg, str(ctx.exception))

    @patch('skills.patch_pipeline_runner.PatchEvaluator')
    @patch('skills.patch_pipeline_runner.GitInspector')
    def test_pipeline_result_key_error(self, mock_git_inspector_cls, mock_patch_evaluator_cls):
        patch_content = f"pass # {uuid.uuid4().hex}"
        target_file = f"{uuid.uuid4().hex}.py"
        non_existent_key = f"missing_{uuid.uuid4().hex}"

        mock_evaluator_instance = mock_patch_evaluator_cls.return_value
        mock_evaluation_result = MagicMock(spec=PatchEvaluationResult)
        mock_evaluation_result.is_safe = True
        mock_evaluation_result.is_valid = True
        mock_evaluator_instance.evaluate.return_value = mock_evaluation_result

        mock_inspector_instance = mock_git_inspector_cls.return_value
        mock_inspector_instance.get_commit_history.return_value = []

        runner = PatchPipelineRunner(repo_path=self.repo_path)
        result = runner.run_pipeline(patch_content=patch_content, target_file=target_file)

        self.assertIsNone(result.get(non_existent_key))
        with self.assertRaises(KeyError):
            _ = result[non_existent_key]


if __name__ == '__main__':
    unittest.main()