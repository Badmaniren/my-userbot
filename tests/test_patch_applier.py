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
        self.repo_path = os.path.join(os.getcwd(), uuid.uuid4().hex)
        self.applier = PatchApplier(self.repo_path)
        self.backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        self.patch_file = f"patch_{uuid.uuid4().hex[:8]}.diff"

    @patch("subprocess.run")
    def test_create_recovery_point_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")
        result = self.applier.create_recovery_point(self.backup_tag)
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "branch", "-f", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_create_recovery_point_failure(self, mock_run):
        err_message = f"error_{uuid.uuid4().hex}"
        mock_run.return_value = MagicMock(returncode=128, stdout=b"", stderr=err_message.encode("utf-8"))
        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.create_recovery_point(self.backup_tag)
        self.assertIn(err_message, str(ctx.exception))

    @patch("subprocess.run")
    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_apply_patch_success(self, mock_isfile, mock_exists, mock_run):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")

        random_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}".encode("utf-8")

        with patch("builtins.open", unittest.mock.mock_open(read_data=random_content)):
            result = self.applier.apply_patch(self.patch_file)
            self.assertTrue(result)
            mock_run.assert_called_once()

    @patch("subprocess.run")
    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_apply_patch_failure(self, mock_isfile, mock_exists, mock_run):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        err_message = f"fail_{uuid.uuid4().hex}"
        mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=err_message.encode("utf-8"))

        random_content = uuid.uuid4().hex.encode("utf-8")
        with patch("builtins.open", unittest.mock.mock_open(read_data=random_content)):
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.apply_patch(self.patch_file)
            self.assertIn(err_message, str(ctx.exception))

    @patch("subprocess.run")
    def test_rollback_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")
        result = self.applier.rollback(self.backup_tag)
        self.assertTrue(result)
        mock_run.assert_any_call(
            ["git", "-C", self.repo_path, "checkout", "-f", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_rollback_failure(self, mock_run):
        err_message = f"rollback_err_{uuid.uuid4().hex}"
        mock_run.return_value = MagicMock(returncode=1, stdout=b"", stderr=err_message.encode("utf-8"))
        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.rollback(self.backup_tag)
        self.assertIn(err_message, str(ctx.exception))

    @patch("subprocess.run")
    def test_verify_repository_state_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")
        result = self.applier.verify_repository_state()
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "status", "--porcelain"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_verify_repository_state_failure(self, mock_run):
        stdout_msg = f"dirty_{uuid.uuid4().hex}"
        mock_run.return_value = MagicMock(returncode=1, stdout=stdout_msg.encode("utf-8"), stderr=b"")
        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.verify_repository_state()
        self.assertIn(stdout_msg, str(ctx.exception))

    @patch.object(PatchApplier, "create_recovery_point")
    @patch.object(PatchApplier, "apply_patch")
    @patch.object(PatchApplier, "verify_repository_state")
    def test_safe_apply_success(self, mock_verify, mock_apply, mock_create):
        mock_create.return_value = True
        mock_apply.return_value = True
        mock_verify.return_value = True

        result = self.applier.safe_apply(self.patch_file, self.backup_tag)
        self.assertTrue(result)
        mock_create.assert_called_once_with(self.backup_tag)
        mock_apply.assert_called_once_with(self.patch_file)
        mock_verify.assert_called_once()

    @patch.object(PatchApplier, "rollback")
    @patch.object(PatchApplier, "apply_patch")
    @patch.object(PatchApplier, "create_recovery_point")
    def test_safe_apply_rollback_on_error(self, mock_create, mock_apply, mock_rollback):
        mock_create.return_value = True
        mock_apply.side_effect = PatchApplierError(uuid.uuid4().hex)
        mock_rollback.return_value = True

        with self.assertRaises(PatchApplierError):
            self.applier.safe_apply(self.patch_file, self.backup_tag)

        mock_create.assert_called_once_with(self.backup_tag)
        mock_apply.assert_called_once_with(self.patch_file)
        mock_rollback.assert_called_once_with(self.backup_tag)

    @patch("subprocess.run")
    def test_apply_patch_integration_function(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")
        file_path = f"src/{uuid.uuid4().hex}.py"
        content = f"print('{uuid.uuid4().hex}')"
        backup_id = f"bk_{uuid.uuid4().hex[:6]}"
        patch_data = {
            "file_path": file_path,
            "content": content,
            "backup_id": backup_id
        }

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            result = apply_patch(self.repo_path, patch_data)
            self.assertTrue(result)
            mock_file.assert_called_once_with(os.path.join(self.repo_path, file_path), "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(content)
            self.assertGreaterEqual(mock_run.call_count, 3)


if __name__ == "__main__":
    unittest.main()