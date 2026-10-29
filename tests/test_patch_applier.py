import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import uuid
import io
import subprocess
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch

class TestPatchApplier(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.applier = PatchApplier(self.repo_path)
        self.backup_tag = uuid.uuid4().hex

    def test_create_recovery_point_success(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.applier.create_recovery_point(self.backup_tag)
            self.assertTrue(result)
            mock_run.assert_called_with(
                ["git", "-C", self.repo_path, "branch", self.backup_tag],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

    def test_create_recovery_point_failure(self):
        err_msg = uuid.uuid4().hex
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr=err_msg.encode())
            with self.assertRaises(PatchApplierError) as cm:
                self.applier.create_recovery_point(self.backup_tag)
            self.assertIn(err_msg, str(cm.exception))

    def test_apply_patch_file_success(self):
        patch_file = f"{uuid.uuid4().hex}.patch"
        content = b"random_patch_content_" + uuid.uuid4().bytes

        with patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", mock_open(read_data=content)), \
             patch("subprocess.run") as mock_run:
            
            mock_run.return_value = MagicMock(returncode=0)
            result = self.applier.apply_patch(patch_file)
            self.assertTrue(result)
            mock_run.assert_called_with(
                ["git", "-C", self.repo_path, "apply"],
                input=content, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

    def test_apply_patch_invalid_source(self):
        bad_source = uuid.uuid4().hex
        with patch("os.path.exists", return_value=False), \
             patch("builtins.open", side_effect=FileNotFoundError):
            with self.assertRaises(PatchApplierError):
                self.applier.apply_patch(bad_source)

    def test_rollback_success(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.applier.rollback(self.backup_tag)
            self.assertTrue(result)
            mock_run.assert_has_calls([
                unittest.mock.call(["git", "-C", self.repo_path, "checkout", self.backup_tag], stdout=subprocess.PIPE, stderr=subprocess.PIPE),
                unittest.mock.call(["git", "-C", self.repo_path, "clean", "-fd"], stdout=subprocess.PIPE, stderr=subprocess.PIPE),
                unittest.mock.call(["git", "-C", self.repo_path, "reset", "--hard"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            ])

    def test_verify_repository_state_failure(self):
        error_output = uuid.uuid4().hex
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout=error_output.encode())
            with self.assertRaises(PatchApplierError) as cm:
                self.applier.verify_repository_state()
            self.assertIn(error_output, str(cm.exception))

    def test_safe_apply_rollback_on_failure(self):
        patch_path = uuid.uuid4().hex
        with patch.object(self.applier, "create_recovery_point") as mock_cp, \
             patch.object(self.applier, "apply_patch", side_effect=PatchApplierError("fail")), \
             patch.object(self.applier, "rollback") as mock_rb:

            with self.assertRaises(PatchApplierError):
                self.applier.safe_apply(patch_path, self.backup_tag)

            mock_cp.assert_called_once()
            mock_rb.assert_called_once_with(self.backup_tag)

    def test_integration_apply_patch(self):
        repo = f"/tmp/{uuid.uuid4().hex}"
        data = {
            "file_path": f"{uuid.uuid4().hex}.txt",
            "content": uuid.uuid4().hex,
            "backup_id": uuid.uuid4().hex
        }

        with patch("builtins.open", mock_open()), \
             patch("subprocess.run") as mock_run, \
             patch("skills.patch_applier.PatchApplier.create_recovery_point"), \
             patch("skills.patch_applier.PatchApplier.verify_repository_state"):

            result = apply_patch(repo, data)
            self.assertTrue(result)

            # Проверяем, что вызывались команды git add и git commit
            calls = [
                unittest.mock.call(["git", "-C", repo, "add", data["file_path"]], check=True),
                unittest.mock.call(["git", "-C", repo, "commit", "-m", "Apply patch via PatchApplier"], check=True)
            ]
            mock_run.assert_has_calls(calls, any_order=True)

if __name__ == "__main__":
    unittest.main()