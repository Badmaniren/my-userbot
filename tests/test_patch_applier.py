import unittest
from unittest.mock import patch, MagicMock
import os
import io
import subprocess
import uuid
import random
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplier(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.patch_applier = PatchApplier(self.repo_path)

    def test_create_recovery_point_success(self):
        tag = f"backup_{uuid.uuid4().hex[:8]}"
        mock_result = MagicMock(returncode=0)
        
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = self.patch_applier.create_recovery_point(tag)
            self.assertTrue(result)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "branch", tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def test_create_recovery_point_failure(self):
        tag = f"backup_{uuid.uuid4().hex[:8]}"
        err_output = f"fatal: branch {tag} already exists {uuid.uuid4().hex}".encode("utf-8")
        mock_result = MagicMock(returncode=128, stderr=err_output)
        
        with patch("subprocess.run", return_value=mock_result):
            with self.assertRaises(PatchApplierError) as ctx:
                self.patch_applier.create_recovery_point(tag)
            self.assertIn("Failed to create recovery point", str(ctx.exception))

    def test_apply_patch_from_absolute_file(self):
        patch_file = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.patch"
        file_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n".encode("utf-8")
        mock_result = MagicMock(returncode=0)

        with patch("os.path.isabs", return_value=True), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", return_value=io.BytesIO(file_content)), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            
            res = self.patch_applier.apply_patch(patch_file)
            self.assertTrue(res)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "apply"],
                input=file_content,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def test_apply_patch_failure(self):
        patch_file = f"{uuid.uuid4().hex}.patch"
        err_msg = f"error: patch failed: {uuid.uuid4().hex}".encode("utf-8")
        mock_result = MagicMock(returncode=1, stderr=err_msg)

        with patch("os.path.isabs", return_value=False), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", return_value=io.BytesIO(b"dummy")), \
             patch("subprocess.run", return_value=mock_result):

            with self.assertRaises(PatchApplierError) as ctx:
                self.patch_applier.apply_patch(patch_file)
            self.assertIn("Failed to apply patch", str(ctx.exception))

    def test_rollback_success(self):
        tag = f"tag_{uuid.uuid4().hex[:6]}"
        mock_result = MagicMock(returncode=0)

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            res = self.patch_applier.rollback(tag)
            self.assertTrue(res)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "checkout", tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def test_rollback_failure(self):
        tag = f"tag_{uuid.uuid4().hex[:6]}"
        mock_result = MagicMock(returncode=1, stderr=b"pathspec did not match")

        with patch("subprocess.run", return_value=mock_result):
            with self.assertRaises(PatchApplierError) as ctx:
                self.patch_applier.rollback(tag)
            self.assertIn("Failed to rollback", str(ctx.exception))

    def test_verify_repository_state_success(self):
        mock_result = MagicMock(returncode=0)

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            res = self.patch_applier.verify_repository_state()
            self.assertTrue(res)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "status", "--porcelain"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def test_verify_repository_state_failure(self):
        output_msg = f"untracked file {uuid.uuid4().hex}".encode("utf-8")
        mock_result = MagicMock(returncode=1, stdout=output_msg)

        with patch("subprocess.run", return_value=mock_result):
            with self.assertRaises(PatchApplierError) as ctx:
                self.patch_applier.verify_repository_state()
            self.assertIn("Repository verification failed", str(ctx.exception))

    def test_safe_apply_success(self):
        patch_path = f"{uuid.uuid4().hex}.patch"
        backup_tag = f"bkp_{uuid.uuid4().hex[:8]}"

        with patch.object(self.patch_applier, "create_recovery_point") as mock_create, \
             patch.object(self.patch_applier, "apply_patch") as mock_apply, \
             patch.object(self.patch_applier, "verify_repository_state") as mock_verify:

            res = self.patch_applier.safe_apply(patch_path, backup_tag)
            self.assertTrue(res)
            mock_create.assert_called_once_with(backup_tag)
            mock_apply.assert_called_once_with(patch_path)
            mock_verify.assert_called_once()

    def test_safe_apply_rollback_on_error(self):
        patch_path = f"{uuid.uuid4().hex}.patch"
        backup_tag = f"bkp_{uuid.uuid4().hex[:8]}"

        with patch.object(self.patch_applier, "create_recovery_point"), \
             patch.object(self.patch_applier, "apply_patch", side_effect=Exception(uuid.uuid4().hex)), \
             patch.object(self.patch_applier, "rollback") as mock_rollback:

            with self.assertRaises(Exception):
                self.patch_applier.safe_apply(patch_path, backup_tag)
            mock_rollback.assert_called_once_with(backup_tag)

    def test_integration_apply_patch_func(self):
        file_path_val = f"src/{uuid.uuid4().hex}.py"
        content_val = f"print('{uuid.uuid4().hex}')"
        backup_id_val = f"backup_{uuid.uuid4().hex[:5]}"
        patch_data = {
            "file_path": file_path_val,
            "content": content_val,
            "backup_id": backup_id_val
        }

        mock_file = MagicMock()
        with patch("builtins.open", return_value=mock_file) as mock_open, \
             patch("subprocess.run") as mock_run, \
             patch.object(PatchApplier, "create_recovery_point") as mock_create_bkp, \
             patch.object(PatchApplier, "verify_repository_state") as mock_verify_state:

            res = apply_patch(self.repo_path, patch_data)
            self.assertTrue(res)
            mock_open.assert_called_once_with(os.path.join(self.repo_path, file_path_val), "w", encoding="utf-8")
            mock_file.__enter__().write.assert_called_once_with(content_val)
            mock_create_bkp.assert_called_once_with(backup_id_val)
            self.assertEqual(mock_run.call_count, 2)
            mock_verify_state.assert_called_once()


if __name__ == "__main__":
    unittest.main()