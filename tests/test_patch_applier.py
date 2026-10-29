import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import os
import sys

from skills.patch_applier import PatchApplier, PatchApplierError

class TestPatchApplier(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.patch_applier = PatchApplier(self.repo_path)
        self.random_patch_content = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py\n" \
                                    f"--- a/{uuid.uuid4().hex}.py\n" \
                                    f"+++ b/{uuid.uuid4().hex}.py\n" \
                                    f"@@ -1,1 +1,1 @@\n" \
                                    f"-print('{uuid.uuid4().hex}')\n" \
                                    f"+print('{uuid.uuid4().hex}')\n"

    def test_init_sets_repo_path(self):
        random_path = f"/var/repo/{uuid.uuid4().hex}"
        applier = PatchApplier(random_path)
        self.assertEqual(applier.repo_path, random_path)

    def test_create_recovery_point_success(self):
        random_branch = f"backup-{uuid.uuid4().hex[:8]}"
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=uuid.uuid4().hex.encode())
            
            result = self.patch_applier.create_recovery_point(random_branch)
            
            self.assertTrue(result)
            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            cmd = args[0]
            self.assertIn("git", cmd)
            self.assertIn("branch", cmd)
            self.assertIn(random_branch, cmd)

    def test_create_recovery_point_failure(self):
        random_branch = f"backup-{uuid.uuid4().hex[:8]}"
        random_error = uuid.uuid4().hex
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=128, stderr=random_error.encode())
            
            with self.assertRaises(PatchApplierError) as ctx:
                self.patch_applier.create_recovery_point(random_branch)
            
            self.assertIn(random_error, str(ctx.exception))

    def test_apply_patch_success(self):
        random_file_name = f"{uuid.uuid4().hex}.py"
        with patch('subprocess.run') as mock_run, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_run.return_value = MagicMock(returncode=0, stdout=b"")
            mock_open.return_value = io.BytesIO(self.random_patch_content.encode('utf-8'))

            result = self.patch_applier.apply_patch(random_file_name)
            
            self.assertTrue(result)
            self.assertEqual(mock_run.call_count, 1)

    def test_apply_patch_failure_raises_exception(self):
        random_file_name = f"{uuid.uuid4().hex}.py"
        random_stderr = uuid.uuid4().hex
        with patch('subprocess.run') as mock_run, \
             patch('builtins.open', create=True) as mock_open:
            
            mock_run.return_value = MagicMock(returncode=1, stderr=random_stderr.encode('utf-8'))
            mock_open.return_value = io.BytesIO(self.random_patch_content.encode('utf-8'))

            with self.assertRaises(PatchApplierError) as ctx:
                self.patch_applier.apply_patch(random_file_name)

            self.assertIn(random_stderr, str(ctx.exception))

    def test_rollback_success(self):
        random_branch = f"backup-{uuid.uuid4().hex[:8]}"
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=b"")

            result = self.patch_applier.rollback(random_branch)

            self.assertTrue(result)
            self.assertTrue(mock_run.called)

    def test_rollback_failure(self):
        random_branch = f"backup-{uuid.uuid4().hex[:8]}"
        random_error = uuid.uuid4().hex
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr=random_error.encode())

            with self.assertRaises(PatchApplierError) as ctx:
                self.patch_applier.rollback(random_branch)

            self.assertIn(random_error, str(ctx.exception))

    def test_safe_apply_workflow_success(self):
        random_patch_path = f"/tmp/{uuid.uuid4().hex}.patch"
        random_backup_tag = f"recovery-{uuid.uuid4().hex[:6]}"

        with patch.object(self.patch_applier, 'create_recovery_point') as mock_backup, \
             patch.object(self.patch_applier, 'apply_patch') as mock_apply, \
             patch.object(self.patch_applier, 'verify_repository_state') as mock_verify:

            mock_backup.return_value = True
            mock_apply.return_value = True
            mock_verify.return_value = True

            result = self.patch_applier.safe_apply(random_patch_path, random_backup_tag)

            self.assertTrue(result)
            mock_backup.assert_called_once_with(random_backup_tag)
            mock_apply.assert_called_once_with(random_patch_path)
            mock_verify.assert_called_once()

    def test_safe_apply_workflow_rollback_on_failure(self):
        random_patch_path = f"/tmp/{uuid.uuid4().hex}.patch"
        random_backup_tag = f"recovery-{uuid.uuid4().hex[:6]}"

        with patch.object(self.patch_applier, 'create_recovery_point') as mock_backup, \
             patch.object(self.patch_applier, 'apply_patch') as mock_apply, \
             patch.object(self.patch_applier, 'rollback') as mock_rollback:

            mock_backup.return_value = True
            mock_apply.side_effect = PatchApplierError(uuid.uuid4().hex)
            mock_rollback.return_value = True

            with self.assertRaises(PatchApplierError):
                self.patch_applier.safe_apply(random_patch_path, random_backup_tag)

            mock_backup.assert_called_once_with(random_backup_tag)
            mock_apply.assert_called_once_with(random_patch_path)
            mock_rollback.assert_called_once_with(random_backup_tag)

    def test_verify_repository_state_clean(self):
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=b"")
            result = self.patch_applier.verify_repository_state()
            self.assertTrue(result)

    def test_verify_repository_state_dirty_or_failed(self):
        random_output = uuid.uuid4().hex
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout=random_output.encode())
            with self.assertRaises(PatchApplierError):
                self.patch_applier.verify_repository_state()

if __name__ == '__main__':
    unittest.main()