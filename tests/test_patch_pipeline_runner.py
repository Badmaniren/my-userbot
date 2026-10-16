import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.patch_pipeline_runner import (
    PatchPipelineRunner,
    PatchPipelineRunnerError
)
from skills.code_validator import CodeValidatorError
from skills.patch_autocorrector import PatchAutocorrectorError


class TestPatchPipelineRunner(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.runner = PatchPipelineRunner(repo_path=self.repo_path)

    def test_initialization(self):
        rand_path = f"/repo/{uuid.uuid4().hex}"
        runner = PatchPipelineRunner(repo_path=rand_path)
        self.assertEqual(runner.repo_path, rand_path)
        self.assertIsNotNone(runner.validator)
        self.assertIsNotNone(runner.autocorrector)

    @patch('skills.patch_pipeline_runner.CodeValidator')
    @patch('skills.patch_pipeline_runner.PatchAutocorrector')
    def test_process_and_apply_success(self, mock_autocorrector_cls, mock_validator_cls):
        mock_validator = mock_validator_cls.return_value
        mock_autocorrector = mock_autocorrector_cls.return_value

        random_code = f"def {uuid.uuid4().hex[:8]}(): pass"
        corrected_code = f"def {uuid.uuid4().hex[:8]}(): return {random.randint(1, 100)}"
        file_name = f"{uuid.uuid4().hex[:6]}.py"

        mock_autocorrector.correct_and_validate.return_value = corrected_code
        mock_validator.validate_code.return_value = True

        runner = PatchPipelineRunner(repo_path=self.repo_path)
        result = runner.process_and_apply(file_name, random_code)

        self.assertTrue(result)
        mock_autocorrector.correct_and_validate.assert_called_once_with(random_code)
        mock_validator.validate_code.assert_called_once_with(corrected_code)

    @patch('skills.patch_pipeline_runner.CodeValidator')
    @patch('skills.patch_pipeline_runner.PatchAutocorrector')
    def test_process_and_apply_validation_failure(self, mock_autocorrector_cls, mock_validator_cls):
        mock_validator = mock_validator_cls.return_value
        mock_autocorrector = mock_autocorrector_cls.return_value

        random_code = f"x = {random.randint(100, 999)}"
        file_name = f"{uuid.uuid4().hex[:6]}.py"

        mock_autocorrector.correct_and_validate.return_value = random_code
        mock_validator.validate_code.return_value = False

        runner = PatchPipelineRunner(repo_path=self.repo_path)

        with self.assertRaises(PatchPipelineRunnerError):
            runner.process_and_apply(file_name, random_code)

    @patch('skills.patch_pipeline_runner.PatchAutocorrector')
    def test_process_and_apply_autocorrector_error(self, mock_autocorrector_cls):
        mock_autocorrector = mock_autocorrector_cls.return_value
        error_msg = uuid.uuid4().hex
        mock_autocorrector.correct_and_validate.side_effect = PatchAutocorrectorError(error_msg)

        random_code = f"eval('{uuid.uuid4().hex}')"
        file_name = f"{uuid.uuid4().hex[:6]}.py"

        runner = PatchPipelineRunner(repo_path=self.repo_path)

        with self.assertRaises(PatchPipelineRunnerError):
            runner.process_and_apply(file_name, random_code)

    @patch('skills.patch_pipeline_runner.CodeValidator')
    @patch('skills.patch_pipeline_runner.PatchAutocorrector')
    def test_process_stream_success(self, mock_autocorrector_cls, mock_validator_cls):
        mock_validator = mock_validator_cls.return_value
        mock_autocorrector = mock_autocorrector_cls.return_value

        stream_data = ''.join(random.choices(string.ascii_letters, k=50))
        stream_bytes = io.BytesIO(stream_data.encode('utf-8'))

        transformed_stream_data = ''.join(random.choices(string.ascii_letters, k=50))
        mock_autocorrector.transform_stream.return_value = transformed_stream_data
        mock_validator.validate_stream.return_value = True

        runner = PatchPipelineRunner(repo_path=self.repo_path)
        result = runner.process_stream(stream_bytes)

        self.assertTrue(result)
        mock_autocorrector.transform_stream.assert_called_once()
        mock_validator.validate_stream.assert_called_once()

    @patch('skills.patch_pipeline_runner.CodeValidator')
    @patch('skills.patch_pipeline_runner.PatchAutocorrector')
    def test_batch_process_patches(self, mock_autocorrector_cls, mock_validator_cls):
        mock_validator = mock_validator_cls.return_value
        mock_autocorrector = mock_autocorrector_cls.return_value

        key1 = uuid.uuid4().hex
        key2 = uuid.uuid4().hex
        val1 = f"def {uuid.uuid4().hex[:6]}(): pass"
        val2 = f"def {uuid.uuid4().hex[:6]}(): pass"

        patches_dict = {key1: val1, key2: val2}

        batch_result = {key1: True, key2: False}
        mock_autocorrector.batch_correct.return_value = patches_dict
        mock_validator.batch_validate.return_value = batch_result

        runner = PatchPipelineRunner(repo_path=self.repo_path)
        result = runner.batch_process(patches_dict)

        self.assertEqual(result, batch_result)
        mock_autocorrector.batch_correct.assert_called_once_with(patches_dict)
        mock_validator.batch_validate.assert_called_once_with(patches_dict)

if __name__ == '__main__':
    unittest.main()