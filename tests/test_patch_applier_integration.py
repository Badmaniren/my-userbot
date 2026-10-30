import unittest
import os
import tempfile
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

    def test_patch_applier_pipeline_and_git_inspector(self):
        applier = PatchApplier(self.repo_path)
        inspector = GitInspector(self.repo_path)

        backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        applier.create_recovery_point(backup_tag)

        target_file = f"module_{random.randint(1000, 9999)}.py"
        unique_string = f"DATA_{uuid.uuid4()}"
        
        patch_data = {
            "file_path": target_file,
            "content": f"print('{unique_string}')\n",
            "backup_id": backup_tag
        }
        
        result = apply_patch(self.repo_path, patch_data)
        self.assertTrue(result)
        
        created_file_path = os.path.join(self.repo_path, target_file)
        self.assertTrue(os.path.exists(created_file_path))
        
        with open(created_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(unique_string, content)
        
        history = inspector.get_commit_history(max_count=5)
        self.assertTrue(len(history) >= 2)
        
        applier.verify_repository_state()

    def test_patch_applier_safe_apply_rollback(self):
        applier = PatchApplier(self.repo_path)
        backup_tag = f"rollback_backup_{uuid.uuid4().hex[:8]}"

        invalid_patch_filename = f"bad_patch_{uuid.uuid4().hex[:8]}.patch"
        invalid_patch_path = os.path.join(self.repo_path, invalid_patch_filename)
        
        with open(invalid_patch_path, "w", encoding="utf-8") as f:
            f.write("INVALID PATCH CONTENT FORMAT THAT FAILS GIT APPLY\n")

        with self.assertRaises(PatchApplierError):
            applier.safe_apply(invalid_patch_filename, backup_tag)

        applier.verify_repository_state()


if __name__ == "__main__":
    unittest.main()