import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.patch_autofix_pipeline import (
    PatchAutofixPipeline,
    PatchAutofixPipelineError,
    patch_autofix_pipeline
)
from skills.patch_autocorrector import PatchAutocorrectorError, PatchSyntaxError
from skills.patch_evaluator import PatchEvaluationResult


class TestPatchAutofixPipelineInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.pipeline = PatchAutofixPipeline(self.repo_path)

    @patch("skills.patch_autofix_pipeline.PatchEvaluator")
    @patch("skills.patch_autofix_pipeline.PatchAutocorrector")
    def test_run_valid_patch_no_correction(self, mock_autocorrector_cls, mock_evaluator_cls):
        mock_evaluator = mock_evaluator_cls.return_value
        mock_autocorrector = mock_autocorrector_cls.return_value

        expected_valid = True
        expected_safe = True
        metrics_key = uuid.uuid4().hex
        metrics_val = random.randint(1, 100)
        
        mock_eval_result = PatchEvaluationResult(
            is_safe=expected_safe,
            is_valid=expected_valid,
            metrics={metrics_key: metrics_val},
            reasons=[],
            telemetry={},
            was_corrected=False
        )
        mock_evaluator.evaluate.return_value = mock_eval_result

        patch_content = f"print('{uuid.uuid4().hex}')"
        target_file = f"{uuid.uuid4().hex}.py"

        pipeline = PatchAutofixPipeline(self.repo_path)
        result = pipeline.run(patch_content, target_file=target_file)

        self.assertTrue(result.is_valid)
        self.assertTrue(result.is_safe)
        self.assertEqual(result.metrics[metrics_key], metrics_val)
        mock_evaluator.evaluate.assert_called_once_with(
            patch_content=patch_content,
            collect_telemetry=True,
            target_file=target_file
        )
        mock_autocorrector.correct_syntax.assert_not_called()

    @patch("skills.patch_autofix_pipeline.PatchEvaluator")
    @patch("skills.patch_autofix_pipeline.PatchAutocorrector")
    def test_run_invalid_patch_successful_autocorrect(self, mock_autocorrector_cls, mock_evaluator_cls):
        mock_evaluator = mock_evaluator_cls.return_value
        mock_autocorrector = mock_autocorrector_cls.return_value

        invalid_eval_result = PatchEvaluationResult(
            is_safe=False,
            is_valid=False,
            metrics={},
            reasons=[uuid.uuid4().hex],
            telemetry={},
            was_corrected=False
        )
        
        corrected_content = f"def {uuid.uuid4().hex}(): pass"
        valid_eval_result = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={uuid.uuid4().hex: random.randint(10, 50)},
            reasons=[],
            telemetry={},
            was_corrected=True
        )

        mock_evaluator.evaluate.side_effect = [invalid_eval_result, valid_eval_result]
        mock_autocorrector.correct_syntax.return_value = corrected_content

        patch_content = f"class {random.randint(1000, 9999)}: invalid"
        target_file = f"{uuid.uuid4().hex}.py"

        pipeline = PatchAutofixPipeline(self.repo_path)
        result = pipeline.run(patch_content, target_file=target_file)

        self.assertTrue(result.is_valid)
        self.assertTrue(result.is_safe)
        self.assertTrue(result.was_corrected)
        mock_autocorrector.correct_syntax.assert_called_once_with(patch_content)
        self.assertEqual(mock_evaluator.evaluate.call_count, 2)

    @patch("skills.patch_autofix_pipeline.PatchEvaluator")
    @patch("skills.patch_autofix_pipeline.PatchAutocorrector")
    def test_run_autocorrect_syntax_error_raises_pipeline_error(self, mock_autocorrector_cls, mock_evaluator_cls):
        mock_evaluator = mock_evaluator_cls.return_value
        mock_autocorrector = mock_autocorrector_cls.return_value

        invalid_eval_result = PatchEvaluationResult(
            is_safe=True,
            is_valid=False,
            metrics={},
            reasons=[uuid.uuid4().hex],
            telemetry={},
            was_corrected=False
        )
        mock_evaluator.evaluate.return_value = invalid_eval_result

        error_msg = uuid.uuid4().hex
        mock_autocorrector.correct_syntax.side_effect = PatchSyntaxError(error_msg)

        patch_content = f"corrupted_{uuid.uuid4().hex}"

        pipeline = PatchAutofixPipeline(self.repo_path)
        with self.assertRaises(PatchAutofixPipelineError) as ctx:
            pipeline.run(patch_content)

        self.assertIn(error_msg, str(ctx.exception))
        mock_autocorrector.correct_syntax.assert_called_once_with(patch_content)

    @patch("skills.patch_autofix_pipeline.PatchEvaluator")
    @patch("skills.patch_autofix_pipeline.PatchAutocorrector")
    def test_run_autocorrect_generic_error_raises_pipeline_error(self, mock_autocorrector_cls, mock_evaluator_cls):
        mock_evaluator = mock_evaluator_cls.return_value
        mock_autocorrector = mock_autocorrector_cls.return_value

        invalid_eval_result = PatchEvaluationResult(
            is_safe=False,
            is_valid=True,
            metrics={},
            reasons=[uuid.uuid4().hex],
            telemetry={},
            was_corrected=False
        )
        mock_evaluator.evaluate.return_value = invalid_eval_result

        error_msg = uuid.uuid4().hex
        mock_autocorrector.correct_syntax.side_effect = PatchAutocorrectorError(error_msg)

        patch_content = f"malformed_{uuid.uuid4().hex}"

        pipeline = PatchAutofixPipeline(self.repo_path)
        with self.assertRaises(PatchAutofixPipelineError) as ctx:
            pipeline.run(patch_content)

        self.assertIn(error_msg, str(ctx.exception))

    @patch("skills.patch_autofix_pipeline.PatchEvaluator")
    @patch("skills.patch_autofix_pipeline.PatchAutocorrector")
    def test_run_stream_processes_correctly(self, mock_autocorrector_cls, mock_evaluator_cls):
        mock_evaluator = mock_evaluator_cls.return_value
        mock_autocorrector = mock_autocorrector_cls.return_value

        stream_data = io.BytesIO(uuid.uuid4().bytes)
        transformed_stream_mock = io.BytesIO(uuid.uuid4().bytes)
        mock_autocorrector.transform_stream.return_value = transformed_stream_mock

        expected_result = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={uuid.uuid4().hex: uuid.uuid4().hex},
            reasons=[],
            telemetry={},
            was_corrected=False
        )
        mock_evaluator.evaluate_stream.return_value = expected_result

        pipeline = PatchAutofixPipeline(self.repo_path)
        result = pipeline.run_stream(stream_data)

        self.assertEqual(result, expected_result)
        mock_autocorrector.transform_stream.assert_called_once_with(stream_data)
        mock_evaluator.evaluate_stream.assert_called_once_with(transformed_stream_mock)

    @patch("skills.patch_autofix_pipeline.PatchAutocorrector")
    def test_run_batch_processes_correctly(self, mock_autocorrector_cls):
        mock_autocorrector = mock_autocorrector_cls.return_value
        batch_dict = {uuid.uuid4().hex: uuid.uuid4().hex, uuid.uuid4().hex: uuid.uuid4().hex}
        expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_autocorrector.batch_correct.return_value = expected_output

        pipeline = PatchAutofixPipeline(self.repo_path)
        result = pipeline.run_batch(batch_dict)

        self.assertEqual(result, expected_output)
        mock_autocorrector.batch_correct.assert_called_once_with(batch_dict)

    @patch("skills.patch_autofix_pipeline.PatchAutofixPipeline")
    def test_functional_interface_wrapper(self, mock_pipeline_cls):
        mock_instance = mock_pipeline_cls.return_value
        expected_result = PatchEvaluationResult(
            is_safe=True,
            is_valid=True,
            metrics={},
            reasons=[],
            telemetry={},
            was_corrected=False
        )
        mock_instance.run.return_value = expected_result

        repo_path = f"/path/{uuid.uuid4().hex}"
        patch_content = f"code = '{uuid.uuid4().hex}'"
        target_file = f"{uuid.uuid4().hex}.py"

        result = patch_autofix_pipeline(repo_path, patch_content, target_file=target_file)

        mock_pipeline_cls.assert_called_once_with(repo_path)
        mock_instance.run.assert_called_once_with(patch_content, target_file)
        self.assertEqual(result, expected_result)