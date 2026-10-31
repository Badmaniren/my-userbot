import unittest
from unittest.mock import patch
import subprocess
import os
import io
import uuid
import random

from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplierInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        self.patch_source = f"{uuid.uuid4().hex}.patch"
        self.file_path = f"src/{uuid.uuid4().hex}.py"
        self.content = f"print('{uuid.uuid4().hex}')\n"
        self.error_msg = f"git_error_{uuid.uuid4().hex}"

    def test_create_recovery_point_success(self):
        applier = PatchApplier(self.repo_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            res = applier.create_recovery_point(self.backup_tag)
            self.assertTrue(res)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "branch", self.backup_tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def test_create_recovery_point_failure(self):
        applier = PatchApplier(self.repo_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 128
            mock_run.return_value.stderr = self.error_msg.encode("utf-8")
            with self.assertRaises(PatchApplierError) as ctx:
                applier.create_recovery_point(self.backup_tag)
            self.assertIn(self.error_msg, str(ctx.exception))

    def test_apply_patch_file_success(self):
        applier = PatchApplier(self.repo_path)
        random_bytes = uuid.uuid4().bytes
        with patch("os.path.isabs", return_value=True), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", return_value=io.BytesIO(random_bytes)), \
             patch("subprocess.run") as mock_run:
            
            mock_run.return_value.returncode = 0
            res = applier.apply_patch(self.patch_source)
            self.assertTrue(res)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "apply"],
                input=random_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def test_apply_patch_not_found(self):
        applier = PatchApplier(self.repo_path)
        with patch("os.path.isabs", return_value=False), \
             patch("os.path.join", return_value=self.patch_source), \
             patch("os.path.exists", return_value=False):
            with self.assertRaises(PatchApplierError) as ctx:
                applier.apply_patch(self.patch_source)
            self.assertIn(self.patch_source, str(ctx.exception))

    def test_apply_patch_execution_failure(self):
        applier = PatchApplier(self.repo_path)
        random_bytes = uuid.uuid4().bytes
        with patch("os.path.isabs", return_value=True), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", return_value=io.BytesIO(random_bytes)), \
             patch("subprocess.run") as mock_run:
            
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = self.error_msg.encode("utf-8")
            with self.assertRaises(PatchApplierError) as ctx:
                applier.apply_patch(self.patch_source)
            self.assertIn(self.error_msg, str(ctx.exception))

    def test_rollback_success(self):
        applier = PatchApplier(self.repo_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            res = applier.rollback(self.backup_tag)
            self.assertTrue(res)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "checkout", self.backup_tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def test_rollback_failure(self):
        applier = PatchApplier(self.repo_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = self.error_msg.encode("utf-8")
            with self.assertRaises(PatchApplierError) as ctx:
                applier.rollback(self.backup_tag)
            self.assertIn(self.error_msg, str(ctx.exception))

    def test_verify_repository_state_success(self):
        applier = PatchApplier(self.repo_path)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = b""
            res = applier.verify_repository_state()
            self.assertTrue(res)

    def test_verify_repository_state_failure(self):
        applier = PatchApplier(self.repo_path)
        dirty_output = f" M {uuid.uuid4().hex}.py\n".encode("utf-8")
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = dirty_output
            with self.assertRaises(PatchApplierError) as ctx:
                applier.verify_repository_state()
            self.assertIn(dirty_output.decode("utf-8", errors="ignore"), str(ctx.exception))

    def test_safe_apply_success(self):
        applier = PatchApplier(self.repo_path)
        with patch.object(applier, "create_recovery_point") as mock_create, \
             patch.object(applier, "apply_patch") as mock_apply, \
             patch.object(applier, "verify_repository_state") as mock_verify:
            
            res = applier.safe_apply(self.patch_source, self.backup_tag)
            self.assertTrue(res)
            mock_create.assert_called_once_with(self.backup_tag)
            mock_apply.assert_called_once_with(self.patch_source)
            mock_verify.assert_called_once()

    def test_safe_apply_failure_with_successful_rollback(self):
        applier = PatchApplier(self.repo_path)
        with patch.object(applier, "create_recovery_point") as mock_create, \
             patch.object(applier, "apply_patch", side_effect=PatchApplierError(self.error_msg)) as mock_apply, \
             patch.object(applier, "rollback") as mock_rollback:
            
            with self.assertRaises(PatchApplierError) as ctx:
                applier.safe_apply(self.patch_source, self.backup_tag)
            self.assertIn(self.error_msg, str(ctx.exception))
            mock_create.assert_called_once_with(self.backup_tag)
            mock_apply.assert_called_once_with(self.patch_source)
            mock_rollback.assert_called_once_with(self.backup_tag)

    def test_safe_apply_failure_with_failed_rollback(self):
        applier = PatchApplier(self.repo_path)
        rollback_error = f"rollback_err_{uuid.uuid4().hex}"
        with patch.object(applier, "create_recovery_point") as mock_create, \
             patch.object(applier, "apply_patch", side_effect=PatchApplierError(self.error_msg)) as mock_apply, \
             patch.object(applier, "rollback", side_effect=PatchApplierError(rollback_error)) as mock_rollback:
            
            with self.assertRaises(PatchApplierError) as ctx:
                applier.safe_apply(self.patch_source, self.backup_tag)
            self.assertIn(rollback_error, str(ctx.exception))
            mock_rollback.assert_called_once_with(self.backup_tag)

    def test_apply_patch_integration_helper_success(self):
        patch_data = {
            "file_path": self.file_path,
            "content": self.content,
            "backup_id": self.backup_tag
        }
        with patch("skills.patch_applier.PatchApplier.create_recovery_point") as mock_create, \
             patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file, \
             patch("subprocess.run") as mock_run, \
             patch("skills.patch_applier.PatchApplier.verify_repository_state") as mock_verify:
            
            res = apply_patch(self.repo_path, patch_data)
            self.assertTrue(res)
            mock_create.assert_called_once_with(self.backup_tag)
            mock_makedirs.assert_called_once()
            mock_file.assert_called_once()
            mock_file().write.assert_called_once_with(self.content)
            self.assertEqual(mock_run.call_count, 2)
            mock_verify.assert_called_once()