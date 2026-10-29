import os
import random
import subprocess
import unittest
import uuid
from unittest.mock import MagicMock, mock_open, patch

from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplier(unittest.TestCase):

    def test_create_recovery_point_success(self):
        repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        backup_tag = f"branch_{uuid.uuid4().hex}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")
            applier = PatchApplier(repo_path)
            result = applier.create_recovery_point(backup_tag)
            self.assertTrue(result)
            mock_run.assert_called_once_with(
                ["git", "-C", repo_path, "branch", backup_tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

    def test_create_recovery_point_failure(self):
        repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        backup_tag = f"branch_{uuid.uuid4().hex}"
        err_msg = f"git_error_{uuid.uuid4().hex}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stderr=err_msg.encode("utf-8")
            )
            applier = PatchApplier(repo_path)
            with self.assertRaises(PatchApplierError) as ctx:
                applier.create_recovery_point(backup_tag)
            self.assertIn(err_msg, str(ctx.exception))

    def test_apply_patch_file_exists_success(self):
        repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        patch_file = f"patch_{uuid.uuid4().hex}.patch"
        patch_content = f"diff_{uuid.uuid4().hex}".encode("utf-8")
        with patch("os.path.isabs", return_value=False), patch(
            "os.path.exists", return_value=True
        ), patch("os.path.isfile", return_value=True), patch(
            "builtins.open", mock_open(read_data=patch_content)
        ), patch(
            "subprocess.run"
        ) as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")
            applier = PatchApplier(repo_path)
            result = applier.apply_patch(patch_file)
            self.assertTrue(result)
            mock_run.assert_called_once_with(
                ["git", "-C", repo_path, "apply"],
                input=patch_content,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

    def test_apply_patch_git_apply_failure(self):
        repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        patch_file = f"patch_{uuid.uuid4().hex}.patch"
        err_msg = f"apply_failed_{uuid.uuid4().hex}"
        with patch("os.path.isabs", return_value=True), patch(
            "os.path.exists", return_value=True
        ), patch("os.path.isfile", return_value=True), patch(
            "builtins.open", mock_open(read_data=b"patch_content")
        ), patch(
            "subprocess.run"
        ) as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stderr=err_msg.encode("utf-8")
            )
            applier = PatchApplier(repo_path)
            with self.assertRaises(PatchApplierError) as ctx:
                applier.apply_patch(patch_file)
            self.assertIn(err_msg, str(ctx.exception))

    def test_apply_patch_file_not_found(self):
        repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        patch_source = f"nonexistent_{uuid.uuid4().hex}"
        with patch("os.path.isabs", return_value=False), patch(
            "os.path.exists", return_value=False
        ), patch("builtins.open", side_effect=OSError("File not found")):
            applier = PatchApplier(repo_path)
            with self.assertRaises(PatchApplierError) as ctx:
                applier.apply_patch(patch_source)
            self.assertIn("Patch source not found or invalid", str(ctx.exception))

    def test_rollback_success(self):
        repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        backup_tag = f"backup_{uuid.uuid4().hex}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            applier = PatchApplier(repo_path)
            result = applier.rollback(backup_tag)
            self.assertTrue(result)
            mock_run.assert_called_once_with(
                ["git", "-C", repo_path, "checkout", backup_tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

    def test_rollback_failure(self):
        repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        backup_tag = f"backup_{uuid.uuid4().hex}"
        err_msg = f"checkout_error_{uuid.uuid4().hex}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stderr=err_msg.encode("utf-8")
            )
            applier = PatchApplier(repo_path)
            with self.assertRaises(PatchApplierError) as ctx:
                applier.rollback(backup_tag)
            self.assertIn("Failed to rollback", str(ctx.exception))

    def test_verify_repository_state_success(self):
        repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            applier = PatchApplier(repo_path)
            result = applier.verify_repository_state()
            self.assertTrue(result)
            mock_run.assert_called_once_with(
                ["git", "-C", repo_path, "status", "--porcelain"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

    def test_verify_repository_state_failure(self):
        repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        out_msg = f"uncommitted_files_{uuid.uuid4().hex}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout=out_msg.encode("utf-8")
            )
            applier = PatchApplier(repo_path)
            with self.assertRaises(PatchApplierError) as ctx:
                applier.verify_repository_state()
            self.assertIn("Repository verification failed", str(ctx.exception))

    def test_safe_apply_success(self):
        repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        patch_path = f"/tmp/patch_{uuid.uuid4().hex}"
        backup_tag = f"tag_{uuid.uuid4().hex}"
        applier = PatchApplier(repo_path)

        with patch.object(applier, "create_recovery_point") as mock_cr, patch.object(
            applier, "apply_patch"
        ) as mock_ap, patch.object(
            applier, "verify_repository_state"
        ) as mock_vr, patch.object(
            applier, "rollback"
        ) as mock_rb:

            result = applier.safe_apply(patch_path, backup_tag)
            self.assertTrue(result)
            mock_cr.assert_called_once_with(backup_tag)
            mock_ap.assert_called_once_with(patch_path)
            mock_vr.assert_called_once()
            mock_rb.assert_not_called()

    def test_safe_apply_rollback_on_error(self):
        repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        patch_path = f"/tmp/patch_{uuid.uuid4().hex}"
        backup_tag = f"tag_{uuid.uuid4().hex}"
        applier = PatchApplier(repo_path)
        err_msg = f"apply_err_{uuid.uuid4().hex}"

        with patch.object(applier, "create_recovery_point") as mock_cr, patch.object(
            applier, "apply_patch", side_effect=PatchApplierError(err_msg)
        ) as mock_ap, patch.object(applier, "rollback") as mock_rb:

            with self.assertRaises(PatchApplierError) as ctx:
                applier.safe_apply(patch_path, backup_tag)

            mock_cr.assert_called_once_with(backup_tag)
            mock_ap.assert_called_once_with(patch_path)
            mock_rb.assert_called_once_with(backup_tag)
            self.assertIn(err_msg, str(ctx.exception))

    def test_apply_patch_standalone_function(self):
        repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        file_path = f"file_{uuid.uuid4().hex}.py"
        content = f"code_{uuid.uuid4().hex}"
        backup_id = f"backup_{uuid.uuid4().hex}"
        patch_data = {
            "file_path": file_path,
            "content": content,
            "backup_id": backup_id,
        }

        m_open = mock_open()
        with patch("builtins.open", m_open), patch(
            "subprocess.run"
        ) as mock_sub_run, patch(
            "skills.patch_applier.PatchApplier"
        ) as mock_applier_cls:

            mock_inst = MagicMock()
            mock_applier_cls.return_value = mock_inst

            res = apply_patch(repo_path, patch_data)
            self.assertTrue(res)

            target_path = os.path.join(repo_path, file_path)
            m_open.assert_called_once_with(target_path, "w", encoding="utf-8")
            m_open().write.assert_called_once_with(content)

            mock_applier_cls.assert_called_once_with(repo_path)
            mock_inst.create_recovery_point.assert_called_once_with(backup_id)
            mock_inst.verify_repository_state.assert_called_once()
            self.assertEqual(mock_sub_run.call_count, 2)


if __name__ == "__main__":
    unittest.main()