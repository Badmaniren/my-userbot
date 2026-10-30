import unittest
from unittest.mock import patch
import os
import io
import uuid
import random
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplier(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.backup_tag = f"branch_{uuid.uuid4().hex[:8]}"
        self.patch_source = f"{uuid.uuid4().hex}.patch"
        self.random_content = uuid.uuid4().bytes
        self.applier = PatchApplier(self.repo_path)

    def test_create_recovery_point_success(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = self.applier.create_recovery_point(self.backup_tag)
            self.assertTrue(result)
            mock_run.assert_called_once()
            called_args = mock_run.call_args[0][0]
            self.assertIn(self.backup_tag, called_args)

    def test_create_recovery_point_failure(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = random.randint(1, 255)
            mock_run.return_value.stderr = uuid.uuid4().bytes
            with self.assertRaises(PatchApplierError):
                self.applier.create_recovery_point(self.backup_tag)

    def test_apply_patch_file_success(self):
        with patch("os.path.isabs", return_value=True), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", unittest.mock.mock_open(read_data=self.random_content)), \
             patch("subprocess.run") as mock_run:

            mock_run.return_value.returncode = 0
            result = self.applier.apply_patch(self.patch_source)
            self.assertTrue(result)
            mock_run.assert_called_once()

    def test_apply_patch_not_found(self):
        with patch("os.path.isabs", return_value=False), \
             patch("os.path.exists", return_value=False), \
             patch("builtins.open", side_effect=FileNotFoundError):

            with self.assertRaises(PatchApplierError):
                self.applier.apply_patch(self.patch_source)

    def test_apply_patch_git_failure(self):
        with patch("os.path.isabs", return_value=True), \
             patch("os.path.exists", return_value=True), \
             patch("os.path.isfile", return_value=True), \
             patch("builtins.open", unittest.mock.mock_open(read_data=self.random_content)), \
             patch("subprocess.run") as mock_run:

            mock_run.return_value.returncode = random.randint(1, 255)
            mock_run.return_value.stderr = uuid.uuid4().bytes
            with self.assertRaises(PatchApplierError):
                self.applier.apply_patch(self.patch_source)

    def test_rollback_success(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = self.applier.rollback(self.backup_tag)
            self.assertTrue(result)
            self.assertEqual(mock_run.call_count, 3)
            self.assertIn("checkout", mock_run.call_args_list[0][0][0])
            self.assertIn(self.backup_tag, mock_run.call_args_list[0][0][0])
            self.assertIn("reset", mock_run.call_args_list[1][0][0])
            self.assertIn("--hard", mock_run.call_args_list[1][0][0])
            self.assertIn("clean", mock_run.call_args_list[2][0][0])

    def test_rollback_failure(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = random.randint(1, 255)
            mock_run.return_value.stderr = uuid.uuid4().bytes
            with self.assertRaises(PatchApplierError):
                self.applier.rollback(self.backup_tag)

    def test_verify_repository_state_success(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = self.applier.verify_repository_state()
            self.assertTrue(result)
            mock_run.assert_called_once()

    def test_verify_repository_state_failure(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = random.randint(1, 255)
            mock_run.return_value.stdout = uuid.uuid4().bytes
            with self.assertRaises(PatchApplierError):
                self.applier.verify_repository_state()

    def test_safe_apply_success(self):
        with patch.object(PatchApplier, "create_recovery_point", return_value=True) as mock_create, \
             patch.object(PatchApplier, "apply_patch", return_value=True) as mock_apply, \
             patch.object(PatchApplier, "verify_repository_state", return_value=True) as mock_verify:

            result = self.applier.safe_apply(self.patch_source, self.backup_tag)
            self.assertTrue(result)
            mock_create.assert_called_once_with(self.backup_tag)
            mock_apply.assert_called_once_with(self.patch_source)
            mock_verify.assert_called_once()

    def test_safe_apply_rollback_on_failure(self):
        with patch.object(PatchApplier, "create_recovery_point", return_value=True) as mock_create, \
             patch.object(PatchApplier, "apply_patch", side_effect=PatchApplierError(uuid.uuid4().hex)) as mock_apply, \
             patch.object(PatchApplier, "rollback", return_value=True) as mock_rollback:

            with self.assertRaises(PatchApplierError):
                self.applier.safe_apply(self.patch_source, self.backup_tag)

            mock_create.assert_called_once_with(self.backup_tag)
            mock_apply.assert_called_once_with(self.patch_source)
            mock_rollback.assert_called_once_with(self.backup_tag)

    def test_integration_apply_patch_success(self):
        file_path_rand = f"{uuid.uuid4().hex}.py"
        content_rand = uuid.uuid4().hex
        backup_id_rand = f"b_{uuid.uuid4().hex[:6]}"
        patch_data = {
            "file_path": file_path_rand,
            "content": content_rand,
            "backup_id": backup_id_rand
        }

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file, \
             patch("subprocess.run") as mock_run, \
             patch.object(PatchApplier, "create_recovery_point", return_value=True) as mock_create, \
             patch.object(PatchApplier, "verify_repository_state", return_value=True) as mock_verify:

            result = apply_patch(self.repo_path, patch_data)
            self.assertTrue(result)
            mock_file.assert_called_once()
            self.assertEqual(mock_run.call_count, 2)
            mock_create.assert_called_once_with(backup_id_rand)
            mock_verify.assert_called_once()


if __name__ == "__main__":
    unittest.main()