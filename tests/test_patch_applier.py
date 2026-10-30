import unittest
from unittest.mock import patch, MagicMock
import os
import subprocess
import io
import uuid
import random
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplier(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.applier = PatchApplier(self.repo_path)

    @patch("subprocess.run")
    def test_create_recovery_point_success(self, mock_run):
        tag = uuid.uuid4().hex
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = self.applier.create_recovery_point(tag)
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "branch", tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_create_recovery_point_failure(self, mock_run):
        tag = uuid.uuid4().hex
        err_output = uuid.uuid4().hex.encode("utf-8")
        mock_result = MagicMock()
        mock_result.returncode = 128
        mock_result.stderr = err_output
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError):
            self.applier.create_recovery_point(tag)

    @patch("subprocess.run")
    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    def test_apply_patch_success(self, mock_file, mock_isfile, mock_exists, mock_run):
        patch_name = f"{uuid.uuid4().hex}.patch"
        mock_exists.return_value = True
        mock_isfile.return_value = True
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = self.applier.apply_patch(patch_name)
        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch("subprocess.run")
    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    def test_apply_patch_failure(self, mock_file, mock_isfile, mock_exists, mock_run):
        patch_name = f"{uuid.uuid4().hex}.patch"
        mock_exists.return_value = False
        
        err_bytes = uuid.uuid4().hex.encode("utf-8")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = err_bytes
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError):
            self.applier.apply_patch(patch_name)

    @patch("subprocess.run")
    def test_rollback_success(self, mock_run):
        tag = uuid.uuid4().hex
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = self.applier.rollback(tag)
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "checkout", tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_rollback_failure(self, mock_run):
        tag = uuid.uuid4().hex
        err_bytes = uuid.uuid4().hex.encode("utf-8")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = err_bytes
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError):
            self.applier.rollback(tag)

    @patch("subprocess.run")
    def test_verify_repository_state_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b""
        mock_run.return_value = mock_result

        result = self.applier.verify_repository_state()
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_verify_repository_state_failure(self, mock_run):
        dirty_output = uuid.uuid4().hex.encode("utf-8")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = dirty_output
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError):
            self.applier.verify_repository_state()

    @patch("skills.patch_applier.PatchApplier.verify_repository_state")
    @patch("skills.patch_applier.PatchApplier.apply_patch")
    @patch("skills.patch_applier.PatchApplier.create_recovery_point")
    def test_safe_apply_success(self, mock_create, mock_apply, mock_verify):
        patch_path = f"{uuid.uuid4().hex}.patch"
        backup_tag = uuid.uuid4().hex

        result = self.applier.safe_apply(patch_path, backup_tag)
        self.assertTrue(result)
        mock_create.assert_called_once_with(backup_tag)
        mock_apply.assert_called_once_with(patch_path)
        mock_verify.assert_called_once()

    @patch("skills.patch_applier.PatchApplier.rollback")
    @patch("skills.patch_applier.PatchApplier.apply_patch")
    @patch("skills.patch_applier.PatchApplier.create_recovery_point")
    def test_safe_apply_rollback_on_failure(self, mock_create, mock_apply, mock_rollback):
        patch_path = f"{uuid.uuid4().hex}.patch"
        backup_tag = uuid.uuid4().hex
        mock_apply.side_effect = PatchApplierError(uuid.uuid4().hex)

        with self.assertRaises(PatchApplierError):
            self.applier.safe_apply(patch_path, backup_tag)

        mock_create.assert_called_once_with(backup_tag)
        mock_rollback.assert_called_once_with(backup_tag)

    @patch("subprocess.run")
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch("skills.patch_applier.PatchApplier.create_recovery_point")
    @patch("skills.patch_applier.PatchApplier.verify_repository_state")
    def test_apply_patch_integration_func(self, mock_verify, mock_create, mock_file, mock_makedirs, mock_run):
        file_path = f"dir_{uuid.uuid4().hex}/{uuid.uuid4().hex}.py"
        content = uuid.uuid4().hex
        backup_id = uuid.uuid4().hex
        patch_data = {
            "file_path": file_path,
            "content": content,
            "backup_id": backup_id
        }

        result = apply_patch(self.repo_path, patch_data)
        self.assertTrue(result)
        mock_create.assert_called_once_with(backup_id)
        mock_makedirs.assert_called_once()
        mock_file.assert_called_once()
        self.assertEqual(mock_run.call_count, 2)
        mock_verify.assert_called_once()


if __name__ == "__main__":
    unittest.main()