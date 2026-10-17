import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.patch_pipeline_integration import (
    PatchPipelineIntegration,
    PatchPipelineError
)
from skills.patch_analyzer import PatchAnalyzerError
from skills.patch_evaluator import PatchEvaluationResult, PatchEvaluatorError


class TestPatchPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/repo/{uuid.uuid4().hex}"
        self.pipeline = PatchPipelineIntegration(repo_path=self.random_repo_path)

    def test_pipeline_initialization(self):
        self.assertEqual(self.pipeline.repo_path, self.random_repo_path)
        self.assertIsNotNone(self.pipeline.analyzer)
        self.assertIsNotNone(self.pipeline.evaluator)

    def test_pipeline_run_success(self):
        patch_text = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py\n+print('{uuid.uuid4().hex}')"
        target_file_name = f"{uuid.uuid4().hex}.py"

        mock_eval_result = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={"score": random.randint(80, 100)},
            reasons=[],
            telemetry={"cpu": random.random()},
            was_corrected=False
        )

        with patch.object(self.pipeline.analyzer, 'analyze') as mock_analyze, \
             patch.object(self.pipeline.evaluator, 'evaluate', return_value=mock_eval_result) as mock_evaluate:
            
            result = self.pipeline.run(patch_content=patch_text, target_file=target_file_name)
            
            mock_analyze.assert_called_once_with(patch_text)
            mock_evaluate.assert_called_once_with(
                patch_content=patch_text,
                collect_telemetry=True,
                target_file=target_file_name
            )
            self.assertEqual(result, mock_eval_result)

    def test_pipeline_run_analyzer_error(self):
        patch_text = f"invalid_patch_{uuid.uuid4().hex}"
        error_msg = f"Analyzer failed with {uuid.uuid4().hex}"

        with patch.object(self.pipeline.analyzer, 'analyze', side_effect=PatchAnalyzerError(error_msg)):
            with self.assertRaises(PatchPipelineError) as ctx:
                self.pipeline.run(patch_content=patch_text)
            self.assertIn(error_msg, str(ctx.exception))

    def test_pipeline_run_evaluator_error(self):
        patch_text = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py"
        error_msg = f"Evaluator failed with {uuid.uuid4().hex}"

        with patch.object(self.pipeline.analyzer, 'analyze'), \
             patch.object(self.pipeline.evaluator, 'evaluate', side_effect=PatchEvaluatorError(error_msg)):
            
            with self.assertRaises(PatchPipelineError) as ctx:
                self.pipeline.run(patch_content=patch_text)
            self.assertIn(error_msg, str(ctx.exception))

    def test_pipeline_run_stream(self):
        stream_content = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        stream_obj = io.BytesIO(stream_content)

        mock_eval_result = PatchEvaluationResult(
            is_safe=random.choice([True, False]),
            is_valid=True,
            metrics={},
            reasons=[uuid.uuid4().hex],
            telemetry={},
            was_corrected=True
        )

        with patch.object(self.pipeline.analyzer, 'analyze_stream') as mock_analyze_stream, \
             patch.object(self.pipeline.evaluator, 'evaluate_stream', return_value=mock_eval_result) as mock_evaluate_stream:
            
            result = self.pipeline.run_stream(stream_obj)

            mock_analyze_stream.assert_called_once_with(stream_obj)
            mock_evaluate_stream.assert_called_once_with(stream_obj)
            self.assertEqual(result, mock_eval_result)

    def test_pipeline_run_stream_analyzer_error(self):
        stream_obj = io.BytesIO(b"bad stream")
        error_msg = f"Stream analyze error {uuid.uuid4().hex}"

        with patch.object(self.pipeline.analyzer, 'analyze_stream', side_effect=PatchAnalyzerError(error_msg)):
            with self.assertRaises(PatchPipelineError) as ctx:
                self.pipeline.run_stream(stream_obj)
            self.assertIn(error_msg, str(ctx.exception))

    def test_pipeline_run_stream_evaluator_error(self):
        stream_obj = io.BytesIO(b"good analyze, bad eval")
        error_msg = f"Stream eval error {uuid.uuid4().hex}"

        with patch.object(self.pipeline.analyzer, 'analyze_stream'), \
             patch.object(self.pipeline.evaluator, 'evaluate_stream', side_effect=PatchEvaluatorError(error_msg)):
            
            with self.assertRaises(PatchPipelineError) as ctx:
                self.pipeline.run_stream(stream_obj)
            self.assertIn(error_msg, str(ctx.exception))

    def test_execute_pipeline_integration(self):
        patch_text = f"diff --integration-{uuid.uuid4().hex}"
        target_file = f"src/{uuid.uuid4().hex}.py"

        mock_eval_result = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={"integrated": True},
            reasons=[],
            telemetry={},
            was_corrected=False
        )

        with patch.object(self.pipeline, 'run', return_value=mock_eval_result) as mock_run:
            result = self.pipeline.execute_pipeline(patch_content=patch_text, target_file=target_file)
            mock_run.assert_called_once_with(patch_text, target_file=target_file)
            self.assertEqual(result, mock_eval_result)


if __name__ == '__main__':
    unittest.main()