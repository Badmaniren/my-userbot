import unittest
from unittest.mock import patch
import subprocess
import os
import uuid
import random
import io

from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplierInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        self.patch_source = f"{uuid.uuid4().hex}.patch"
        self.applier = PatchApplier(self.repo_path)

    @patch("skills.patch_applier.subprocess.run")
    def test_create_recovery_point_success(self, mock_run):
        mock_result = mock_run.return_value
        mock_result.returncode = 0

        res = self.applier.create_recovery_point(self.backup_tag)
        self.assertTrue(res)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "branch", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("skills.patch_applier.subprocess.run")
    def test_create_recovery_point_failure(self, mock_run):
        err_msg = f"fatal: branch {self.backup_tag} already exists"
        mock_result = mock_run.return_value
        mock_result.returncode = 128
        mock_result.stderr = err_msg.encode("utf-8")

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.create_recovery_point(self.backup_tag)
        self.assertIn("Failed to create recovery point", str(ctx.exception))

    @patch("skills.patch_applier.os.path.exists")
    @patch("skills.patch_applier.os.path.isfile")
    @patch("skills.patch_applier.subprocess.run")
    def test_apply_patch_file_success(self, mock_run, mock_isfile, mock_exists):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_result = mock_run.return_value
        mock_result.returncode = 0

        patch_content_bytes = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n".encode("utf-8")

        with patch("builtins.open", unittest.mock.mock_open(read_data=patch_content_bytes)):
            res = self.applier.apply_patch(self.patch_source)
            self.assertTrue(res)
            mock_run.assert_called_once()

    @patch("skills.patch_applier.os.path.exists")
    @patch("skills.patch_applier.os.path.isfile")
    @patch("skills.patch_applier.subprocess.run")
    def test_apply_patch_failure(self, mock_run, mock_isfile, mock_exists):
        mock_exists.return_value = False
        err_msg = f"error: patch failed: {uuid.uuid4().hex}"
        mock_result = mock_run.return_value
        mock_result.returncode = 1
        mock_result.stderr = err_msg.encode("utf-8")

        patch_content_bytes = f"invalid patch {uuid.uuid4().hex}\n".encode("utf-8")

        with patch("builtins.open", unittest.mock.mock_open(read_data=patch_content_bytes)):
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.apply_patch(self.patch_source)
            self.assertIn("Failed to apply patch", str(ctx.exception))

    @patch("skills.patch_applier.subprocess.run")
    def test_rollback_success(self, mock_run):
        mock_result = mock_run.return_value
        mock_result.returncode = 0

        res = self.applier.rollback(self.backup_tag)
        self.assertTrue(res)
        self.assertEqual(mock_run.call_count, 3)

    @patch("skills.patch_applier.subprocess.run")
    def test_rollback_failure(self, mock_run):
        mock_result = mock_run.return_value
        mock_result.returncode = 1
        err_msg = f"pathspec '{self.backup_tag}' did not match any file(s) known to git"
        mock_result.stderr = err_msg.encode("utf-8")

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.rollback(self.backup_tag)
        self.assertIn("Failed to rollback", str(ctx.exception))

    @patch("skills.patch_applier.subprocess.run")
    def test_verify_repository_state_success(self, mock_run):
        mock_result = mock_run.return_value
        mock_result.returncode = 0
        mock_result.stdout = b""

        res = self.applier.verify_repository_state()
        self.assertTrue(res)

    @patch("skills.patch_applier.subprocess.run")
    def test_verify_repository_state_failure(self, mock_run):
        mock_result = mock_run.return_value
        mock_result.returncode = 0
        dirty_output = f" M {uuid.uuid4().hex}.py\n".encode("utf-8")
        mock_result.stdout = dirty_output

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.verify_repository_state()
        self.assertIn("Repository verification failed", str(ctx.exception))

    @patch.object(PatchApplier, "create_recovery_point")
    @patch.object(PatchApplier, "apply_patch")
    @patch.object(PatchApplier, "verify_repository_state")
    @patch.object(PatchApplier, "rollback")
    def test_safe_apply_success(self, mock_rollback, mock_verify, mock_apply, mock_create):
        mock_create.return_value = True
        mock_apply.return_value = True
        mock_verify.return_value = True

        res = self.applier.safe_apply(self.patch_source, self.backup_tag)
        self.assertTrue(res)
        mock_create.assert_called_once_with(self.backup_tag)
        mock_apply.assert_called_once_with(self.patch_source)
        mock_verify.assert_called_once()
        mock_rollback.assert_not_called()

    @patch.object(PatchApplier, "create_recovery_point")
    @patch.object(PatchApplier, "apply_patch")
    @patch.object(PatchApplier, "verify_repository_state")
    @patch.object(PatchApplier, "rollback")
    def test_safe_apply_failure_triggers_rollback(self, mock_rollback, mock_verify, mock_apply, mock_create):
        mock_create.return_value = True
        err_msg = f"error applying {uuid.uuid4().hex}"
        mock_apply.side_effect = PatchApplierError(err_msg)
        mock_rollback.return_value = True

        with self.assertRaises(PatchApplierError):
            self.applier.safe_apply(self.patch_source, self.backup_tag)

        mock_create.assert_called_once_with(self.backup_tag)
        mock_apply.assert_called_once_with(self.patch_source)
        mock_verify.assert_not_called()
        mock_rollback.assert_called_once_with(self.backup_tag)

    @patch("skills.patch_applier.subprocess.run")
    @patch("skills.patch_applier.os.makedirs")
    @patch.object(PatchApplier, "create_recovery_point")
    @patch.object(PatchApplier, "verify_repository_state")
    def test_apply_patch_integration_function(self, mock_verify, mock_create, mock_makedirs, mock_run):
        mock_create.return_value = True
        mock_verify.return_value = True
        mock_run.return_value.returncode = 0

        target_file = f"src/{uuid.uuid4().hex}.py"
        target_content = f"# content {uuid.uuid4().hex}"
        backup_id = f"backup_{uuid.uuid4().hex[:6]}"

        patch_data = {
            "file_path": target_file,
            "content": target_content,
            "backup_id": backup_id
        }

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res = apply_patch(self.repo_path, patch_data)
            self.assertTrue(res)
            mock_create.assert_called_once_with(backup_id)
            mock_makedirs.assert_called_once()
            mock_file.assert_called_once()
            mock_file().write.assert_called_once_with(target_content)
            self.assertEqual(mock_run.call_count, 2)
            mock_verify.assert_called_once()


if __name__ == "__main__":
    unittest.main()