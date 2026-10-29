import os
import subprocess
import tempfile
import unittest
import uuid
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

        subprocess.run(["git", "-C", self.repo_path, "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Architect Test"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "architect@test.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.initial_file = "init_file.txt"
        self.initial_path = os.path.join(self.repo_path, self.initial_file)
        with open(self.initial_path, "w", encoding="utf-8") as f:
            f.write("Initial content\n")
            
        subprocess.run(["git", "-C", self.repo_path, "add", self.initial_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_apply_patch_integration_success(self):
        unique_file = f"file_{uuid.uuid4().hex}.txt"
        unique_content = f"content_{uuid.uuid4().hex}"
        unique_backup = f"backup_{uuid.uuid4().hex[:8]}"

        patch_data = {
            "file_path": unique_file,
            "content": unique_content,
            "backup_id": unique_backup
        }

        result = apply_patch(self.repo_path, patch_data)
        self.assertTrue(result)

        target_file_path = os.path.join(self.repo_path, unique_file)
        self.assertTrue(os.path.exists(target_file_path))

        with open(target_file_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, unique_content)

        applier = PatchApplier(self.repo_path)
        self.assertTrue(applier.verify_repository_state())

    def test_safe_apply_and_rollback(self):
        applier = PatchApplier(self.repo_path)
        backup_tag = f"tag_{uuid.uuid4().hex[:8]}"

        bad_file = f"bad_{uuid.uuid4().hex}.txt"
        bad_path = os.path.join(self.repo_path, bad_file)

        applier.create_recovery_point(backup_tag)

        with open(bad_path, "w", encoding="utf-8") as f:
            f.write("Broken state")

        with self.assertRaises(PatchApplierError):
            applier.apply_patch("non_existent_patch_source_xyz.patch")

        applier.rollback(backup_tag)
        self.assertFalse(os.path.exists(bad_path))
        self.assertTrue(applier.verify_repository_state())


if __name__ == "__main__":
    unittest.main()