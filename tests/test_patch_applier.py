import unittest
from unittest.mock import patch, MagicMock
import os
import io
import uuid
import random
import string
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplierInquisition(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        self.patch_filename = f"{uuid.uuid4().hex[:6]}.patch"
        self.initial_content = f"content_{uuid.uuid4().hex}"
        self.applier = PatchApplier(self.repo_path)

    def test_create_recovery_point_success(self):
        random_branch = f"br_{uuid.uuid4().hex[:8]}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            res = self.applier.create_recovery_point(random_branch)
            self.assertTrue(res)
            mock_run.assert_called_once()
            called_args = mock_run.call_args[0][0]
            self.assertIn("branch", called_args)
            self.assertIn(random_branch, called_args)

    def test_create_recovery_point_failure(self):
        random_branch = f"br_{uuid.uuid4().hex[:8]}"
        error_msg = f"err_{uuid.uuid4().hex}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 128
            mock_run.return_value.stderr = error_msg.encode("utf-8")
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.create_recovery_point(random_branch)
            self.assertIn(error_msg, str(ctx.exception))

    def test_apply_patch_file_exists(self):
        patch_content_bytes = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n".encode("utf-8")
        with patch("os.path.isabs", return_value=True), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", return_value=io.BytesIO(patch_content_bytes)), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            res = self.applier.apply_patch(self.patch_filename)
            self.assertTrue(res)
            mock_run.assert_called_once()
            self.assertEqual(mock_run.call_args[1]["input"], patch_content_bytes)

    def test_apply_patch_failure(self):
        patch_content_bytes = f"invalid_patch_{uuid.uuid4().hex}".encode("utf-8")
        error_stderr = f"git_apply_error_{uuid.uuid4().hex}".encode("utf-8")
        with patch("os.path.isabs", return_value=True), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", return_value=io.BytesIO(patch_content_bytes)), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = error_stderr
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.apply_patch(self.patch_filename)
            self.assertIn(error_stderr.decode("utf-8"), str(ctx.exception))

    def test_rollback_success(self):
        tag = f"tag_{uuid.uuid4().hex[:8]}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            res = self.applier.rollback(tag)
            self.assertTrue(res)
            called_args = mock_run.call_args[0][0]
            self.assertIn("checkout", called_args)
            self.assertIn(tag, called_args)

    def test_rollback_failure(self):
        tag = f"tag_{uuid.uuid4().hex[:8]}"
        err_out = f"checkout_err_{uuid.uuid4().hex}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = err_out.encode("utf-8")
            with self.assertRaises(PatchApplierError):
                self.applier.rollback(tag)

    def test_verify_repository_state_clean(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = b""
            res = self.applier.verify_repository_state()
            self.assertTrue(res)

    def test_verify_repository_state_dirty_or_error(self):
        dirty_output = f"M file_{uuid.uuid4().hex}.py\n".encode("utf-8")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = dirty_output
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.verify_repository_state()
            self.assertIn(dirty_output.decode("utf-8"), str(ctx.exception))

    def test_safe_apply_success(self):
        patch_path = f"{uuid.uuid4().hex}.patch"
        backup_id = f"bk_{uuid.uuid4().hex}"
        with patch.object(self.applier, "create_recovery_point", return_value=True) as mock_cp, \
             patch.object(self.applier, "apply_patch", return_value=True) as mock_ap, \
             patch.object(self.applier, "verify_repository_state", return_value=True) as mock_vr:
            res = self.applier.safe_apply(patch_path, backup_id)
            self.assertTrue(res)
            mock_cp.assert_called_once_with(backup_id)
            mock_ap.assert_called_once_with(patch_path)
            mock_vr.assert_called_once()

    def test_safe_apply_rollback_on_exception(self):
        patch_path = f"{uuid.uuid4().hex}.patch"
        backup_id = f"bk_{uuid.uuid4().hex}"
        with patch.object(self.applier, "create_recovery_point", return_value=True) as mock_cp, \
             patch.object(self.applier, "apply_patch", side_effect=PatchApplierError(uuid.uuid4().hex)) as mock_ap, \
             patch.object(self.applier, "rollback", return_value=True) as mock_rb:
            with self.assertRaises(PatchApplierError):
                self.applier.safe_apply(patch_path, backup_id)
            mock_cp.assert_called_once_with(backup_id)
            mock_ap.assert_called_once_with(patch_path)
            mock_rb.assert_called_once_with(backup_id)

    def test_apply_patch_integration_helper(self):
        file_path = f"dir_{uuid.uuid4().hex}/file_{uuid.uuid4().hex}.py"
        content = f"print('{uuid.uuid4().hex}')"
        backup_id = f"backup_{uuid.uuid4().hex[:6]}"
        patch_data = {
            "file_path": file_path,
            "content": content,
            "backup_id": backup_id
        }
        with patch("subprocess.run") as mock_run, \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file, \
             patch("os.makedirs") as mock_dirs:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = b""
            res = apply_patch(self.repo_path, patch_data)
            self.assertTrue(res)
            mock_dirs.assert_called_once()
            mock_file.assert_called_once()
            self.assertGreaterEqual(mock_run.call_count, 3)