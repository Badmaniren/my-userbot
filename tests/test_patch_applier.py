import unittest
from unittest.mock import patch
import io
import uuid
import random
import subprocess
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplier(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.applier = PatchApplier(self.repo_path)

    def test_create_recovery_point_success(self):
        backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = self.applier.create_recovery_point(backup_tag)
            self.assertTrue(result)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "branch", backup_tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def test_create_recovery_point_failure(self):
        backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        err_output = f"fatal: branch {backup_tag} already exists".encode("utf-8")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 128
            mock_run.return_value.stderr = err_output
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.create_recovery_point(backup_tag)
            self.assertIn("Failed to create recovery point", str(ctx.exception))

    def test_apply_patch_file_success(self):
        patch_file = f"patch_{uuid.uuid4().hex[:6]}.diff"
        patch_content_bytes = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n".encode("utf-8")

        with patch("os.path.isabs", return_value=True), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", return_value=io.BytesIO(patch_content_bytes)), \
             patch("subprocess.run") as mock_run:
            
            mock_run.return_value.returncode = 0
            result = self.applier.apply_patch(patch_file)
            self.assertTrue(result)
            mock_run.assert_called_once()

    def test_apply_patch_fallback_source(self):
        patch_source = f"{uuid.uuid4().hex}.patch"
        patch_content_bytes = f"content_{uuid.uuid4().hex}".encode("utf-8")

        with patch("os.path.isabs", return_value=False), \
             patch("os.path.exists", side_effect=[False, False, True, True]), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", return_value=io.BytesIO(patch_content_bytes)), \
             patch("subprocess.run") as mock_run:
            
            mock_run.return_value.returncode = 0
            result = self.applier.apply_patch(patch_source)
            self.assertTrue(result)

    def test_apply_patch_failure(self):
        patch_file = f"corrupt_{uuid.uuid4().hex}.diff"
        err_output = f"error: patch failed: {uuid.uuid4().hex}".encode("utf-8")

        with patch("os.path.isabs", return_value=True), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", return_value=io.BytesIO(b"data")), \
             patch("subprocess.run") as mock_run:
            
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = err_output
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.apply_patch(patch_file)
            self.assertIn("Failed to apply patch", str(ctx.exception))

    def test_rollback_success(self):
        backup_tag = f"tag_{uuid.uuid4().hex[:8]}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = self.applier.rollback(backup_tag)
            self.assertTrue(result)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "checkout", backup_tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def test_rollback_failure(self):
        backup_tag = f"tag_{uuid.uuid4().hex[:8]}"
        err_output = f"error: pathspec '{backup_tag}' did not match any file(s)".encode("utf-8")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = err_output
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.rollback(backup_tag)
            self.assertIn("Failed to rollback", str(ctx.exception))

    def test_verify_repository_state_success(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = self.applier.verify_repository_state()
            self.assertTrue(result)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "status", "--porcelain"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def test_verify_repository_state_failure(self):
        out_msg = f"untracked_{uuid.uuid4().hex}.py".encode("utf-8")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 128
            mock_run.return_value.stdout = out_msg
            with self.assertRaises(PatchApplierError) as ctx:
                self.applier.verify_repository_state()
            self.assertIn("Repository verification failed", str(ctx.exception))

    def test_safe_apply_success(self):
        patch_path = f"{uuid.uuid4().hex}.diff"
        backup_tag = f"safe_{uuid.uuid4().hex[:6]}"

        with patch.object(self.applier, "create_recovery_point", return_value=True) as mock_create, \
             patch.object(self.applier, "apply_patch", return_value=True) as mock_apply, \
             patch.object(self.applier, "verify_repository_state", return_value=True) as mock_verify:

            result = self.applier.safe_apply(patch_path, backup_tag)
            self.assertTrue(result)
            mock_create.assert_called_once_with(backup_tag)
            mock_apply.assert_called_once_with(patch_path)
            mock_verify.assert_called_once()

    def test_safe_apply_triggers_rollback_on_failure(self):
        patch_path = f"{uuid.uuid4().hex}.diff"
        backup_tag = f"safe_{uuid.uuid4().hex[:6]}"

        with patch.object(self.applier, "create_recovery_point", return_value=True) as mock_create, \
             patch.object(self.applier, "apply_patch", side_effect=Exception("Crash")) as mock_apply, \
             patch.object(self.applier, "rollback", return_value=True) as mock_rollback:

            with self.assertRaises(Exception):
                self.applier.safe_apply(patch_path, backup_tag)

            mock_create.assert_called_once_with(backup_tag)
            mock_apply.assert_called_once_with(patch_path)
            mock_rollback.assert_called_once_with(backup_tag)

    def test_apply_patch_integration_function(self):
        file_path = f"src/{uuid.uuid4().hex}.py"
        content = f"# {uuid.uuid4().hex}\nprint('{uuid.uuid4().hex}')"
        backup_id = f"rev_{uuid.uuid4().hex[:6]}"
        patch_data = {
            "file_path": file_path,
            "content": content,
            "backup_id": backup_id
        }

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file, \
             patch("subprocess.run") as mock_run, \
             patch("skills.patch_applier.PatchApplier") as mock_applier_cls:

            mock_applier_instance = mock_applier_cls.return_value
            mock_applier_instance.verify_repository_state.return_value = True

            result = apply_patch(self.repo_path, patch_data)
            self.assertTrue(result)
            mock_file.assert_called_once()
            mock_applier_instance.create_recovery_point.assert_called_once_with(backup_id)
            mock_applier_instance.verify_repository_state.assert_called_once()
            self.assertEqual(mock_run.call_count, 2)