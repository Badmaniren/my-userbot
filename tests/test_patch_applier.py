import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.patch_applier import PatchApplier
from skills.patch_autocorrector import PatchAutocorrector, PatchAutocorrectorError
from skills.patch_executor import PatchExecutor, PatchExecutorError

class TestPatchApplier(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.mock_autocorrector = MagicMock(spec=PatchAutocorrector)
        self.mock_executor = MagicMock(spec=PatchExecutor)

        self.applier = PatchApplier(
            repo_path=self.repo_path,
            autocorrector=self.mock_autocorrector,
            executor=self.mock_executor
        )

    def test_apply_patch_flow_success(self):
        raw_patch = "".join(random.choices(string.ascii_letters, k=50))
        corrected_patch = f"corrected_{uuid.uuid4().hex}"

        self.mock_autocorrector.correct_syntax.return_value = corrected_patch
        self.mock_executor.apply_patch.return_value = True

        result = self.applier.apply(raw_patch)

        self.assertTrue(result)
        self.mock_autocorrector.correct_syntax.assert_called_once_with(raw_patch)
        self.mock_executor.apply_patch.assert_called_once_with(corrected_patch)

    def test_apply_patch_autocorrector_failure(self):
        raw_patch = "".join(random.choices(string.ascii_letters, k=30))
        error_msg = f"error_{uuid.uuid4().hex}"

        self.mock_autocorrector.correct_syntax.side_effect = PatchAutocorrectorError(error_msg)

        with self.assertRaises(PatchAutocorrectorError):
            self.applier.apply(raw_patch)

        self.mock_executor.apply_patch.assert_not_called()

    def test_apply_patch_executor_failure(self):
        raw_patch = "".join(random.choices(string.ascii_letters, k=40))
        corrected_patch = f"fixed_{uuid.uuid4().hex}"

        self.mock_autocorrector.correct_syntax.return_value = corrected_patch
        self.mock_executor.apply_patch.side_effect = PatchExecutorError(f"exec_fail_{uuid.uuid4().hex}")

        with self.assertRaises(PatchExecutorError):
            self.applier.apply(raw_patch)

    def test_batch_process_stream(self):
        random_stream_content = b"".join([bytes([random.randint(0, 255)]) for _ in range(100)])
        stream = io.BytesIO(random_stream_content)

        transformed_data = f"data_{uuid.uuid4().hex}"
        self.mock_autocorrector.transform_stream.return_value = transformed_data
        self.mock_executor.apply_patch.return_value = True

        result = self.applier.process_stream(stream)

        self.assertTrue(result)
        self.mock_autocorrector.transform_stream.assert_called_once()
        self.mock_executor.apply_patch.assert_called_with(transformed_data)

    def test_rollback_delegation(self):
        file_path = f"/src/{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        self.mock_executor.rollback_patch.return_value = True

        result = self.applier.rollback(file_path, commit_hash)

        self.assertTrue(result)
        self.mock_executor.rollback_patch.assert_called_once_with(file_path, commit_hash)

    def test_integration_with_mocked_components(self):
        # Проверка взаимодействия компонентов через композицию
        with patch('skills.patch_applier.PatchAutocorrector') as MockAC, \
             patch('skills.patch_applier.PatchExecutor') as MockExec:

            instance_ac = MockAC.return_value
            instance_exec = MockExec.return_value

            applier = PatchApplier(self.repo_path, instance_ac, instance_exec)

            test_input = f"input_{uuid.uuid4().hex}"
            instance_ac.correct_syntax.return_value = f"output_{uuid.uuid4().hex}"
            instance_exec.apply_patch.return_value = True

            applier.apply(test_input)

            instance_ac.correct_syntax.assert_called_with(test_input)
            self.assertTrue(instance_exec.apply_patch.called)

if __name__ == '__main__':
    unittest.main()