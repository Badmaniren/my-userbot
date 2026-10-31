import unittest
from unittest.mock import patch, MagicMock
import subprocess
import os
import io
import uuid
import random
import string
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplier(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.applier = PatchApplier(self.repo_path)
        self.backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        self.patch_source = f"{uuid.uuid4().hex}.patch"

    @patch("subprocess.run")
    def test_create_recovery_point_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = self.applier.create_recovery_point(self.backup_tag)
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "branch", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_create_recovery_point_failure(self, mock_run):
        err_output = f"fatal: branch {self.backup_tag} already exists - {uuid.uuid4().hex}".encode('utf-8')
        mock_run.return_value = MagicMock(returncode=128, stderr=err_output)
        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.create_recovery_point(self.backup_tag)
        self.assertIn("Failed to create recovery point", str(ctx.exception))

    @patch("subprocess.run")
    @patch("builtins.open")
    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_apply_patch_success(self, mock_isfile, mock_exists, mock_open, mock_run):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        random_patch_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n+{uuid.uuid4().hex}".encode('utf-8')
        mock_open.return_value.__enter__.return_value = io.BytesIO(random_patch_content)
        mock_run.return_value = MagicMock(returncode=0)

        result = self.applier.apply_patch(self.patch_source)
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "apply"],
            input=random_patch_content,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("os.path.exists")
    def test_apply_patch_not_found(self, mock_exists):
        mock_exists.return_value = False
        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.apply_patch(self.patch_source)
        self.assertIn("Patch source not found", str(ctx.exception))

    @patch("subprocess.run")
    @patch("builtins.open")
    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_apply_patch_git_failure(self, mock_isfile, mock_exists, mock_open, mock_run):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_open.return_value.__enter__.return_value = io.BytesIO(b"corrupted patch")
        err_msg = f"error: patch failed: {uuid.uuid4().hex}".encode('utf-8')
        mock_run.return_value = MagicMock(returncode=1, stderr=err_msg)

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.apply_patch(self.patch_source)
        self.assertIn("Failed to apply patch", str(ctx.exception))

    @patch("subprocess.run")
    def test_rollback_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = self.applier.rollback(self.backup_tag)
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "checkout", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_rollback_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stderr=b"pathspec did not match any file(s)")
        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.rollback(self.backup_tag)
        self.assertIn("Failed to rollback", str(ctx.exception))

    @patch("subprocess.run")
    def test_verify_repository_state_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b"")
        result = self.applier.verify_repository_state()
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_verify_repository_state_failure(self, mock_run):
        dirty_output = f" M {uuid.uuid4().hex}.py\n".encode('utf-8')
        mock_run.return_value = MagicMock(returncode=0, stdout=dirty_output)
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
    def test_safe_apply_rollback_on_failure(self, mock_create, mock_apply, mock_rollback):
        mock_create.return_value = True
        mock_apply.side_effect = PatchApplierError(f"Apply error {uuid.uuid4().hex}")
        mock_rollback.return_value = True

        with self.assertRaises(PatchApplierError):
            self.applier.safe_apply(self.patch_source, self.backup_tag)

        mock_rollback.assert_called_once_with(self.backup_tag)

    @patch.object(PatchApplier, "rollback")
    @patch.object(PatchApplier, "apply_patch")
    @patch.object(PatchApplier, "create_recovery_point")
    def test_safe_apply_rollback_failure(self, mock_create, mock_apply, mock_rollback):
        mock_create.return_value = True
        mock_apply.side_effect = PatchApplierError("Apply error")
        mock_rollback.side_effect = Exception("Rollback catastrophe")

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.safe_apply(self.patch_source, self.backup_tag)
        self.assertIn("Failed to rollback after error", str(ctx.exception))

    @patch("subprocess.run")
    @patch("os.makedirs")
    @patch("builtins.open")
    @patch.object(PatchApplier, "verify_repository_state")
    @patch.object(PatchApplier, "create_recovery_point")
    def test_apply_patch_integration_function(self, mock_create_rp, mock_verify_repo, mock_open, mock_makedirs, mock_run):
        file_path = f"modules/{uuid.uuid4().hex}.py"
        content = f"print('{uuid.uuid4().hex}')"
        backup_id = f"tag_{uuid.uuid4().hex[:6]}"
        patch_data = {
            "file_path": file_path,
            "content": content,
            "backup_id": backup_id
        }

        mock_create_rp.return_value = True
        mock_verify_repo.return_value = True
        mock_run.return_value = MagicMock(returncode=0)

        result = apply_patch(self.repo_path, patch_data)
        self.assertTrue(result)
        mock_create_rp.assert_called_once_with(backup_id)
        mock_makedirs.assert_called_once()
        mock_open.assert_called_once()
        self.assertEqual(mock_run.call_count, 2)
        mock_verify_repo.assert_called_once()


if __name__ == "__main__":
    unittest.main()