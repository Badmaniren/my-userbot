import unittest
from unittest.mock import patch, mock_open
import subprocess
import io
import os
import random
import uuid

from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplierInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.applier = PatchApplier(self.repo_path)

    def test_create_recovery_point_success(self):
        branch_name = f"branch_{uuid.uuid4().hex[:8]}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = self.applier.create_recovery_point(branch_name)
            self.assertTrue(result)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "branch", branch_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def test_create_recovery_point_failure(self):
        branch_name = f"branch_{uuid.uuid4().hex[:8]}"
        error_output = f"fatal: branch {branch_name} already exists {uuid.uuid4().hex}".encode("utf-8")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = error_output
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.create_recovery_point(branch_name)
            self.assertIn("Failed to create recovery point", str(ctx.exception))

    def test_apply_patch_from_file_success(self):
        patch_filename = f"{uuid.uuid4().hex}.patch"
        patch_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n".encode("utf-8")
        
        with patch("os.path.isabs", return_value=False), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", mock_open(read_data=patch_content)), \
             patch("subprocess.run") as mock_run:

            mock_run.return_value.returncode = 0
            result = self.applier.apply_patch(patch_filename)
            self.assertTrue(result)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "apply"],
                input=patch_content,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def test_apply_patch_not_found(self):
        missing_patch = f"{uuid.uuid4().hex}.patch"
        with patch("os.path.isabs", return_value=False), \
             patch("os.path.exists", return_value=False):
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.apply_patch(missing_patch)
            self.assertIn("Patch source not found", str(ctx.exception))

    def test_apply_patch_failure(self):
        patch_filename = f"{uuid.uuid4().hex}.patch"
        patch_content = b"corrupted patch data"
        git_error_msg = f"error: patch failed: {uuid.uuid4().hex}".encode("utf-8")
        
        with patch("os.path.isabs", return_value=False), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", mock_open(read_data=patch_content)), \
             patch("subprocess.run") as mock_run:

            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = git_error_msg
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.apply_patch(patch_filename)
            self.assertIn("Failed to apply patch", str(ctx.exception))

    def test_rollback_success(self):
        backup_tag = f"tag_{uuid.uuid4().hex[:8]}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = self.applier.rollback(backup_tag)
            self.assertTrue(result)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "checkout", "-f", backup_tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def test_rollback_failure(self):
        backup_tag = f"tag_{uuid.uuid4().hex[:8]}"
        error_output = f"error: pathspec '{backup_tag}' did not match any file(s)".encode("utf-8")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = error_output
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.rollback(backup_tag)
            self.assertIn("Failed to rollback", str(ctx.exception))

    def test_verify_repository_state_success(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = b""
            result = self.applier.verify_repository_state()
            self.assertTrue(result)

    def test_verify_repository_state_failure_dirty(self):
        dirty_output = f" M {uuid.uuid4().hex}.py\n".encode("utf-8")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = dirty_output
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.verify_repository_state()
            self.assertIn("Repository verification failed", str(ctx.exception))

    def test_safe_apply_success(self):
        patch_file = f"{uuid.uuid4().hex}.patch"
        backup_tag = f"backup_{uuid.uuid4().hex[:6]}"

        with patch.object(self.applier, "create_recovery_point", return_value=True) as mock_cp, \
             patch.object(self.applier, "apply_patch", return_value=True) as mock_ap, \
             patch.object(self.applier, "verify_repository_state", return_value=True) as mock_vr:

            result = self.applier.safe_apply(patch_file, backup_tag)
            self.assertTrue(result)
            mock_cp.assert_called_once_with(backup_tag)
            mock_ap.assert_called_once_with(patch_file)
            mock_vr.assert_called_once()

    def test_safe_apply_failure_with_rollback(self):
        patch_file = f"{uuid.uuid4().hex}.patch"
        backup_tag = f"backup_{uuid.uuid4().hex[:6]}"

        with patch.object(self.applier, "verify_repository_state", return_value=True) as mock_vr, \
             patch.object(self.applier, "create_recovery_point", return_value=True) as mock_cp, \
             patch.object(self.applier, "apply_patch", side_effect=PatchApplierError("Apply error")) as mock_ap, \
             patch.object(self.applier, "rollback", return_value=True) as mock_rb:

            with self.assertRaises(PatchApplierError):
                self.applier.safe_apply(patch_file, backup_tag)

            mock_vr.assert_called_once()
            mock_cp.assert_called_once_with(backup_tag)
            mock_ap.assert_called_once_with(patch_file)
            mock_rb.assert_called_once_with(backup_tag)

    def test_apply_patch_integration_function(self):
        file_path = f"modules/{uuid.uuid4().hex}.py"
        content = f"# content {uuid.uuid4().hex}"
        backup_id = f"bck_{uuid.uuid4().hex[:6]}"
        patch_data = {
            "file_path": file_path,
            "content": content,
            "backup_id": backup_id
        }

        with patch("skills.patch_applier.PatchApplier.create_recovery_point") as mock_cp, \
             patch("os.makedirs") as mock_mkdirs, \
             patch("builtins.open", mock_open()) as mock_file, \
             patch("subprocess.run") as mock_run, \
             patch("skills.patch_applier.PatchApplier.verify_repository_state", return_value=True) as mock_vs:

            result = apply_patch(self.repo_path, patch_data)
            self.assertTrue(result)
            mock_cp.assert_called_once_with(backup_id)
            mock_mkdirs.assert_called_once()
            mock_file.assert_called_once()
            self.assertEqual(mock_run.call_count, 2)
            mock_vs.assert_called_once()