import unittest
from unittest.mock import patch, MagicMock
import os
import io
import subprocess
import uuid
import random
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplierInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.applier = PatchApplier(self.repo_path)
        self.backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        self.patch_filename = f"patch_{uuid.uuid4().hex[:8]}.patch"
        self.patch_path = os.path.join(self.repo_path, self.patch_filename)
        self.random_content = f"content_{uuid.uuid4().hex}".encode("utf-8")

    @patch("subprocess.run")
    def test_create_recovery_point_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr=b"")
        result = self.applier.create_recovery_point(self.backup_tag)
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "branch", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_create_recovery_point_failure(self, mock_run):
        error_msg = f"error_{uuid.uuid4().hex}".encode("utf-8")
        mock_run.return_value = MagicMock(returncode=1, stderr=error_msg)
        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.create_recovery_point(self.backup_tag)
        self.assertIn(error_msg.decode("utf-8"), str(ctx.exception))

    @patch("subprocess.run")
    @patch("builtins.open")
    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_apply_patch_success(self, mock_isfile, mock_exists, mock_open_file, mock_run):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_open_file.return_value.__enter__.return_value = io.BytesIO(self.random_content)
        mock_run.return_value = MagicMock(returncode=0, stderr=b"")

        result = self.applier.apply_patch(self.patch_filename)
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "apply"],
            input=self.random_content,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    @patch("builtins.open")
    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_apply_patch_failure(self, mock_isfile, mock_exists, mock_open_file, mock_run):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_open_file.return_value.__enter__.return_value = io.BytesIO(self.random_content)
        error_output = f"failed_patch_{uuid.uuid4().hex}".encode("utf-8")
        mock_run.return_value = MagicMock(returncode=1, stderr=error_output)

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.apply_patch(self.patch_filename)
        self.assertIn(error_output.decode("utf-8"), str(ctx.exception))

    @patch("subprocess.run")
    def test_rollback_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr=b"")
        result = self.applier.rollback(self.backup_tag)
        self.assertTrue(result)
        self.assertEqual(mock_run.call_count, 2)
        mock_run.assert_has_calls([
            unittest.mock.call(
                ["git", "-C", self.repo_path, "checkout", self.backup_tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            ),
            unittest.mock.call(
                ["git", "-C", self.repo_path, "clean", "-fd"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        ])

    @patch("subprocess.run")
    def test_rollback_failure(self, mock_run):
        err_msg = f"rollback_err_{uuid.uuid4().hex}".encode("utf-8")
        mock_run.return_value = MagicMock(returncode=1, stderr=err_msg)
        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.rollback(self.backup_tag)
        self.assertIn(err_msg.decode("utf-8"), str(ctx.exception))

    @patch("subprocess.run")
    def test_verify_repository_state_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b"")
        result = self.applier.verify_repository_state()
        self.assertTrue(result)

    @patch("subprocess.run")
    def test_verify_repository_state_failure_nonzero(self, mock_run):
        out_msg = f"dirty_repo_{uuid.uuid4().hex}".encode("utf-8")
        mock_run.return_value = MagicMock(returncode=1, stdout=out_msg)
        with self.assertRaises(PatchApplierError):
            self.applier.verify_repository_state()

    @patch("subprocess.run")
    def test_verify_repository_state_failure_output(self, mock_run):
        out_msg = f"modified_file_{uuid.uuid4().hex}".encode("utf-8")
        mock_run.return_value = MagicMock(returncode=0, stdout=out_msg)
        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.verify_repository_state()
        self.assertIn(out_msg.decode("utf-8"), str(ctx.exception))

    def test_safe_apply_success(self):
        with patch.object(self.applier, "create_recovery_point") as mock_create, \
             patch.object(self.applier, "apply_patch") as mock_apply, \
             patch.object(self.applier, "verify_repository_state") as mock_verify:

            mock_create.return_value = True
            mock_apply.return_value = True
            mock_verify.return_value = True

            res = self.applier.safe_apply(self.patch_path, self.backup_tag)
            self.assertTrue(res)
            mock_create.assert_called_once_with(self.backup_tag)
            mock_apply.assert_called_once_with(self.patch_path)
            mock_verify.assert_called_once()

    def test_safe_apply_failure_and_rollback(self):
        with patch.object(self.applier, "create_recovery_point") as mock_create, \
             patch.object(self.applier, "apply_patch") as mock_apply, \
             patch.object(self.applier, "rollback") as mock_rollback:

            mock_create.return_value = True
            mock_apply.side_effect = PatchApplierError(f"error_{uuid.uuid4().hex}")
            mock_rollback.return_value = True

            with self.assertRaises(PatchApplierError):
                self.applier.safe_apply(self.patch_path, self.backup_tag)

            mock_create.assert_called_once_with(self.backup_tag)
            mock_apply.assert_called_once_with(self.patch_path)
            mock_rollback.assert_called_once_with(self.backup_tag)

    @patch("subprocess.run")
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    def test_apply_patch_integration_function(self, mock_file_open, mock_makedirs, mock_run):
        file_path = f"src/{uuid.uuid4().hex}.py"
        content = f"print('{uuid.uuid4().hex}')"
        backup_id = f"bk_{uuid.uuid4().hex[:6]}"
        patch_data = {
            "file_path": file_path,
            "content": content,
            "backup_id": backup_id
        }

        mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")

        res = apply_patch(self.repo_path, patch_data)
        self.assertTrue(res)

        mock_makedirs.assert_called_once()
        mock_file_open.assert_called_once()
        mock_file_open().write.assert_called_once_with(content)
        self.assertEqual(mock_run.call_count, 4)