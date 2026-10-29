import unittest
import tempfile
import os
import subprocess
import uuid
import random
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

        subprocess.run(["git", "-C", self.repo_path, "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Test User"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "test@example.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.file_name = f"test_file_{uuid.uuid4().hex[:8]}.py"
        self.file_path = os.path.join(self.repo_path, self.file_name)
        
        self.initial_content = f"# Initial content {random.randint(1000, 9999)}\n"
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)
            
        subprocess.run(["git", "-C", self.repo_path, "add", self.file_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_patch_applier_lifecycle_and_rollback(self):
        applier = PatchApplier(self.repo_path)
        backup_tag = f"backup_{uuid.uuid4().hex[:8]}"

        applier.create_recovery_point(backup_tag)

        rand_val = random.randint(10000, 99999)
        updated_content = f"# Updated content {rand_val}\n"
        
        patch_data = {
            "file_path": self.file_name,
            "content": updated_content,
            "backup_id": backup_tag
        }
        
        result = apply_patch(self.repo_path, patch_data)
        self.assertTrue(result)
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(str(rand_val), content)

        applier.rollback(backup_tag)

        with open(self.file_path, "r", encoding="utf-8") as f:
            restored_content = f.read()
        self.assertEqual(restored_content, self.initial_content)

    def test_safe_apply_failure_and_auto_rollback(self):
        applier = PatchApplier(self.repo_path)
        backup_tag = f"safe_backup_{uuid.uuid4().hex[:8]}"

        bad_patch_name = f"nonexistent_{uuid.uuid4().hex[:8]}.patch"

        with self.assertRaises(PatchApplierError):
            applier.safe_apply(bad_patch_name, backup_tag)

        applier.verify_repository_state()


if __name__ == "__main__":
    unittest.main()