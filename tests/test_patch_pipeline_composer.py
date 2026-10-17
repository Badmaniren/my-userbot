import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.patch_pipeline_composer import (
    PatchPipelineComposer,
    PatchPipelineError,
    PipelineResult
)
from skills.patch_analyzer import PatchAnalyzerError
from skills.patch_evaluator import PatchEvaluationResult, PatchEvaluatorError
from skills.patch_checker import PatchCheckerError

class TestPatchPipelineComposer(unittest.TestCase):

    def setUp(self):
        self.repo_dir = f"/tmp/{uuid.uuid4().hex}"
        self.composer = PatchPipelineComposer(repo_path=self.repo_dir)

    def test_composer_initialization(self):
        self.assertEqual(self.composer.repo_path, self.repo_dir)
        self.assertIsNotNone(self.composer.analyzer)
        self.assertIsNotNone(self.composer.evaluator)

    @patch('skills.patch_pipeline_composer.PatchAnalyzer')
    @patch('skills.patch_pipeline_composer.PatchEvaluator')
    def test_process_pipeline_success(self, mock_evaluator_cls, mock_analyzer_cls):
        diff_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n+{uuid.uuid4().hex}"
        target_file = f"src/{uuid.uuid4().hex}.py"

        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {
            "status": "clean",
            "risk_score": random.randint(0, 10)
        }

        mock_evaluator = mock_evaluator_cls.return_value
        mock_eval_result = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={"score": random.uniform(80.0, 100.0)},
            reasons=[],
            telemetry={"cpu": random.randint(1, 10)},
            was_corrected=False
        )
        mock_evaluator.evaluate.return_value = mock_eval_result

        result = self.composer.process(diff_content, target_file=target_file)

        self.assertIsInstance(result, PipelineResult)
        self.assertTrue(result.success)
        self.assertEqual(result.analysis["status"], "clean")
        self.assertEqual(result.evaluation.is_safe, True)
        mock_analyzer.analyze.assert_called_once_with(diff_content)
        mock_evaluator.evaluate.assert_called_once()

    @patch('skills.patch_pipeline_composer.PatchAnalyzer')
    def test_process_pipeline_analyzer_failure(self, mock_analyzer_cls):
        diff_content = f"malformed_diff_{uuid.uuid4().hex}"
        error_msg = f"Analysis failed: {uuid.uuid4().hex}"

        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.side_effect = PatchAnalyzerError(error_msg)

        with self.assertRaises(PatchPipelineError) as ctx:
            self.composer.process(diff_content)

        self.assertIn(error_msg, str(ctx.exception))

    @patch('skills.patch_pipeline_composer.PatchAnalyzer')
    @patch('skills.patch_pipeline_composer.PatchEvaluator')
    def test_process_pipeline_evaluator_failure(self, mock_evaluator_cls, mock_analyzer_cls):
        diff_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"
        error_msg = f"Evaluation failed: {uuid.uuid4().hex}"

        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"status": "ok"}

        mock_evaluator = mock_evaluator_cls.return_value
        mock_evaluator.evaluate.side_effect = PatchEvaluatorError(error_msg)

        with self.assertRaises(PatchPipelineError) as ctx:
            self.composer.process(diff_content)

        self.assertIn(error_msg, str(ctx.exception))

    @patch('skills.patch_pipeline_composer.PatchAnalyzer')
    @patch('skills.patch_pipeline_composer.PatchEvaluator')
    def test_process_stream(self, mock_evaluator_cls, mock_analyzer_cls):
        stream_data = f"stream_diff_{uuid.uuid4().hex}\n+{uuid.uuid4().hex}".encode('utf-8')
        stream_obj = io.BytesIO(stream_data)

        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze_stream.return_value = {"stream_analyzed": True}

        mock_evaluator = mock_evaluator_cls.return_value
        mock_eval_result = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={},
            reasons=[],
            telemetry={},
            was_corrected=False
        )
        mock_evaluator.evaluate_stream.return_value = mock_eval_result

        result = self.composer.process_stream(stream_obj)

        self.assertIsInstance(result, PipelineResult)
        self.assertTrue(result.success)
        self.assertEqual(result.analysis, {"stream_analyzed": True})
        mock_analyzer.analyze_stream.assert_called_once()
        mock_evaluator.evaluate_stream.assert_called_once()

    @patch('skills.patch_pipeline_composer.PatchAnalyzer')
    @patch('skills.patch_pipeline_composer.PatchEvaluator')
    def test_process_with_autocorrect_flow(self, mock_evaluator_cls, mock_analyzer_cls):
        diff_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n-{uuid.uuid4().hex}"

        mock_analyzer = mock_analyzer_cls.return_value
        mock_analyzer.analyze.return_value = {"status": "risky"}

        mock_evaluator = mock_evaluator_cls.return_value
        mock_eval_result = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={"auto_fixed": True},
            reasons=[uuid.uuid4().hex],
            telemetry={},
            was_corrected=True
        )
        mock_evaluator.evaluate_with_autocorrect.return_value = mock_eval_result

        result = self.composer.process_with_autocorrect(diff_content)

        self.assertTrue(result.success)
        self.assertTrue(result.evaluation.was_corrected)
        mock_evaluator.evaluate_with_autocorrect.assert_called_once_with(diff_content)

if __name__ == '__main__':
    unittest.main()