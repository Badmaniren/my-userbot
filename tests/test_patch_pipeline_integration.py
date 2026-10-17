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
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.pipeline = PatchPipelineIntegration(repo_path=self.repo_path)

    def test_pipeline_composition_initialization(self):
        self.assertIsNotNone(self.pipeline)
        self.assertEqual(self.pipeline.repo_path, self.repo_path)

    def test_pipeline_run_success(self):
        rand_patch_content = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py\n+print('{uuid.uuid4().hex}')"
        rand_target_file = f"src/{uuid.uuid4().hex}.py"
        
        mock_analysis_result = {
            "status": "clean",
            "stats": {str(uuid.uuid4().hex): random.randint(1, 100)}
        }
        
        mock_eval_result = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={str(uuid.uuid4().hex): random.random()},
            reasons=[str(uuid.uuid4().hex)],
            telemetry={str(uuid.uuid4().hex): str(uuid.uuid4().hex)},
            was_corrected=False
        )

        with patch('skills.patch_pipeline_integration.PatchAnalyzer') as mock_analyzer_cls, \
             patch('skills.patch_pipeline_integration.PatchEvaluator') as mock_evaluator_cls:
            
            mock_analyzer_instance = mock_analyzer_cls.return_value
            mock_analyzer_instance.analyze.return_value = mock_analysis_result
            
            mock_evaluator_instance = mock_evaluator_cls.return_value
            mock_evaluator_instance.evaluate.return_value = mock_eval_result

            result = self.pipeline.run(rand_patch_content, target_file=rand_target_file)

            self.assertTrue(result.is_safe)
            self.assertTrue(result.is_valid)
            mock_analyzer_instance.analyze.assert_called_once_with(rand_patch_content)
            mock_evaluator_instance.evaluate.assert_called_once_with(
                patch_content=rand_patch_content,
                collect_telemetry=True,
                target_file=rand_target_file
            )

    def test_pipeline_run_analyzer_error(self):
        rand_patch_content = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py"
        rand_error_msg = f"Analyzer crashed {uuid.uuid4().hex}"

        with patch('skills.patch_pipeline_integration.PatchAnalyzer') as mock_analyzer_cls, \
             patch('skills.patch_pipeline_integration.PatchEvaluator') as mock_evaluator_cls:
            
            mock_analyzer_instance = mock_analyzer_cls.return_value
            mock_analyzer_instance.analyze.side_effect = PatchAnalyzerError(rand_error_msg)

            with self.assertRaises(PatchPipelineError) as ctx:
                self.pipeline.run(rand_patch_content)
            
            self.assertIn(rand_error_msg, str(ctx.exception))

    def test_pipeline_run_evaluator_error(self):
        rand_patch_content = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py"
        rand_error_msg = f"Evaluator failed {uuid.uuid4().hex}"

        mock_analysis_result = {"status": "ok"}

        with patch('skills.patch_pipeline_integration.PatchAnalyzer') as mock_analyzer_cls, \
             patch('skills.patch_pipeline_integration.PatchEvaluator') as mock_evaluator_cls:
            
            mock_analyzer_instance = mock_analyzer_cls.return_value
            mock_analyzer_instance.analyze.return_value = mock_analysis_result
            
            mock_evaluator_instance = mock_evaluator_cls.return_value
            mock_evaluator_instance.evaluate.side_effect = PatchEvaluatorError(rand_error_msg)

            with self.assertRaises(PatchPipelineError) as ctx:
                self.pipeline.run(rand_patch_content)
            
            self.assertIn(rand_error_msg, str(ctx.exception))

    def test_pipeline_run_stream(self):
        rand_stream_data = f"stream_diff_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(rand_stream_data)

        mock_eval_result = PatchEvaluationResult(
            is_safe=random.choice([True, False]),
            is_valid=True,
            metrics={},
            reasons=[],
            telemetry={},
            was_corrected=False
        )

        with patch('skills.patch_pipeline_integration.PatchAnalyzer') as mock_analyzer_cls, \
             patch('skills.patch_pipeline_integration.PatchEvaluator') as mock_evaluator_cls:
            
            mock_analyzer_instance = mock_analyzer_cls.return_value
            mock_analyzer_instance.analyze_stream.return_value = {"stream_analyzed": True}
            
            mock_evaluator_instance = mock_evaluator_cls.return_value
            mock_evaluator_instance.evaluate_stream.return_value = mock_eval_result

            result = self.pipeline.run_stream(mock_stream)

            self.assertEqual(result, mock_eval_result)
            mock_analyzer_instance.analyze_stream.assert_called_once_with(mock_stream)
            mock_evaluator_instance.evaluate_stream.assert_called_once_with(mock_stream)

if __name__ == '__main__':
    unittest.main()