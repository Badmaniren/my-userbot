import unittest
import tempfile
import os
import shutil
import subprocess
import uuid
import random

from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch
from skills.git_inspector import GitInspector


class TestPatchApplierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "-C", self.test_dir, "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Test User"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "test@example.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.initial_file = "README.md"
        self.initial_content = f"Initial content {uuid.uuid4()}"
        file_path = os.path.join(self.test_dir, self.initial_file)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)
            
        subprocess.run(["git", "-C", self.test_dir, "add", self.initial_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_patch_applier_full_integration(self):
        applier = PatchApplier(self.test_dir)
        inspector = GitInspector(self.test_dir)

        backup_tag = f"backup-{uuid.uuid4()}"
        applier.create_recovery_point(backup_tag)

        target_file = f"src/module_{random.randint(1000, 9999)}.py"
        file_content = f"# Generated content {uuid.uuid4()}"

        patch_data = {
            "file_path": target_file,
            "content": file_content,
            "backup_id": backup_tag
        }

        res = apply_patch(self.test_dir, patch_data)
        self.assertTrue(res)

        full_target_path = os.path.join(self.test_dir, target_file)
        self.assertTrue(os.path.exists(full_target_path))

        with open(full_target_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, file_content)

        history = inspector.get_commit_history(max_count=5)
        self.assertTrue(len(history) >= 2)

        applier.verify_repository_state()

    def test_patch_applier_rollback_on_error(self):
        applier = PatchApplier(self.test_dir)
        backup_tag = f"backup-err-{uuid.uuid4()}"
        
        applier.create_recovery_point(backup_tag)
        
        invalid_target = "README.md"
        full_path = os.path.join(self.test_dir, invalid_target)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(f"Corrupted content {uuid.uuid4()}")

        with self.assertRaises((PatchApplierError, Exception)):
            applier.verify_repository_state()
            applier.rollback(backup_tag)
            applier.verify_repository_state()


if __name__ == "__main__":
    unittest.main()