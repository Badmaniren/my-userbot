import unittest
import tempfile
import shutil
import os
import uuid
import random
import subprocess
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        subprocess.run(["git", "-C", self.repo_path, "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Architect Test"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "architect@test.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.initial_file = os.path.join(self.repo_path, "README.md")
        with open(self.initial_file, "w", encoding="utf-8") as f:
            f.write("# Initial State\n")
            
        subprocess.run(["git", "-C", self.repo_path, "add", "README.md"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_safe_apply_and_rollback_integration(self):
        unique_backup_tag = f"backup-{uuid.uuid4().hex[:8]}"
        applier = PatchApplier(self.repo_path)
        
        patch_filename = f"patch_{uuid.uuid4().hex[:6]}.patch"
        patch_path = os.path.join(self.repo_path, patch_filename)
        
        patch_content = (
            f"diff --git a/README.md b/README.md\n"
            f"index 1234567..89abcdef 100644\n"
            f"--- a/README.md\n"
            f"+++ b/README.md\n"
            f"@@ -1 +1,2 @@\n"
            f" # Initial State\n"
            f"+# Updated via patch {uuid.uuid4().hex[:6]}\n"
        )

        with open(patch_path, "w", encoding="utf-8") as f:
            f.write(patch_content)

        applier.safe_apply(patch_filename, unique_backup_tag)

        with open(self.initial_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Updated via patch", content)

        bad_backup_tag = f"bad-backup-{uuid.uuid4().hex[:8]}"
        bad_patch_filename = f"bad_patch_{uuid.uuid4().hex[:6]}.patch"
        bad_patch_path = os.path.join(self.repo_path, bad_patch_filename)

        with open(bad_patch_path, "w", encoding="utf-8") as f:
            f.write("INVALID PATCH CONTENT THAT WILL FAIL GIT APPLY\n")

        with self.assertRaises(PatchApplierError):
            applier.safe_apply(bad_patch_filename, bad_backup_tag)

    def test_apply_patch_dictionary_integration(self):
        unique_backup_id = f"dict-backup-{uuid.uuid4().hex[:8]}"
        unique_file_name = f"dir_{uuid.uuid4().hex[:4]}/module_{uuid.uuid4().hex[:6]}.py"
        unique_code_content = f"# Generated content {uuid.uuid4()}\nx = {random.randint(1000, 9999)}\n"
        
        patch_data = {
            "file_path": unique_file_name,
            "content": unique_code_content,
            "backup_id": unique_backup_id
        }
        
        result = apply_patch(self.repo_path, patch_data)
        self.assertTrue(result)
        
        target_file_full = os.path.join(self.repo_path, unique_file_name)
        self.assertTrue(os.path.exists(target_file_full))
        
        with open(target_file_full, "r", encoding="utf-8") as f:
            read_content = f.read()

        self.assertEqual(read_content, unique_code_content)
        
        status_cmd = ["git", "-C", self.repo_path, "status", "--porcelain"]
        status_res = subprocess.run(status_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(len(status_res.stdout.strip()), 0)


if __name__ == "__main__":
    unittest.main()