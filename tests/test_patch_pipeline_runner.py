import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import sys

from skills.patch_applier import PatchApplier, PatchApplierError
from skills.patch_verifier import PatchVerifier, PatchVerifierError
import skills.patch_pipeline_runner as pipeline_runner

class TestPatchPipelineRunnerArchitectInquisitor(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        self.patch_source = f"patch_{uuid.uuid4().hex}.diff"
        self.patch_data = {"id": uuid.uuid4().hex, "content": f"content_{uuid.uuid4().hex}"}

    @patch('skills.patch_pipeline_runner.PatchApplier')
    @patch('skills.patch_pipeline_runner.PatchVerifier')
    def test_pipeline_runner_success(self, mock_verifier_cls, mock_applier_cls):
        mock_applier_instance = mock_applier_cls.return_value
        mock_verifier_instance = mock_verifier_cls.return_value

        mock_applier_instance.create_recovery_point.return_value = True
        mock_verifier_instance.verify_and_apply.return_value = True

        if hasattr(pipeline_runner, 'run_patch_pipeline'):
            result = pipeline_runner.run_patch_pipeline(self.repo_path, self.patch_data, self.backup_tag)
            self.assertTrue(result)
            mock_applier_instance.create_recovery_point.assert_called_once_with(self.backup_tag)
            mock_verifier_instance.verify_and_apply.assert_called_once_with(self.patch_data)
        elif hasattr(pipeline_runner, 'PatchPipelineRunner'):
            runner = pipeline_runner.PatchPipelineRunner(self.repo_path)
            result = runner.execute(self.patch_data, self.backup_tag)
            self.assertTrue(result)
        else:
            self.fail("Модуль patch_pipeline_runner не содержит ни run_patch_pipeline, ни PatchPipelineRunner")

    @patch('skills.patch_pipeline_runner.PatchApplier')
    def test_pipeline_runner_recovery_failure(self, mock_applier_cls):
        mock_applier_instance = mock_applier_cls.return_value
        mock_applier_instance.create_recovery_point.return_value = False

        if hasattr(pipeline_runner, 'run_patch_pipeline'):
            result = pipeline_runner.run_patch_pipeline(self.repo_path, self.patch_data, self.backup_tag)
            self.assertFalse(result)
        elif hasattr(pipeline_runner, 'PatchPipelineRunner'):
            runner = pipeline_runner.PatchPipelineRunner(self.repo_path)
            result = runner.execute(self.patch_data, self.backup_tag)
            self.assertFalse(result)
        else:
            self.fail("Отсутствуют необходимые интерфейсы в patch_pipeline_runner")

    @patch('skills.patch_pipeline_runner.PatchApplier')
    @patch('skills.patch_pipeline_runner.PatchVerifier')
    def test_pipeline_runner_rollback_on_error(self, mock_verifier_cls, mock_applier_cls):
        mock_applier_instance = mock_applier_cls.return_value
        mock_verifier_instance = mock_verifier_cls.return_value

        mock_applier_instance.create_recovery_point.return_value = True
        mock_verifier_instance.verify_and_apply.side_effect = PatchVerifierError(uuid.uuid4().hex)
        mock_applier_instance.rollback.return_value = True

        if hasattr(pipeline_runner, 'run_patch_pipeline'):
            try:
                pipeline_runner.run_patch_pipeline(self.repo_path, self.patch_data, self.backup_tag)
            except Exception:
                pass
            mock_applier_instance.rollback.assert_called_once_with(self.backup_tag)
        elif hasattr(pipeline_runner, 'PatchPipelineRunner'):
            runner = pipeline_runner.PatchPipelineRunner(self.repo_path)
            try:
                runner.execute(self.patch_data, self.backup_tag)
            except Exception:
                pass
            mock_applier_instance.rollback.assert_called_once_with(self.backup_tag)

    @patch('skills.patch_pipeline_runner.PatchApplier')
    @patch('skills.patch_pipeline_runner.PatchVerifier')
    def test_pipeline_data_integrity(self, mock_verifier_cls, mock_applier_cls):
        unique_key = uuid.uuid4().hex
        unique_value = uuid.uuid4().hex
        custom_patch = {unique_key: unique_value}

        mock_applier_instance = mock_applier_cls.return_value
        mock_verifier_instance = mock_verifier_cls.return_value

        mock_applier_instance.create_recovery_point.return_value = True

        captured_data = {}
        def side_effect_verify(p_data):
            captured_data.update(p_data)
            return True

        mock_verifier_instance.verify_and_apply.side_effect = side_effect_verify

        if hasattr(pipeline_runner, 'run_patch_pipeline'):
            pipeline_runner.run_patch_pipeline(self.repo_path, custom_patch, self.backup_tag)
            self.assertEqual(captured_data.get(unique_key), unique_value)
        elif hasattr(pipeline_runner, 'PatchPipelineRunner'):
            runner = pipeline_runner.PatchPipelineRunner(self.repo_path)
            runner.execute(custom_patch, self.backup_tag)
            self.assertEqual(captured_data.get(unique_key), unique_value)

    def test_imports_presence(self):
        self.assertTrue(hasattr(pipeline_runner, 'PatchApplier') or 'PatchApplier' in dir(pipeline_runner))
        self.assertTrue(hasattr(pipeline_runner, 'PatchVerifier') or 'PatchVerifier' in dir(pipeline_runner))

if __name__ == '__main__':
    unittest.main()