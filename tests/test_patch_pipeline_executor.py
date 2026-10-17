import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.patch_pipeline_executor import PatchPipelineExecutor, PatchPipelineError
from skills.patch_evaluator import PatchEvaluationResult


class TestPatchPipelineExecutor(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.patch_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n+print('{uuid.uuid4().hex}')"
        self.target_file = f"src/{uuid.uuid4().hex}.py"

        self.mock_is_safe = random.choice([True, False])
        self.mock_is_valid = random.choice([True, False])
        self.mock_metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        self.mock_reasons = [uuid.uuid4().hex, uuid.uuid4().hex]
        self.mock_telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_was_corrected = random.choice([True, False])

    def test_pipeline_execution_success(self):
        with patch('skills.patch_pipeline_executor.GitInspector') as mock_git_insp, \
             patch('skills.patch_pipeline_executor.PatchEvaluator') as mock_patch_eval, \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', unittest.mock.mock_open()) as mock_open_file:

            git_instance = mock_git_insp.return_value
            git_instance.analyze_repository.return_value = {uuid.uuid4().hex: uuid.uuid4().hex}

            eval_instance = mock_patch_eval.return_value
            expected_result = PatchEvaluationResult(
                is_safe=self.mock_is_safe,
                is_valid=self.mock_is_valid,
                metrics=self.mock_metrics,
                reasons=self.mock_reasons,
                telemetry=self.mock_telemetry,
                was_corrected=self.mock_was_corrected
            )
            eval_instance.evaluate.return_value = expected_result

            executor = PatchPipelineExecutor(repo_path=self.repo_path)
            result = executor.execute(patch_content=self.patch_content, target_file=self.target_file)

            mock_git_insp.assert_called_once_with(self.repo_path)
            git_instance.analyze_repository.assert_called_once()

            mock_patch_eval.assert_called_once_with(repo_path=self.repo_path)
            eval_instance.evaluate.assert_called_once_with(
                patch_content=self.patch_content,
                target_file=self.target_file,
                collect_telemetry=True
            )

            self.assertEqual(result.is_safe, self.mock_is_safe)
            self.assertEqual(result.is_valid, self.mock_is_valid)
            self.assertEqual(result.metrics, self.mock_metrics)
            self.assertEqual(result.reasons, self.mock_reasons)
            self.assertEqual(result.telemetry, self.mock_telemetry)
            self.assertEqual(result.was_corrected, self.mock_was_corrected)

    def test_pipeline_execution_with_autocorrect(self):
        with patch('skills.patch_pipeline_executor.GitInspector') as mock_git_insp, \
             patch('skills.patch_pipeline_executor.PatchEvaluator') as mock_patch_eval:

            git_instance = mock_git_insp.return_value
            eval_instance = mock_patch_eval.return_value

            expected_result = PatchEvaluationResult(
                is_safe=True,
                is_valid=True,
                metrics=self.mock_metrics,
                reasons=[],
                telemetry={},
                was_corrected=True
            )
            eval_instance.evaluate_with_autocorrect.return_value = expected_result

            executor = PatchPipelineExecutor(repo_path=self.repo_path)
            result = executor.execute_with_autocorrect(patch_content=self.patch_content)

            git_instance.analyze_repository.assert_called_once()
            eval_instance.evaluate_with_autocorrect.assert_called_once_with(self.patch_content)

            self.assertTrue(result.was_corrected)
            self.assertTrue(result.is_safe)

    def test_pipeline_git_inspector_failure_raises_error(self):
        with patch('skills.patch_pipeline_executor.GitInspector') as mock_git_insp, \
             patch('skills.patch_pipeline_executor.PatchEvaluator') as mock_patch_eval:

            git_instance = mock_git_insp.return_value
            random_error_msg = uuid.uuid4().hex
            git_instance.analyze_repository.side_effect = Exception(random_error_msg)

            executor = PatchPipelineExecutor(repo_path=self.repo_path)

            with self.assertRaises(PatchPipelineError) as ctx:
                executor.execute(patch_content=self.patch_content, target_file=self.target_file)

            self.assertIn(random_error_msg, str(ctx.exception))

    def test_pipeline_evaluator_failure_raises_error(self):
        with patch('skills.patch_pipeline_executor.GitInspector') as mock_git_insp, \
             patch('skills.patch_pipeline_executor.PatchEvaluator') as mock_patch_eval:

            git_instance = mock_git_insp.return_value
            git_instance.analyze_repository.return_value = {}

            eval_instance = mock_patch_eval.return_value
            random_error_msg = uuid.uuid4().hex
            eval_instance.evaluate.side_effect = Exception(random_error_msg)

            executor = PatchPipelineExecutor(repo_path=self.repo_path)

            with self.assertRaises(PatchPipelineError) as ctx:
                executor.execute(patch_content=self.patch_content, target_file=self.target_file)

            self.assertIn(random_error_msg, str(ctx.exception))

    def test_pipeline_stream_execution(self):
        with patch('skills.patch_pipeline_executor.GitInspector') as mock_git_insp, \
             patch('skills.patch_pipeline_executor.PatchEvaluator') as mock_patch_eval:

            git_instance = mock_git_insp.return_value
            eval_instance = mock_patch_eval.return_value

            stream_data = io.BytesIO(self.patch_content.encode('utf-8'))

            expected_result = PatchEvaluationResult(
                is_safe=True,
                is_valid=True,
                metrics=self.mock_metrics,
                reasons=[],
                telemetry={},
                was_corrected=False
            )
            eval_instance.evaluate_stream.return_value = expected_result

            executor = PatchPipelineExecutor(repo_path=self.repo_path)
            result = executor.execute_stream(stream=stream_data)

            git_instance.analyze_repository.assert_called_once()
            eval_instance.evaluate_stream.assert_called_once_with(stream_data)
            self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()