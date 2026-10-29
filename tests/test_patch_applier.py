import unittest
from unittest.mock import patch
import os
import subprocess
import io
import uuid
import random

from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplier(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        self.patch_source = f"patch_{uuid.uuid4().hex[:8]}.diff"
        self.applier = PatchApplier(self.repo_path)

    @patch("subprocess.run")
    def test_create_recovery_point_success(self, mock_run):
        mock_run.return_value.returncode = 0
        result = self.applier.create_recovery_point(self.backup_tag)
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "branch", "-f", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_create_recovery_point_failure(self, mock_run):
        err_bytes = uuid.uuid4().bytes
        mock_run.return_value.returncode = random.randint(1, 255)
        mock_run.return_value.stderr = err_bytes

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.create_recovery_point(self.backup_tag)

        self.assertIn("Failed to create recovery point", str(ctx.exception))

    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("subprocess.run")
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data=b"random diff content")
    def test_apply_patch_file_success(self, mock_file, mock_run, mock_isfile, mock_exists):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_run.return_value.returncode = 0

        result = self.applier.apply_patch(self.patch_source)
        self.assertTrue(result)
        mock_run.assert_called_once()

    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("subprocess.run")
    def test_apply_patch_failure(self, mock_run, mock_isfile, mock_exists):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        err_bytes = uuid.uuid4().bytes
        mock_run.return_value.returncode = random.randint(1, 255)
        mock_run.return_value.stderr = err_bytes

        with patch("builtins.open", unittest.mock.mock_open(read_data=b"corrupted diff")):
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.apply_patch(self.patch_source)
            self.assertIn("Failed to apply patch", str(ctx.exception))

    @patch("os.path.exists")
    def test_apply_patch_not_found(self, mock_exists):
        mock_exists.return_value = False
        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.apply_patch(self.patch_source)
        self.assertIn("Patch source not found or invalid", str(ctx.exception))

    @patch("subprocess.run")
    def test_rollback_success(self, mock_run):
        mock_run.return_value.returncode = 0
        result = self.applier.rollback(self.backup_tag)
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "checkout", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_rollback_failure(self, mock_run):
        mock_run.return_value.returncode = random.randint(1, 255)
        mock_run.return_value.stderr = uuid.uuid4().bytes

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.rollback(self.backup_tag)
        self.assertIn("Failed to rollback", str(ctx.exception))

    @patch("subprocess.run")
    def test_verify_repository_state_success(self, mock_run):
        mock_run.return_value.returncode = 0
        result = self.applier.verify_repository_state()
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_verify_repository_state_failure(self, mock_run):
        mock_run.return_value.returncode = random.randint(1, 255)
        mock_run.return_value.stdout = uuid.uuid4().bytes

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.verify_repository_state()
        self.assertIn("Repository verification failed", str(ctx.exception))

    @patch.object(PatchApplier, "create_recovery_point")
    @patch.object(PatchApplier, "apply_patch")
    @patch.object(PatchApplier, "verify_repository_state")
    def test_safe_apply_success(self, mock_verify, mock_apply, mock_create):
        mock_create.return_value = True
        mock_apply.return_value = True
        mock_verify.return_value = True

        result = self.applier.safe_apply(self.patch_source, self.backup_tag)
        self.assertTrue(result)
        mock_create.assert_called_once_with(self.backup_tag)
        mock_apply.assert_called_once_with(self.patch_source)
        mock_verify.assert_called_once()

    @patch.object(PatchApplier, "rollback")
    @patch.object(PatchApplier, "apply_patch")
    @patch.object(PatchApplier, "create_recovery_point")
    def test_safe_apply_failure_triggers_rollback(self, mock_create, mock_apply, mock_rollback):
        mock_create.return_value = True
        mock_apply.side_effect = PatchApplierError(uuid.uuid4().hex)
        mock_rollback.return_value = True

        with self.assertRaises(PatchApplierError):
            self.applier.safe_apply(self.patch_source, self.backup_tag)

        mock_rollback.assert_called_once_with(self.backup_tag)

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch("skills.patch_applier.PatchApplier.create_recovery_point")
    @patch("skills.patch_applier.PatchApplier.verify_repository_state")
    def test_apply_patch_integration_function(self, mock_verify, mock_create, mock_file, mock_run):
        file_name = f"file_{uuid.uuid4().hex}.py"
        file_content = f"print('{uuid.uuid4().hex}')"
        backup_id = f"tag_{uuid.uuid4().hex}"

        patch_data = {
            "file_path": file_name,
            "content": file_content,
            "backup_id": backup_id
        }

        mock_create.return_value = True
        mock_verify.return_value = True
        mock_run.return_value.returncode = 0

        res = apply_patch(self.repo_path, patch_data)
        self.assertTrue(res)
        mock_file.assert_called()
        mock_create.assert_called_once_with(backup_id)
        mock_verify.assert_called_once()


if __name__ == "__main__":
    unittest.main()