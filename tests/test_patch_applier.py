import unittest
from unittest.mock import patch, MagicMock
import os
import io
import uuid
import random
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplier(unittest.TestCase):
    def setUp(self):
        self.repo_path = os.path.join("/tmp", uuid.uuid4().hex)
        self.applier = PatchApplier(self.repo_path)
        self.backup_tag = uuid.uuid4().hex
        self.patch_filename = f"{uuid.uuid4().hex}.patch"

    @patch("skills.patch_applier.subprocess.run")
    def test_create_recovery_point_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = self.applier.create_recovery_point(self.backup_tag)
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "branch", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("skills.patch_applier.subprocess.run")
    def test_create_recovery_point_failure(self, mock_run):
        err_message = uuid.uuid4().hex.encode("utf-8")
        mock_result = MagicMock()
        mock_result.returncode = 128
        mock_result.stderr = err_message
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.create_recovery_point(self.backup_tag)
        self.assertIn(err_message.decode("utf-8"), str(ctx.exception))

    @patch("skills.patch_applier.os.path.exists")
    @patch("skills.patch_applier.os.path.isfile")
    @patch("skills.patch_applier.subprocess.run")
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data=b"random patch content")
    def test_apply_patch_file_exists(self, mock_file, mock_run, mock_isfile, mock_exists):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = self.applier.apply_patch(self.patch_filename)
        self.assertTrue(result)
        mock_file.assert_called_once()
        mock_run.assert_called_once()

    @patch("skills.patch_applier.os.path.exists")
    @patch("skills.patch_applier.subprocess.run")
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data=b"fail patch content")
    def test_apply_patch_failure(self, mock_file, mock_run, mock_exists):
        mock_exists.return_value = True
        err_message = uuid.uuid4().hex.encode("utf-8")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = err_message
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.apply_patch(self.patch_filename)
        self.assertIn(err_message.decode("utf-8"), str(ctx.exception))

    @patch("skills.patch_applier.os.path.exists")
    def test_apply_patch_source_not_found(self, mock_exists):
        mock_exists.return_value = False

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.apply_patch(self.patch_filename)
        self.assertIn(self.patch_filename, str(ctx.exception))

    @patch("skills.patch_applier.subprocess.run")
    def test_rollback_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = self.applier.rollback(self.backup_tag)
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "checkout", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("skills.patch_applier.subprocess.run")
    def test_rollback_failure(self, mock_run):
        err_message = uuid.uuid4().hex.encode("utf-8")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = err_message
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.rollback(self.backup_tag)
        self.assertIn(err_message.decode("utf-8"), str(ctx.exception))

    @patch("skills.patch_applier.subprocess.run")
    def test_verify_repository_state_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b""
        mock_run.return_value = mock_result

        result = self.applier.verify_repository_state()
        self.assertTrue(result)

    @patch("skills.patch_applier.subprocess.run")
    def test_verify_repository_state_failure(self, mock_run):
        stdout_msg = uuid.uuid4().hex.encode("utf-8")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = stdout_msg
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.verify_repository_state()
        self.assertIn(stdout_msg.decode("utf-8"), str(ctx.exception))

    @patch.object(PatchApplier, "create_recovery_point")
    @patch.object(PatchApplier, "apply_patch")
    @patch.object(PatchApplier, "verify_repository_state")
    def test_safe_apply_success(self, mock_verify, mock_apply, mock_create):
        mock_create.return_value = True
        mock_apply.return_value = True
        mock_verify.return_value = True

        result = self.applier.safe_apply(self.patch_filename, self.backup_tag)
        self.assertTrue(result)
        mock_create.assert_called_once_with(self.backup_tag)
        mock_apply.assert_called_once_with(self.patch_filename)
        mock_verify.assert_called_once()

    @patch.object(PatchApplier, "rollback")
    @patch.object(PatchApplier, "verify_repository_state")
    @patch.object(PatchApplier, "apply_patch")
    @patch.object(PatchApplier, "create_recovery_point")
    def test_safe_apply_rollback_on_error(self, mock_create, mock_apply, mock_verify, mock_rollback):
        mock_create.return_value = True
        mock_apply.side_effect = PatchApplierError(uuid.uuid4().hex)
        mock_rollback.return_value = True

        with self.assertRaises(PatchApplierError):
            self.applier.safe_apply(self.patch_filename, self.backup_tag)

        mock_rollback.assert_called_once_with(self.backup_tag)

    @patch("skills.patch_applier.subprocess.run")
    @patch("skills.patch_applier.os.makedirs")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch.object(PatchApplier, "create_recovery_point")
    @patch.object(PatchApplier, "verify_repository_state")
    def test_apply_patch_integration_function(self, mock_verify, mock_create, mock_file, mock_makedirs, mock_run):
        file_path = f"src/{uuid.uuid4().hex}.py"
        content = f"print('{uuid.uuid4().hex}')"
        backup_id = uuid.uuid4().hex
        patch_data = {
            "file_path": file_path,
            "content": content,
            "backup_id": backup_id
        }

        mock_create.return_value = True
        mock_verify.return_value = True
        mock_run_result = MagicMock()
        mock_run_result.returncode = 0
        mock_run.return_value = mock_run_result

        result = apply_patch(self.repo_path, patch_data)
        self.assertTrue(result)
        mock_create.assert_called_once_with(backup_id)
        mock_file.assert_called_once()
        self.assertEqual(mock_run.call_count, 2)
        mock_verify.assert_called_once()


if __name__ == "__main__":
    unittest.main()