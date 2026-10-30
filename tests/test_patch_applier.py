import unittest
from unittest.mock import patch, MagicMock
import os
import io
import uuid
import random
import subprocess
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplier(unittest.TestCase):

    def setUp(self):
        self.repo_path = os.path.join("/tmp", uuid.uuid4().hex)
        self.applier = PatchApplier(self.repo_path)
        self.backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        self.patch_source = f"{uuid.uuid4().hex}.patch"

    @patch("subprocess.run")
    def test_create_recovery_point_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        res = self.applier.create_recovery_point(self.backup_tag)
        self.assertTrue(res)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "branch", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_create_recovery_point_failure(self, mock_run):
        err_msg = f"git_error_{uuid.uuid4().hex}"
        mock_res = MagicMock(returncode=1, stderr=err_msg.encode("utf-8"))
        mock_run.return_value = mock_res
        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.create_recovery_point(self.backup_tag)
        self.assertIn(err_msg, str(ctx.exception))

    @patch("subprocess.run")
    @patch("builtins.open")
    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_apply_patch_success(self, mock_isfile, mock_exists, mock_open, mock_run):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        random_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}".encode("utf-8")
        mock_open.return_value.__enter__.return_value = io.BytesIO(random_content)
        mock_run.return_value = MagicMock(returncode=0)

        res = self.applier.apply_patch(self.patch_source)
        self.assertTrue(res)
        mock_run.assert_any_call(
            ["git", "-C", self.repo_path, "apply"],
            input=random_content,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    @patch("builtins.open")
    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_apply_patch_failure(self, mock_isfile, mock_exists, mock_open, mock_run):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        random_content = uuid.uuid4().hex.encode("utf-8")
        mock_open.return_value.__enter__.return_value = io.BytesIO(random_content)
        err_out = f"patch_failed_{uuid.uuid4().hex}"
        mock_run.return_value = MagicMock(returncode=1, stderr=err_out.encode("utf-8"))

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.apply_patch(self.patch_source)
        self.assertIn(err_out, str(ctx.exception))

    @patch("subprocess.run")
    def test_rollback_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        res = self.applier.rollback(self.backup_tag)
        self.assertTrue(res)
        self.assertEqual(mock_run.call_count, 3)
        mock_run.assert_called_with(
            ["git", "-C", self.repo_path, "checkout", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_rollback_failure(self, mock_run):
        err_msg = f"rollback_err_{uuid.uuid4().hex}"
        mock_run.return_value = MagicMock(returncode=1, stderr=err_msg.encode("utf-8"))
        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.rollback(self.backup_tag)
        self.assertIn(err_msg, str(ctx.exception))

    @patch("subprocess.run")
    def test_verify_repository_state_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b"")
        res = self.applier.verify_repository_state()
        self.assertTrue(res)

    @patch("subprocess.run")
    def test_verify_repository_state_failure(self, mock_run):
        dirty_output = f"M file_{uuid.uuid4().hex}.py\n".encode("utf-8")
        mock_run.return_value = MagicMock(returncode=0, stdout=dirty_output)
        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.verify_repository_state()
        self.assertIn("Repository verification failed", str(ctx.exception))

    @patch("skills.patch_applier.PatchApplier.verify_repository_state")
    @patch("skills.patch_applier.PatchApplier.apply_patch")
    @patch("skills.patch_applier.PatchApplier.create_recovery_point")
    def test_safe_apply_success(self, mock_create, mock_apply, mock_verify):
        mock_create.return_value = True
        mock_apply.return_value = True
        mock_verify.return_value = True

        res = self.applier.safe_apply(self.patch_source, self.backup_tag)
        self.assertTrue(res)
        mock_create.assert_called_once_with(self.backup_tag)
        mock_apply.assert_called_once_with(self.patch_source)
        mock_verify.assert_called_once()

    @patch("skills.patch_applier.PatchApplier.rollback")
    @patch("skills.patch_applier.PatchApplier.apply_patch")
    @patch("skills.patch_applier.PatchApplier.create_recovery_point")
    def test_safe_apply_rollback_on_error(self, mock_create, mock_apply, mock_rollback):
        mock_create.return_value = True
        mock_apply.side_effect = PatchApplierError(uuid.uuid4().hex)
        mock_rollback.return_value = True

        with self.assertRaises(PatchApplierError):
            self.applier.safe_apply(self.patch_source, self.backup_tag)

        mock_rollback.assert_called_once_with(self.backup_tag)

    @patch("subprocess.run")
    @patch("builtins.open")
    @patch("os.makedirs")
    @patch("skills.patch_applier.PatchApplier.verify_repository_state")
    @patch("skills.patch_applier.PatchApplier.create_recovery_point")
    def test_apply_patch_integration_function(self, mock_create, mock_verify, mock_makedirs, mock_open, mock_run):
        mock_create.return_value = True
        mock_verify.return_value = True
        file_path = f"src/{uuid.uuid4().hex}.py"
        content = f"print('{uuid.uuid4().hex}')"
        backup_id = f"rev_{uuid.uuid4().hex[:6]}"
        patch_data = {
            "file_path": file_path,
            "content": content,
            "backup_id": backup_id
        }

        mock_file_instance = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file_instance

        res = apply_patch(self.repo_path, patch_data)
        self.assertTrue(res)
        mock_create.assert_called_once_with(backup_id)
        mock_makedirs.assert_called_once()
        mock_file_instance.write.assert_called_once_with(content)
        self.assertEqual(mock_run.call_count, 2)
        mock_verify.assert_called_once()


if __name__ == "__main__":
    unittest.main()