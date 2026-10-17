import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.patch_autofix_pipeline import (
    PatchAutofixPipeline,
    PatchAutofixPipelineError
)
from skills.patch_evaluator import PatchEvaluationResult
from skills.patch_autocorrector import PatchAutocorrectorError, PatchSyntaxError


class TestPatchAutofixPipeline(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.target_file = f"src/{uuid.uuid4().hex}.py"
        self.patch_content = f"print('{uuid.uuid4().hex}')\n"
        self.corrected_code = f"print('{uuid.uuid4().hex}')  # corrected\n"

    def test_pipeline_initialization_success(self):
        with patch("skills.patch_autofix_pipeline.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_autofix_pipeline.PatchAutocorrector") as mock_autocorrector_cls:
            
            pipeline = PatchAutofixPipeline(self.repo_path)
            
            mock_evaluator_cls.assert_called_once_with(self.repo_path)
            mock_autocorrector_cls.assert_called_once()
            self.assertIsNotNone(pipeline)

    def test_run_pipeline_success_without_correction(self):
        eval_result_mock = MagicMock(spec=PatchEvaluationResult)
        eval_result_mock.is_safe = True
        eval_result_mock.is_valid = True
        eval_result_mock.was_corrected = False

        with patch("skills.patch_autofix_pipeline.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_autofix_pipeline.PatchAutocorrector"):
            
            mock_evaluator_instance = mock_evaluator_cls.return_value
            mock_evaluator_instance.evaluate.return_value = eval_result_mock

            pipeline = PatchAutofixPipeline(self.repo_path)
            result = pipeline.run(self.patch_content, self.target_file)

            mock_evaluator_instance.evaluate.assert_called_once_with(
                patch_content=self.patch_content,
                collect_telemetry=True,
                target_file=self.target_file
            )
            self.assertEqual(result, eval_result_mock)
            self.assertTrue(result.is_valid)

    def test_run_pipeline_triggers_autocorrection(self):
        initial_eval_mock = MagicMock(spec=PatchEvaluationResult)
        initial_eval_mock.is_safe = False
        initial_eval_mock.is_valid = False
        initial_eval_mock.reasons = [uuid.uuid4().hex]

        corrected_eval_mock = MagicMock(spec=PatchEvaluationResult)
        corrected_eval_mock.is_safe = True
        corrected_eval_mock.is_valid = True
        corrected_eval_mock.was_corrected = True

        with patch("skills.patch_autofix_pipeline.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_autofix_pipeline.PatchAutocorrector") as mock_autocorrector_cls:
            
            mock_evaluator_instance = mock_evaluator_cls.return_value
            mock_evaluator_instance.evaluate.side_effect = [initial_eval_mock, corrected_eval_mock]

            mock_autocorrector_instance = mock_autocorrector_cls.return_value
            mock_autocorrector_instance.correct_syntax.return_value = self.corrected_code

            pipeline = PatchAutofixPipeline(self.repo_path)
            result = pipeline.run(self.patch_content, self.target_file)

            mock_autocorrector_instance.correct_syntax.assert_called_once_with(self.patch_content)
            self.assertEqual(mock_evaluator_instance.evaluate.call_count, 2)
            self.assertEqual(result, corrected_eval_mock)
            self.assertTrue(result.was_corrected)

    def test_run_pipeline_handles_autocorrector_exception(self):
        initial_eval_mock = MagicMock(spec=PatchEvaluationResult)
        initial_eval_mock.is_safe = False
        initial_eval_mock.is_valid = False

        error_message = uuid.uuid4().hex

        with patch("skills.patch_autofix_pipeline.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_autofix_pipeline.PatchAutocorrector") as mock_autocorrector_cls:
            
            mock_evaluator_instance = mock_evaluator_cls.return_value
            mock_evaluator_instance.evaluate.return_value = initial_eval_mock

            mock_autocorrector_instance = mock_autocorrector_cls.return_value
            mock_autocorrector_instance.correct_syntax.side_effect = PatchSyntaxError(error_message)

            pipeline = PatchAutofixPipeline(self.repo_path)
            
            with self.assertRaises(PatchAutofixPipelineError) as ctx:
                pipeline.run(self.patch_content, self.target_file)
            
            self.assertIn(error_message, str(ctx.exception))

    def test_stream_pipeline_processing(self):
        stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        stream_result = MagicMock(spec=PatchEvaluationResult)
        stream_result.is_safe = True
        stream_result.is_valid = True

        with patch("skills.patch_autofix_pipeline.PatchEvaluator") as mock_evaluator_cls, \
             patch("skills.patch_autofix_pipeline.PatchAutocorrector") as mock_autocorrector_cls:
            
            mock_evaluator_instance = mock_evaluator_cls.return_value
            mock_evaluator_instance.evaluate_stream.return_value = stream_result

            mock_autocorrector_instance = mock_autocorrector_cls.return_value
            mock_autocorrector_instance.transform_stream.return_value = uuid.uuid4().hex

            pipeline = PatchAutofixPipeline(self.repo_path)
            result = pipeline.run_stream(stream_data)

            mock_autocorrector_instance.transform_stream.assert_called_once()
            mock_evaluator_instance.evaluate_stream.assert_called_once()
            self.assertEqual(result, stream_result)

    def test_batch_pipeline_execution(self):
        batch_dict = {
            f"file_{uuid.uuid4().hex}.py": f"content_{uuid.uuid4().hex}",
            f"file_{uuid.uuid4().hex}.py": f"content_{uuid.uuid4().hex}"
        }
        batch_response = {
            k: random.choice([True, False]) for k in batch_dict.keys()
        }

        with patch("skills.patch_autofix_pipeline.PatchEvaluator"), \
             patch("skills.patch_autofix_pipeline.PatchAutocorrector") as mock_autocorrector_cls:
            
            mock_autocorrector_instance = mock_autocorrector_cls.return_value
            mock_autocorrector_instance.batch_correct.return_value = batch_response

            pipeline = PatchAutofixPipeline(self.repo_path)
            result = pipeline.run_batch(batch_dict)

            mock_autocorrector_instance.batch_correct.assert_called_once_with(batch_dict)
            self.assertEqual(result, batch_response)


if __name__ == '__main__':
    unittest.main()