import unittest
import os
import subprocess
import tempfile
import shutil
import uuid
import random

from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch
from skills.git_inspector import GitInspector


class TestPatchApplierIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "-C", self.test_dir, "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Architect"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "architect@system.local"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.init_file = "README.md"
        self.init_path = os.path.join(self.test_dir, self.init_file)
        with open(self.init_path, "w", encoding="utf-8") as f:
            f.write("Initial state\n")
            
        subprocess.run(["git", "-C", self.test_dir, "add", self.init_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_integration_patch_applier_lifecycle(self):
        unique_id = str(uuid.uuid4())[:8]
        backup_tag = f"backup-{unique_id}"
        target_filename = f"file_{unique_id}.txt"
        file_content = f"Random content: {random.randint(1000, 9999)}\n"

        patch_data = {
            "file_path": target_filename,
            "content": file_content,
            "backup_id": backup_tag
        }

        success = apply_patch(self.test_dir, patch_data)
        self.assertTrue(success)

        target_full_path = os.path.join(self.test_dir, target_filename)
        self.assertTrue(os.path.exists(target_full_path))
        with open(target_full_path, "r", encoding="utf-8") as f:
            read_data = f.read()
        self.assertEqual(read_data, file_content)

        inspector = GitInspector(self.test_dir)
        history = inspector.get_commit_history(max_count=5)
        self.assertGreaterEqual(len(history), 2)

        applier = PatchApplier(self.test_dir)
        applier.verify_repository_state()

        corrupt_backup = f"rollback-{unique_id}"
        applier.create_recovery_point(corrupt_backup)

        bad_filename = f"bad_{unique_id}.txt"
        bad_full_path = os.path.join(self.test_dir, bad_filename)
        with open(bad_full_path, "w", encoding="utf-8") as f:
            f.write("Should be rolled back\n")

        applier.rollback(corrupt_backup)
        self.assertFalse(os.path.exists(bad_full_path))


if __name__ == "__main__":
    unittest.main()