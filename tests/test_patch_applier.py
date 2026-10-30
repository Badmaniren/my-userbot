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
        self.repo_path = os.path.join(os.sep, f"tmp_{uuid.uuid4().hex}")
        self.backup_tag = f"tag_{uuid.uuid4().hex}"
        self.patch_source = f"patch_{uuid.uuid4().hex}.diff"
        self.applier = PatchApplier(self.repo_path)

    @patch("skills.patch_applier.subprocess.run")
    def test_create_recovery_point_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        res = self.applier.create_recovery_point(self.backup_tag)
        self.assertTrue(res)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "branch", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("skills.patch_applier.subprocess.run")
    def test_create_recovery_point_failure(self, mock_run):
        err_msg = f"error_{uuid.uuid4().hex}".encode("utf-8")
        mock_result = MagicMock()
        mock_result.returncode = 128
        mock_result.stderr = err_msg
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.create_recovery_point(self.backup_tag)
        self.assertIn(err_msg.decode("utf-8"), str(ctx.exception))

    @patch("skills.patch_applier.os.path.exists")
    @patch("skills.patch_applier.os.path.isfile")
    @patch("skills.patch_applier.subprocess.run")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    def test_apply_patch_file_success(self, mock_file, mock_run, mock_isfile, mock_exists):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        patch_content_bytes = uuid.uuid4().hex.encode("utf-8")
        mock_file.return_value.read.return_value = patch_content_bytes

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        res = self.applier.apply_patch(self.patch_source)
        self.assertTrue(res)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "apply"],
            input=patch_content_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("skills.patch_applier.os.path.exists")
    @patch("skills.patch_applier.os.path.isfile")
    @patch("skills.patch_applier.subprocess.run")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    def test_apply_patch_failure(self, mock_file, mock_run, mock_isfile, mock_exists):
        mock_exists.return_value = True
        mock_isfile.return_value = True
        err_msg = f"fail_{uuid.uuid4().hex}".encode("utf-8")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = err_msg
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.apply_patch(self.patch_source)
        self.assertIn(err_msg.decode("utf-8"), str(ctx.exception))

    @patch("skills.patch_applier.os.path.exists")
    def test_apply_patch_file_not_found(self, mock_exists):
        mock_exists.return_value = False
        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.apply_patch(self.patch_source)
        self.assertIn(f"file not found {self.patch_source}", str(ctx.exception))

    @patch("skills.patch_applier.subprocess.run")
    def test_rollback_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        res = self.applier.rollback(self.backup_tag)
        self.assertTrue(res)
        self.assertEqual(mock_run.call_count, 2)
        mock_run.assert_any_call(
            ["git", "-C", self.repo_path, "checkout", "-f", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        mock_run.assert_any_call(
            ["git", "-C", self.repo_path, "clean", "-fd"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("skills.patch_applier.subprocess.run")
    def test_rollback_failure(self, mock_run):
        err_msg = f"rollback_err_{uuid.uuid4().hex}".encode("utf-8")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = err_msg
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.rollback(self.backup_tag)
        self.assertIn(err_msg.decode("utf-8"), str(ctx.exception))

    @patch("skills.patch_applier.subprocess.run")
    def test_verify_repository_state_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b""
        mock_run.return_value = mock_result

        res = self.applier.verify_repository_state()
        self.assertTrue(res)

    @patch("skills.patch_applier.subprocess.run")
    def test_verify_repository_state_failure_dirty(self, mock_run):
        dirty_output = f"M file_{uuid.uuid4().hex}.py\n".encode("utf-8")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = dirty_output
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.verify_repository_state()
        self.assertIn(dirty_output.decode("utf-8"), str(ctx.exception))

    @patch.object(PatchApplier, "create_recovery_point")
    @patch.object(PatchApplier, "apply_patch")
    @patch.object(PatchApplier, "verify_repository_state")
    def test_safe_apply_success(self, mock_verify, mock_apply, mock_create):
        res = self.applier.safe_apply(self.patch_source, self.backup_tag)
        self.assertTrue(res)
        mock_create.assert_called_once_with(self.backup_tag)
        mock_apply.assert_called_once_with(self.patch_source)
        mock_verify.assert_called_once()

    @patch.object(PatchApplier, "rollback")
    @patch.object(PatchApplier, "verify_repository_state")
    @patch.object(PatchApplier, "apply_patch")
    @patch.object(PatchApplier, "create_recovery_point")
    def test_safe_apply_failure_and_rollback(self, mock_create, mock_apply, mock_verify, mock_rollback):
        mock_verify.side_effect = PatchApplierError(f"error_{uuid.uuid4().hex}")

        with self.assertRaises(PatchApplierError):
            self.applier.safe_apply(self.patch_source, self.backup_tag)

        mock_create.assert_called_once_with(self.backup_tag)
        mock_apply.assert_called_once_with(self.patch_source)
        mock_rollback.assert_called_once_with(self.backup_tag)

    @patch("skills.patch_applier.os.makedirs")
    @patch("skills.patch_applier.subprocess.run")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch.object(PatchApplier, "create_recovery_point")
    @patch.object(PatchApplier, "verify_repository_state")
    def test_apply_patch_integration_function(self, mock_verify, mock_create, mock_file, mock_run, mock_makedirs):
        file_path = f"src/mod_{uuid.uuid4().hex}.py"
        content = f"print('{uuid.uuid4().hex}')"
        backup_id = f"bk_{uuid.uuid4().hex}"
        patch_data = {
            "file_path": file_path,
            "content": content,
            "backup_id": backup_id
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        res = apply_patch(self.repo_path, patch_data)
        self.assertTrue(res)

        mock_create.assert_called_once_with(backup_id)
        mock_makedirs.assert_called_once()
        mock_file.assert_called_once()
        mock_file().write.assert_called_once_with(content)
        mock_verify.assert_called_once()
        self.assertEqual(mock_run.call_count, 2)