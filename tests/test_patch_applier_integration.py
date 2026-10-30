import unittest
import tempfile
import os
import subprocess
import uuid
import random
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch
from skills.git_inspector import GitInspector


class TestPatchApplierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        subprocess.run(["git", "-C", self.repo_path, "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Test User"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "test@example.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.initial_file = "README.md"
        self.initial_content = f"Initial content {uuid.uuid4()}"
        file_path = os.path.join(self.repo_path, self.initial_file)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)
            
        subprocess.run(["git", "-C", self.repo_path, "add", self.initial_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_patch_applier_lifecycle(self):
        applier = PatchApplier(self.repo_path)
        
        backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        applier.create_recovery_point(backup_tag)
        
        new_file_name = f"feature_{random.randint(1000, 9999)}.py"
        new_file_content = f"# Feature code {uuid.uuid4()}\nprint('hello')"
        
        patch_data = {
            "file_path": new_file_name,
            "content": new_file_content,
            "backup_id": f"dict_backup_{uuid.uuid4().hex[:8]}"
        }
        
        success = apply_patch(self.repo_path, patch_data)
        self.assertTrue(success)
        
        created_file_path = os.path.join(self.repo_path, new_file_name)
        self.assertTrue(os.path.exists(created_file_path))
        with open(created_file_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, new_file_content)
        
        inspector = GitInspector(self.repo_path)
        history = inspector.get_commit_history(max_count=5)
        self.assertGreaterEqual(len(history), 2)
        
        applier.rollback(backup_tag)
        self.assertFalse(os.path.exists(created_file_path))
        
        applier.verify_repository_state()


if __name__ == "__main__":
    unittest.main()