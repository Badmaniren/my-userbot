import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.patch_runner import PatchRunner, PatchRunnerError
from skills.patch_autocorrector import PatchAutocorrectorError
from skills.patch_executor import PatchExecutorError

class TestPatchRunner(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.mock_autocorrector = MagicMock()
        self.mock_executor = MagicMock()

        self.runner = PatchRunner(
            repo_path=self.repo_path,
            autocorrector=self.mock_autocorrector,
            executor=self.mock_executor
        )

    def test_run_patch_success_code_key(self):
        rand_code = f"print('{uuid.uuid4().hex}')"
        rand_corrected = f"print('{uuid.uuid4().hex}')"
        rand_file = f"{uuid.uuid4().hex}.py"

        patch_data = {
            "code": rand_code,
            "file_path": rand_file
        }

        self.mock_autocorrector.correct_and_validate.return_value = rand_corrected
        self.mock_executor.apply_patch.return_value = True

        result = self.runner.run_patch(patch_data)

        self.assertTrue(result)
        self.mock_autocorrector.correct_and_validate.assert_called_once_with(rand_code)

        expected_payload = {
            "code": rand_corrected,
            "content": rand_corrected,
            "file_path": rand_file
        }
        self.mock_executor.apply_patch.assert_called_once_with(expected_payload)

    def test_run_patch_success_content_key(self):
        rand_content = f"x = {random.randint(1, 100)}"
        rand_corrected = f"x = {random.randint(101, 200)}"
        rand_file = f"{uuid.uuid4().hex}.py"

        patch_data = {
            "content": rand_content,
            "file_path": rand_file
        }

        self.mock_autocorrector.correct_and_validate.return_value = rand_corrected
        self.mock_executor.apply_patch.return_value = True

        result = self.runner.run_patch(patch_data)

        self.assertTrue(result)
        self.mock_autocorrector.correct_and_validate.assert_called_once_with(rand_content)

        expected_payload = {
            "content": rand_corrected,
            "code": rand_corrected,
            "file_path": rand_file
        }
        self.mock_executor.apply_patch.assert_called_once_with(expected_payload)

    def test_run_patch_autocorrector_error_raises_runner_error(self):
        rand_code = uuid.uuid4().hex
        rand_error_msg = uuid.uuid4().hex
        patch_data = {"code": rand_code}

        self.mock_autocorrector.correct_and_validate.side_effect = PatchAutocorrectorError(rand_error_msg)

        with self.assertRaises(PatchRunnerError) as ctx:
            self.runner.run_patch(patch_data)

        self.assertIn(rand_error_msg, str(ctx.exception))
        self.mock_executor.apply_patch.assert_not_called()

    def test_run_patch_executor_error_raises_runner_error(self):
        rand_code = uuid.uuid4().hex
        rand_corrected = uuid.uuid4().hex
        rand_error_msg = uuid.uuid4().hex
        patch_data = {"code": rand_code}

        self.mock_autocorrector.correct_and_validate.return_value = rand_corrected
        self.mock_executor.apply_patch.side_effect = PatchExecutorError(rand_error_msg)

        with self.assertRaises(PatchRunnerError) as ctx:
            self.runner.run_patch(patch_data)

        self.assertIn(rand_error_msg, str(ctx.exception))

    def test_execute_pipeline_from_lessons(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        expected_result = {rand_key: rand_val}

        self.mock_executor.execute_from_lessons.return_value = expected_result

        res = self.runner.execute_pipeline_from_lessons()

        self.assertEqual(res, expected_result)
        self.mock_executor.execute_from_lessons.assert_called_once()

    def test_rollback_operation(self):
        rand_file = f"{uuid.uuid4().hex}.py"
        rand_commit = uuid.uuid4().hex

        self.mock_executor.rollback_patch.return_value = True

        res = self.runner.rollback_operation(rand_file, rand_commit)

        self.assertTrue(res)
        self.mock_executor.rollback_patch.assert_called_once_with(rand_file, rand_commit)

    def test_process_stream(self):
        rand_stream_data = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(rand_stream_data)
        rand_transformed = uuid.uuid4().hex

        self.mock_autocorrector.transform_stream.return_value = rand_transformed

        res = self.runner.process_stream(stream)

        self.assertEqual(res, rand_transformed)
        self.mock_autocorrector.transform_stream.assert_called_once_with(stream)

    def test_process_stream_error_raises_runner_error(self):
        err_msg = uuid.uuid4().hex
        self.mock_autocorrector.transform_stream.side_effect = PatchAutocorrectorError(err_msg)

        with self.assertRaises(PatchRunnerError) as ctx:
            self.runner.process_stream("some code string")

        self.assertIn(err_msg, str(ctx.exception))

    def test_default_initialization(self):
        with patch('skills.patch_runner.PatchAutocorrector') as mock_ac_cls, \
             patch('skills.patch_runner.PatchExecutor') as mock_ex_cls:

            mock_sanitizer = MagicMock()
            mock_validator = MagicMock()
            mock_inspector = MagicMock()
            mock_parser = MagicMock()

            runner = PatchRunner(
                repo_path=self.repo_path,
                sanitizer=mock_sanitizer,
                validator=mock_validator,
                git_inspector=mock_inspector,
                lesson_parser=mock_parser
            )

            mock_ac_cls.assert_called_once_with(
                repo_path=self.repo_path,
                sanitizer=mock_sanitizer,
                validator=mock_validator
            )
            mock_ex_cls.assert_called_once_with(
                repo_path=self.repo_path,
                git_inspector=mock_inspector,
                lesson_parser=mock_parser
            )
            self.assertEqual(runner.repo_path, self.repo_path)

if __name__ == '__main__':
    unittest.main()