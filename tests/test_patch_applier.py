import unittest
from unittest.mock import patch, MagicMock
import os
import subprocess
import io
import uuid
import random
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplierInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        self.patch_file = f"patch_{uuid.uuid4().hex[:8]}.diff"
        self.random_error_msg = f"git_error_{uuid.uuid4().hex}"

    def test_create_recovery_point_success(self):
        applier = PatchApplier(self.repo_path)
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = applier.create_recovery_point(self.backup_tag)
            self.assertTrue(result)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "branch", self.backup_tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def test_create_recovery_point_failure(self):
        applier = PatchApplier(self.repo_path)
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = self.random_error_msg.encode("utf-8")

        with patch("subprocess.run", return_value=mock_result):
            with self.assertRaises(PatchApplierError) as ctx:
                applier.create_recovery_point(self.backup_tag)
            self.assertIn(self.random_error_msg, str(ctx.exception))

    def test_apply_patch_file_success(self):
        applier = PatchApplier(self.repo_path)
        mock_result = MagicMock()
        mock_result.returncode = 0
        patch_content = b"random_patch_content_" + uuid.uuid4().hex.encode("utf-8")

        with patch("os.path.isabs", return_value=True), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", return_value=io.BytesIO(patch_content)), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            
            result = applier.apply_patch(self.patch_file)
            self.assertTrue(result)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "apply"],
                input=patch_content,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

    def test_apply_patch_failure(self):
        applier = PatchApplier(self.repo_path)
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = self.random_error_msg.encode("utf-8")
        patch_content = b"bad_patch_" + uuid.uuid4().hex.encode("utf-8")

        with patch("os.path.isabs", return_value=True), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", return_value=io.BytesIO(patch_content)), \
             patch("subprocess.run", return_value=mock_result):

            with self.assertRaises(PatchApplierError) as ctx:
                applier.apply_patch(self.patch_file)
            self.assertIn(self.random_error_msg, str(ctx.exception))

    def test_rollback_success(self):
        applier = PatchApplier(self.repo_path)
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = applier.rollback(self.backup_tag)
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

    def test_rollback_failure(self):
        applier = PatchApplier(self.repo_path)
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = self.random_error_msg.encode("utf-8")

        with patch("subprocess.run", return_value=mock_result):
            with self.assertRaises(PatchApplierError) as ctx:
                applier.rollback(self.backup_tag)
            self.assertIn(self.random_error_msg, str(ctx.exception))

    def test_verify_repository_state_success(self):
        applier = PatchApplier(self.repo_path)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = b""

        with patch("subprocess.run", return_value=mock_result):
            result = applier.verify_repository_state()
            self.assertTrue(result)

    def test_verify_repository_state_failure(self):
        applier = PatchApplier(self.repo_path)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = self.random_error_msg.encode("utf-8")

        with patch("subprocess.run", return_value=mock_result):
            with self.assertRaises(PatchApplierError) as ctx:
                applier.verify_repository_state()
            self.assertIn(self.random_error_msg, str(ctx.exception))

    def test_safe_apply_success(self):
        applier = PatchApplier(self.repo_path)

        with patch.object(applier, "create_recovery_point", return_value=True) as mock_create, \
             patch.object(applier, "apply_patch", return_value=True) as mock_apply, \
             patch.object(applier, "verify_repository_state", return_value=True) as mock_verify, \
             patch.object(applier, "rollback") as mock_rollback:

            result = applier.safe_apply(self.patch_file, self.backup_tag)
            self.assertTrue(result)
            mock_create.assert_called_once_with(self.backup_tag)
            mock_apply.assert_called_once_with(self.patch_file)
            mock_verify.assert_called_once()
            mock_rollback.assert_not_called()

    def test_safe_apply_failure_triggers_rollback(self):
        applier = PatchApplier(self.repo_path)

        with patch.object(applier, "create_recovery_point", return_value=True) as mock_create, \
             patch.object(applier, "apply_patch", side_effect=PatchApplierError(self.random_error_msg)) as mock_apply, \
             patch.object(applier, "rollback", return_value=True) as mock_rollback:

            with self.assertRaises(PatchApplierError):
                applier.safe_apply(self.patch_file, self.backup_tag)

            mock_create.assert_called_once_with(self.backup_tag)
            mock_apply.assert_called_once_with(self.patch_file)
            mock_rollback.assert_called_once_with(self.backup_tag)

    def test_apply_patch_integration_helper(self):
        file_path = f"src/{uuid.uuid4().hex}.py"
        content = f"print('{uuid.uuid4().hex}')"
        backup_id = f"bak_{uuid.uuid4().hex[:6]}"
        patch_data = {
            "file_path": file_path,
            "content": content,
            "backup_id": backup_id
        }

        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file_open, \
             patch("skills.patch_applier.PatchApplier") as mock_applier_cls, \
             patch("subprocess.run") as mock_subprocess_run:

            mock_applier_instance = mock_applier_cls.return_value
            mock_applier_instance.verify_repository_state.return_value = True

            result = apply_patch(self.repo_path, patch_data)
            self.assertTrue(result)
            mock_makedirs.assert_called_once()
            mock_file_open.assert_called_once()
            mock_applier_instance.create_recovery_point.assert_called_once_with(backup_id)
            mock_applier_instance.verify_repository_state.assert_called_once()
            self.assertEqual(mock_subprocess_run.call_count, 2)