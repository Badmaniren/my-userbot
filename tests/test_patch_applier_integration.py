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
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Test Architect"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "architect@test.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.initial_file = "README.md"
        initial_path = os.path.join(self.repo_path, self.initial_file)
        with open(initial_path, "w", encoding="utf-8") as f:
            f.write("# Initial Repository\n")
            
        subprocess.run(["git", "-C", self.repo_path, "add", self.initial_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_patch_applier_lifecycle_and_recovery(self):
        applier = PatchApplier(self.repo_path)

        backup_tag = f"backup-{uuid.uuid4().hex[:8]}"
        self.assertTrue(applier.create_recovery_point(backup_tag))

        target_file = f"module_{random.randint(1000, 9999)}.py"
        unique_content = f"# Generated content {uuid.uuid4()}\n"
        
        patch_data = {
            "file_path": target_file,
            "content": unique_content,
            "backup_id": backup_tag
        }
        
        result = apply_patch(self.repo_path, patch_data)
        self.assertTrue(result)

        target_full_path = os.path.join(self.repo_path, target_file)
        self.assertTrue(os.path.exists(target_full_path))

        with open(target_full_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, unique_content)

        inspector = GitInspector(self.repo_path)
        history = inspector.get_commit_history(max_count=5)
        self.assertGreaterEqual(len(history), 2)
        
        rollback_tag = f"rollback-{uuid.uuid4().hex[:8]}"
        self.assertTrue(applier.create_recovery_point(rollback_tag))

        bad_file = "corrupted.py"
        bad_full_path = os.path.join(self.repo_path, bad_file)
        with open(bad_full_path, "w", encoding="utf-8") as f:
            f.write("syntax error = {{\n")

        with self.assertRaises(Exception):
            applier.safe_apply(bad_file, rollback_tag)

        self.assertTrue(applier.verify_repository_state())

    def test_patch_applier_failure_handling(self):
        applier = PatchApplier(self.repo_path)
        non_existent_backup = f"non-existent-{uuid.uuid4().hex}"
        with self.assertRaises(PatchApplierError):
            applier.rollback(non_existent_backup)


if __name__ == "__main__":
    unittest.main()