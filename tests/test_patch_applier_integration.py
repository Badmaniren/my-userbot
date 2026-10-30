import unittest
import os
import subprocess
import shutil
import tempfile
import uuid
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        subprocess.run(["git", "-C", self.repo_path, "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "ArchitectTest"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "architect@test.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.initial_file = "init_file.txt"
        self.initial_path = os.path.join(self.repo_path, self.initial_file)
        self.initial_content = f"initial content {uuid.uuid4()}"
        
        with open(self.initial_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)
            
        subprocess.run(["git", "-C", self.repo_path, "add", self.initial_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_apply_patch_dict_integration(self):
        random_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        random_content = f"# Generated content {uuid.uuid4()}\nprint('OK')"
        random_backup_tag = f"backup_{uuid.uuid4().hex[:6]}"

        patch_data = {
            "file_path": random_file_name,
            "content": random_content,
            "backup_id": random_backup_tag
        }

        result = apply_patch(self.repo_path, patch_data)
        self.assertTrue(result)

        target_file_full_path = os.path.join(self.repo_path, random_file_name)
        self.assertTrue(os.path.exists(target_file_full_path))

        with open(target_file_full_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, random_content)

        applier = PatchApplier(self.repo_path)
        self.assertTrue(applier.verify_repository_state())

    def test_safe_apply_and_rollback_integration(self):
        applier = PatchApplier(self.repo_path)
        random_tag = f"tag_{uuid.uuid4().hex[:6]}"
        
        bad_file_name = f"faulty_{uuid.uuid4().hex[:8]}.txt"
        bad_file_path = os.path.join(self.repo_path, bad_file_name)
        
        with open(bad_file_path, "w", encoding="utf-8") as f:
            f.write("bad stuff")

        with self.assertRaises(PatchApplierError):
            applier.safe_apply(bad_file_path, random_tag)

        self.assertTrue(applier.verify_repository_state())
        self.assertFalse(os.path.exists(bad_file_path))


if __name__ == "__main__":
    unittest.main()