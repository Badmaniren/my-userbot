import os
import unittest
import subprocess
import uuid
import random
import io
from unittest.mock import patch, MagicMock

from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplier(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.applier = PatchApplier(self.repo_path)

    @patch("subprocess.run")
    def test_create_recovery_point_success(self, mock_run):
        backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        res = self.applier.create_recovery_point(backup_tag)

        self.assertTrue(res)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "branch", "-f", backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_create_recovery_point_failure(self, mock_run):
        backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        err_text = f"error_{uuid.uuid4().hex}"
        mock_result = MagicMock()
        mock_result.returncode = 128
        mock_result.stderr = err_text.encode("utf-8")
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.create_recovery_point(backup_tag)

        self.assertIn(err_text, str(ctx.exception))

    @patch("subprocess.run")
    @patch("builtins.open")
    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_apply_patch_success(self, mock_isfile, mock_exists, mock_open, mock_run):
        patch_file = f"{uuid.uuid4().hex}.patch"
        file_content = f"content_{uuid.uuid4().hex}".encode("utf-8")

        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_open.return_value = io.BytesIO(file_content)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        res = self.applier.apply_patch(patch_file)

        self.assertTrue(res)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "apply"],
            input=file_content,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    @patch("builtins.open")
    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_apply_patch_failure(self, mock_isfile, mock_exists, mock_open, mock_run):
        patch_file = f"{uuid.uuid4().hex}.patch"
        err_text = f"reject_{uuid.uuid4().hex}"
        file_content = f"content_{uuid.uuid4().hex}".encode("utf-8")

        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_open.return_value = io.BytesIO(file_content)

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = err_text.encode("utf-8")
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.apply_patch(patch_file)

        self.assertIn(err_text, str(ctx.exception))

    @patch("subprocess.run")
    def test_rollback_success(self, mock_run):
        backup_tag = f"tag_{uuid.uuid4().hex[:8]}"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        res = self.applier.rollback(backup_tag)

        self.assertTrue(res)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "checkout", backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_rollback_failure(self, mock_run):
        backup_tag = f"tag_{uuid.uuid4().hex[:8]}"
        err_text = f"checkout_err_{uuid.uuid4().hex}"
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = err_text.encode("utf-8")
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.rollback(backup_tag)

        self.assertIn(err_text, str(ctx.exception))

    @patch("subprocess.run")
    def test_verify_repository_state_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        res = self.applier.verify_repository_state()

        self.assertTrue(res)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "status", "--porcelain"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_verify_repository_state_failure(self, mock_run):
        output_text = f"dirty_{uuid.uuid4().hex}"
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = output_text.encode("utf-8")
        mock_run.return_value = mock_result

        with self.assertRaises(PatchApplierError) as ctx:
            self.applier.verify_repository_state()

        self.assertIn(output_text, str(ctx.exception))

    @patch.object(PatchApplier, "verify_repository_state")
    @patch.object(PatchApplier, "apply_patch")
    @patch.object(PatchApplier, "create_recovery_point")
    def test_safe_apply_success(self, mock_create, mock_apply, mock_verify):
        patch_path = f"{uuid.uuid4().hex}.patch"
        backup_tag = f"{uuid.uuid4().hex}"

        res = self.applier.safe_apply(patch_path, backup_tag)

        self.assertTrue(res)
        mock_create.assert_called_once_with(backup_tag)
        mock_apply.assert_called_once_with(patch_path)
        mock_verify.assert_called_once()

    @patch.object(PatchApplier, "rollback")
    @patch.object(PatchApplier, "apply_patch")
    @patch.object(PatchApplier, "create_recovery_point")
    def test_safe_apply_failure_triggers_rollback(self, mock_create, mock_apply, mock_rollback):
        patch_path = f"{uuid.uuid4().hex}.patch"
        backup_tag = f"{uuid.uuid4().hex}"
        mock_apply.side_effect = PatchApplierError(f"fail_{uuid.uuid4().hex}")

        with self.assertRaises(PatchApplierError):
            self.applier.safe_apply(patch_path, backup_tag)

        mock_create.assert_called_once_with(backup_tag)
        mock_rollback.assert_called_once_with(backup_tag)

    @patch("subprocess.run")
    @patch("builtins.open")
    def test_apply_patch_integration_function(self, mock_open, mock_run):
        file_path = f"src/{uuid.uuid4().hex}.py"
        content = f"print('{uuid.uuid4().hex}')"
        backup_id = f"bk_{uuid.uuid4().hex[:6]}"
        patch_data = {
            "file_path": file_path,
            "content": content,
            "backup_id": backup_id
        }

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        res = apply_patch(self.repo_path, patch_data)

        self.assertTrue(res)
        mock_file.write.assert_called_once_with(content)
        expected_calls_count = 5
        self.assertEqual(mock_run.call_count, expected_calls_count)


if __name__ == "__main__":
    unittest.main()