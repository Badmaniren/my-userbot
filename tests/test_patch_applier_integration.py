import unittest
import os
import tempfile
import subprocess
import uuid
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        subprocess.run(["git", "init", self.repo_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Test User"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "test@example.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.initial_file = "README.md"
        self.initial_content = f"Initial content {uuid.uuid4()}\n"
        file_full_path = os.path.join(self.repo_path, self.initial_file)
        with open(file_full_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)
            
        subprocess.run(["git", "-C", self.repo_path, "add", self.initial_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_apply_patch_integration_success(self):
        unique_file_name = f"patch_target_{uuid.uuid4().hex[:8]}.txt"
        unique_content = f"Random telemetry data: {uuid.uuid4()}"
        
        patch_data = {
            "file_path": unique_file_name,
            "content": unique_content,
            "backup_id": f"backup_{uuid.uuid4().hex[:6]}"
        }
        
        result = apply_patch(self.repo_path, patch_data)
        self.assertTrue(result)
        
        target_file_full = os.path.join(self.repo_path, unique_file_name)
        self.assertTrue(os.path.exists(target_file_full))
        
        with open(target_file_full, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, unique_content)

    def test_patch_applier_recovery_and_rollback(self):
        applier = PatchApplier(self.repo_path)
        backup_tag = f"tag_{uuid.uuid4().hex[:6]}"
        
        self.assertTrue(applier.create_recovery_point(backup_tag))
        
        target_file = "experimental.txt"
        target_path = os.path.join(self.repo_path, target_file)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write("Experimental changes")
            
        subprocess.run(["git", "-C", self.repo_path, "add", target_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Add experimental"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.assertTrue(applier.verify_repository_state())
        
        self.assertTrue(applier.rollback(backup_tag))
        self.assertFalse(os.path.exists(target_path))

    def test_patch_applier_safe_apply_failure(self):
        applier = PatchApplier(self.repo_path)
        backup_tag = f"safe_tag_{uuid.uuid4().hex[:6]}"
        non_existent_patch = f"nonexistent_{uuid.uuid4()}.patch"
        
        with self.assertRaises(PatchApplierError):
            applier.safe_apply(non_existent_patch, backup_tag)


if __name__ == "__main__":
    unittest.main()