import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.patch_runner import PatchRunner, PatchRunnerError
from skills.code_validator import CodeValidator, CodeValidatorASTError
from skills.patch_autocorrector import PatchAutocorrector, PatchAutocorrectorError
from skills.patch_executor import PatchExecutor, PatchExecutorError


class TestPatchRunnerArchitecture(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.patch_runner = PatchRunner(repo_path=self.repo_path)

    def test_composition_dependencies_initialization(self):
        self.assertIsInstance(self.patch_runner.validator, CodeValidator)
        self.assertIsInstance(self.patch_runner.autocorrector, PatchAutocorrector)
        self.assertIsInstance(self.patch_runner.executor, PatchExecutor)

    @patch('skills.patch_runner.CodeValidator.validate_code')
    @patch('skills.patch_runner.PatchAutocorrector.correct_and_validate')
    @patch('skills.patch_runner.PatchExecutor.apply_patch')
    def test_pipeline_success_path(self, mock_apply, mock_correct, mock_validate):
        random_code = f"print('{uuid.uuid4().hex}')"
        random_file = f"{uuid.uuid4().hex}.py"
        patch_payload = {
            "file_path": random_file,
            "code": random_code
        }

        mock_validate.return_value = True
        mock_apply.return_value = True

        result = self.patch_runner.run_pipeline(patch_payload)

        self.assertTrue(result)
        mock_validate.assert_called_once_with(random_code)
        mock_correct.assert_not_called()
        mock_apply.assert_called_once_with(patch_payload)

    @patch('skills.patch_runner.CodeValidator.validate_code')
    @patch('skills.patch_runner.PatchAutocorrector.correct_and_validate')
    @patch('skills.patch_runner.PatchExecutor.apply_patch')
    def test_pipeline_autocorrection_trigger(self, mock_apply, mock_correct, mock_validate):
        random_malformed_code = f"x = {random.randint(1, 100)}  # {uuid.uuid4().hex}"
        random_corrected_code = f"x = {random.randint(101, 200)}  # {uuid.uuid4().hex}"
        random_file = f"{uuid.uuid4().hex}.py"

        patch_payload = {
            "file_path": random_file,
            "code": random_malformed_code
        }

        mock_validate.return_value = False
        mock_correct.return_value = random_corrected_code
        mock_apply.return_value = True

        result = self.patch_runner.run_pipeline(patch_payload)

        self.assertTrue(result)
        mock_validate.assert_called_once_with(random_malformed_code)
        mock_correct.assert_called_once_with(random_malformed_code)

        expected_corrected_payload = {
            "file_path": random_file,
            "code": random_corrected_code
        }
        mock_apply.assert_called_once_with(expected_corrected_payload)

    @patch('skills.patch_runner.CodeValidator.validate_code')
    @patch('skills.patch_runner.PatchAutocorrector.correct_and_validate')
    @patch('skills.patch_runner.PatchExecutor.apply_patch')
    def test_pipeline_autocorrection_fails_raises_error(self, mock_apply, mock_correct, mock_validate):
        random_bad_code = f"def {uuid.uuid4().hex}(): pass"
        random_file = f"{uuid.uuid4().hex}.py"

        patch_payload = {
            "file_path": random_file,
            "code": random_bad_code
        }

        mock_validate.return_value = False
        mock_correct.side_effect = PatchAutocorrectorError(uuid.uuid4().hex)

        with self.assertRaises(PatchRunnerError):
            self.patch_runner.run_pipeline(patch_payload)

        mock_apply.assert_not_called()

    @patch('skills.patch_runner.CodeValidator.validate_code')
    @patch('skills.patch_runner.PatchExecutor.apply_patch')
    def test_pipeline_execution_failure_raises_error(self, mock_apply, mock_validate):
        random_code = f"result = {random.random()}"
        random_file = f"{uuid.uuid4().hex}.py"
        patch_payload = {
            "file_path": random_file,
            "code": random_code
        }

        mock_validate.return_value = True
        mock_apply.side_effect = PatchExecutorError(uuid.uuid4().hex)

        with self.assertRaises(PatchRunnerError):
            self.patch_runner.run_pipeline(patch_payload)

    def test_stream_processing_pipeline(self):
        random_stream_content = f"import os\n# {uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_stream_content)

        with patch('skills.patch_runner.CodeValidator.validate_stream') as mock_val_stream, \
             patch('skills.patch_runner.PatchAutocorrector.transform_stream') as mock_trans_stream:

            unique_transformed = f"# {uuid.uuid4().hex}"
            mock_val_stream.return_value = False
            mock_trans_stream.return_value = unique_transformed

            result = self.patch_runner.process_stream(mock_stream)

            self.assertEqual(result, unique_transformed)
            mock_val_stream.assert_called_once()
            mock_trans_stream.assert_called_once()