import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import sys
from types import ModuleType

class TestPatchPipelineArchitect(unittest.TestCase):

    def setUp(self):
        self.repo_path_val = f"/repo/{uuid.uuid4().hex}"
        self.malformed_code = f"print('{uuid.uuid4().hex}')\n"
        self.sanitized_code = f"print('{uuid.uuid4().hex}')\n"
        self.corrected_code = f"print('{uuid.uuid4().hex}')\n"

        self.mock_sanitizer_instance = MagicMock()
        self.mock_sanitizer_instance.sanitize_patch.return_value = self.sanitized_code

        self.mock_validator_instance = MagicMock()
        self.mock_validator_instance.validate_code.return_value = True

        self.mock_autocorrector_instance = MagicMock()
        self.mock_autocorrector_instance.correct_and_validate.return_value = self.corrected_code
        self.mock_autocorrector_instance.process_and_verify.return_value = True

    @patch('skills.patch_pipeline.CodeSanitizer')
    @patch('skills.patch_pipeline.CodeValidator')
    @patch('skills.patch_pipeline.PatchAutocorrector')
    def test_pipeline_composition_imports_and_instantiation(self, mock_autocorrector_cls, mock_validator_cls, mock_sanitizer_cls):
        mock_sanitizer_cls.return_value = self.mock_sanitizer_instance
        mock_validator_cls.return_value = self.mock_validator_instance
        mock_autocorrector_cls.return_value = self.mock_autocorrector_instance

        from skills.patch_pipeline import PatchPipeline

        pipeline = PatchPipeline(repo_path=self.repo_path_val)

        mock_sanitizer_cls.assert_called_once_with(repo_path=self.repo_path_val)
        mock_validator_cls.assert_called_once_with(repo_path=self.repo_path_val)
        mock_autocorrector_cls.assert_called_once_with(
            repo_path=self.repo_path_val,
            sanitizer=self.mock_sanitizer_instance,
            validator=self.mock_validator_instance
        )
        self.assertIsNotNone(pipeline)

    @patch('skills.patch_pipeline.CodeSanitizer')
    @patch('skills.patch_pipeline.CodeValidator')
    @patch('skills.patch_pipeline.PatchAutocorrector')
    def test_process_patch_success_path(self, mock_autocorrector_cls, mock_validator_cls, mock_sanitizer_cls):
        mock_sanitizer_cls.return_value = self.mock_sanitizer_instance
        mock_validator_cls.return_value = self.mock_validator_instance
        mock_autocorrector_cls.return_value = self.mock_autocorrector_instance

        from skills.patch_pipeline import PatchPipeline

        pipeline = PatchPipeline(repo_path=self.repo_path_val)
        result = pipeline.process_patch(self.malformed_code)

        self.mock_sanitizer_instance.sanitize_patch.assert_called_once_with(self.malformed_code)
        self.mock_validator_instance.validate_code.assert_called_once_with(self.sanitized_code)
        self.assertEqual(result, self.sanitized_code)

    @patch('skills.patch_pipeline.CodeSanitizer')
    @patch('skills.patch_pipeline.CodeValidator')
    @patch('skills.patch_pipeline.PatchAutocorrector')
    def test_process_patch_triggers_autocorrect_on_validation_failure(self, mock_autocorrector_cls, mock_validator_cls, mock_sanitizer_cls):
        self.mock_validator_instance.validate_code.return_value = False

        mock_sanitizer_cls.return_value = self.mock_sanitizer_instance
        mock_validator_cls.return_value = self.mock_validator_instance
        mock_autocorrector_cls.return_value = self.mock_autocorrector_instance

        from skills.patch_pipeline import PatchPipeline

        pipeline = PatchPipeline(repo_path=self.repo_path_val)
        result = pipeline.process_patch(self.malformed_code)

        self.mock_sanitizer_instance.sanitize_patch.assert_called_once_with(self.malformed_code)
        self.mock_validator_instance.validate_code.assert_called_once_with(self.sanitized_code)
        self.mock_autocorrector_instance.correct_and_validate.assert_called_once_with(self.sanitized_code)
        self.assertEqual(result, self.corrected_code)

    @patch('skills.patch_pipeline.CodeSanitizer')
    @patch('skills.patch_pipeline.CodeValidator')
    @patch('skills.patch_pipeline.PatchAutocorrector')
    def test_process_stream_pipeline(self, mock_autocorrector_cls, mock_validator_cls, mock_sanitizer_cls):
        stream_content = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(stream_content)

        sanitized_stream_result = f"sanitized_{uuid.uuid4().hex}"
        self.mock_sanitizer_instance.sanitize_stream.return_value = sanitized_stream_result
        self.mock_validator_instance.validate_stream.return_value = True

        mock_sanitizer_cls.return_value = self.mock_sanitizer_instance
        mock_validator_cls.return_value = self.mock_validator_instance
        mock_autocorrector_cls.return_value = self.mock_autocorrector_instance

        from skills.patch_pipeline import PatchPipeline

        pipeline = PatchPipeline(repo_path=self.repo_path_val)
        res = pipeline.process_stream(mock_stream)

        self.mock_sanitizer_instance.sanitize_stream.assert_called_once_with(mock_stream)
        self.mock_validator_instance.validate_stream.assert_called_once_with(sanitized_stream_result)
        self.assertEqual(res, sanitized_stream_result)

    @patch('skills.patch_pipeline.CodeSanitizer')
    @patch('skills.patch_pipeline.CodeValidator')
    @patch('skills.patch_pipeline.PatchAutocorrector')
    def test_batch_process_pipeline(self, mock_autocorrector_cls, mock_validator_cls, mock_sanitizer_cls):
        key_1 = uuid.uuid4().hex
        key_2 = uuid.uuid4().hex
        val_1 = f"code_{uuid.uuid4().hex}"
        val_2 = f"code_{uuid.uuid4().hex}"

        batch_input = {key_1: val_1, key_2: val_2}
        batch_sanitized = {key_1: f"s_{val_1}", key_2: f"s_{val_2}"}

        self.mock_sanitizer_instance.batch_sanitize.return_value = batch_sanitized

        # Make validator fail for key_1, pass for key_2
        def side_effect_validate(code):
            if val_1 in code:
                return False
            return True

        self.mock_validator_instance.validate_code.side_effect = side_effect_validate
        corrected_val_1 = f"corrected_{val_1}"
        self.mock_autocorrector_instance.correct_and_validate.return_value = corrected_val_1

        mock_sanitizer_cls.return_value = self.mock_sanitizer_instance
        mock_validator_cls.return_value = self.mock_validator_instance
        mock_autocorrector_cls.return_value = self.mock_autocorrector_instance

        from skills.patch_pipeline import PatchPipeline

        pipeline = PatchPipeline(repo_path=self.repo_path_val)
        result_batch = pipeline.batch_process(batch_input)

        self.mock_sanitizer_instance.batch_sanitize.assert_called_once_with(batch_input)
        self.assertEqual(result_batch[key_1], corrected_val_1)
        self.assertEqual(result_batch[key_2], batch_sanitized[key_2])