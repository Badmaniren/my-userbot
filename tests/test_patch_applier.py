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
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.backup_tag = f"backup_{uuid.uuid4().hex}"
        self.patch_file_name = f"patch_{uuid.uuid4().hex}.diff"
        self.random_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n+{uuid.uuid4().hex}".encode("utf-8")

    @patch("subprocess.run")
    def test_create_recovery_point_success(self, mock_run):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        applier = PatchApplier(self.repo_path)
        result = applier.create_recovery_point(self.backup_tag)

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "branch", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_create_recovery_point_failure(self, mock_run):
        mock_process = MagicMock()
        mock_process.returncode = random.randint(1, 255)
        err_msg_str = f"error_{uuid.uuid4().hex}"
        mock_process.stderr = err_msg_str.encode("utf-8")
        mock_run.return_value = mock_process

        applier = PatchApplier(self.repo_path)
        with self.assertRaises(PatchApplierError) as ctx:
            applier.create_recovery_point(self.backup_tag)

        self.assertIn(err_msg_str, str(ctx.exception))

    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("subprocess.run")
    def test_apply_patch_from_file(self, mock_run, mock_isfile, mock_exists):
        mock_exists.return_value = True
        mock_isfile.return_value = True

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        applier = PatchApplier(self.repo_path)

        with patch("builtins.open", unittest.mock.mock_open(read_data=self.random_content)):
            result = applier.apply_patch(self.patch_file_name)

        self.assertTrue(result)
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertEqual(kwargs.get("input"), self.random_content)

    @patch("os.path.exists")
    @patch("os.path.isfile")
    @patch("subprocess.run")
    def test_apply_patch_failure(self, mock_run, mock_isfile, mock_exists):
        mock_exists.return_value = True
        mock_isfile.return_value = True

        mock_process = MagicMock()
        mock_process.returncode = random.randint(1, 255)
        err_out = f"patch_failed_{uuid.uuid4().hex}".encode("utf-8")
        mock_process.stderr = err_out
        mock_run.return_value = mock_process

        applier = PatchApplier(self.repo_path)

        with patch("builtins.open", unittest.mock.mock_open(read_data=self.random_content)):
            with self.assertRaises(PatchApplierError) as ctx:
                applier.apply_patch(self.patch_file_name)

        self.assertIn(err_out.decode("utf-8"), str(ctx.exception))

    @patch("os.path.exists")
    @patch("os.path.isfile")
    def test_apply_patch_invalid_source(self, mock_isfile, mock_exists):
        mock_exists.return_value = False
        mock_isfile.return_value = False

        applier = PatchApplier(self.repo_path)
        with patch("builtins.open", side_effect=FileNotFoundError):
            with self.assertRaises(PatchApplierError) as ctx:
                applier.apply_patch(self.patch_file_name)

        self.assertIn("Patch source not found", str(ctx.exception))

    @patch("subprocess.run")
    def test_rollback_success(self, mock_run):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        applier = PatchApplier(self.repo_path)
        result = applier.rollback(self.backup_tag)

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "checkout", self.backup_tag],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_rollback_failure(self, mock_run):
        mock_process = MagicMock()
        mock_process.returncode = random.randint(1, 255)
        err_msg = f"checkout_err_{uuid.uuid4().hex}"
        mock_process.stderr = err_msg.encode("utf-8")
        mock_run.return_value = mock_process

        applier = PatchApplier(self.repo_path)
        with self.assertRaises(PatchApplierError) as ctx:
            applier.rollback(self.backup_tag)

        self.assertIn(err_msg, str(ctx.exception))

    @patch("subprocess.run")
    def test_verify_repository_state_success(self, mock_run):
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        applier = PatchApplier(self.repo_path)
        result = applier.verify_repository_state()

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["git", "-C", self.repo_path, "status", "--porcelain"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

    @patch("subprocess.run")
    def test_verify_repository_state_failure(self, mock_run):
        mock_process = MagicMock()
        mock_process.returncode = random.randint(1, 255)
        stdout_err = f"dirty_repo_{uuid.uuid4().hex}"
        mock_process.stdout = stdout_err.encode("utf-8")
        mock_run.return_value = mock_process

        applier = PatchApplier(self.repo_path)
        with self.assertRaises(PatchApplierError) as ctx:
            applier.verify_repository_state()

        self.assertIn(stdout_err, str(ctx.exception))

    @patch.object(PatchApplier, "verify_repository_state")
    @patch.object(PatchApplier, "apply_patch")
    @patch.object(PatchApplier, "create_recovery_point")
    def test_safe_apply_success(self, mock_create, mock_apply, mock_verify):
        mock_create.return_value = True
        mock_apply.return_value = True
        mock_verify.return_value = True

        applier = PatchApplier(self.repo_path)
        result = applier.safe_apply(self.patch_file_name, self.backup_tag)

        self.assertTrue(result)
        mock_create.assert_called_once_with(self.backup_tag)
        mock_apply.assert_called_once_with(self.patch_file_name)
        mock_verify.assert_called_once()

    @patch.object(PatchApplier, "rollback")
    @patch.object(PatchApplier, "apply_patch")
    @patch.object(PatchApplier, "create_recovery_point")
    def test_safe_apply_failure_triggers_rollback(self, mock_create, mock_apply, mock_rollback):
        mock_create.return_value = True
        mock_apply.side_effect = PatchApplierError(f"fail_{uuid.uuid4().hex}")
        mock_rollback.return_value = True

        applier = PatchApplier(self.repo_path)
        with self.assertRaises(PatchApplierError):
            applier.safe_apply(self.patch_file_name, self.backup_tag)

        mock_create.assert_called_once_with(self.backup_tag)
        mock_apply.assert_called_once_with(self.patch_file_name)
        mock_rollback.assert_called_once_with(self.backup_tag)

    @patch("subprocess.run")
    def test_apply_patch_integration_function(self, mock_run):
        file_path_rand = f"module_{uuid.uuid4().hex}.py"
        content_rand = f"def {uuid.uuid4().hex}(): pass"
        backup_id_rand = f"bk_{uuid.uuid4().hex}"

        patch_data = {
            "file_path": file_path_rand,
            "content": content_rand,
            "backup_id": backup_id_rand
        }

        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            result = apply_patch(self.repo_path, patch_data)

        self.assertTrue(result)
        mock_file.assert_called_once_with(os.path.join(self.repo_path, file_path_rand), "w", encoding="utf-8")
        mock_file().write.assert_called_once_with(content_rand)
        self.assertGreaterEqual(mock_run.call_count, 3)