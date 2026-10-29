import unittest
import os
import subprocess
import uuid
import random
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch
from skills.code_sanitizer import CodeSanitizerError
from skills.code_validator import CodeValidatorError
from skills.git_inspector import GitInspector


class TestPatchApplierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"/tmp/test_repo_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        
        subprocess.run(["git", "-C", self.test_dir, "init"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Test Bot"], check=True)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "bot@test.com"], check=True)
        
        self.initial_file = "README.md"
        self.initial_content = f"Initial content {uuid.uuid4().hex}\n"
        self.file_path = os.path.join(self.test_dir, self.initial_file)

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)
            
        subprocess.run(["git", "-C", self.test_dir, "add", self.initial_file], check=True)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True)

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.test_dir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_patch_applier_full_lifecycle_and_rollback(self):
        applier = PatchApplier(self.test_dir)
        backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        
        self.assertTrue(applier.create_recovery_point(backup_tag))
        
        new_content = f"Updated content {random.randint(1000, 9999)}\n"
        patch_file_name = f"change_{uuid.uuid4().hex[:6]}.patch"
        patch_file_path = os.path.join(self.test_dir, patch_file_name)
        
        diff_content = f"""diff --git a/README.md b/README.md
index 1234567..89abcdef 100644
--- a/README.md
+++ b/README.md
@@ -1 +1 @@
-{self.initial_content.strip()}
+{new_content.strip()}
"""
        with open(patch_file_path, "w", encoding="utf-8") as f:
            f.write(diff_content)

        self.assertTrue(applier.safe_apply(patch_file_path, backup_tag))
        
        inspector = GitInspector(self.test_dir)
        history = inspector.get_commit_history(max_count=5)
        self.assertIsInstance(history, list)

        invalid_patch_name = f"bad_{uuid.uuid4().hex[:6]}.patch"
        invalid_patch_path = os.path.join(self.test_dir, invalid_patch_name)
        with open(invalid_patch_path, "w", encoding="utf-8") as f:
            f.write("INVALID PATCH DATA FORMAT RANDOM")

        new_backup_tag = f"backup_fail_{uuid.uuid4().hex[:8]}"
        applier.create_recovery_point(new_backup_tag)
        
        with self.assertRaises((PatchApplierError, Exception)):
            applier.safe_apply(invalid_patch_path, new_backup_tag)

    def test_apply_patch_integration_function(self):
        target_file = f"module_{uuid.uuid4().hex[:6]}.py"
        random_code_string = f"x = {random.randint(1, 500)}\n"
        backup_id = f"id_{uuid.uuid4().hex[:8]}"
        
        patch_data = {
            "file_path": target_file,
            "content": random_code_string,
            "backup_id": backup_id
        }
        
        result = apply_patch(self.test_dir, patch_data)
        self.assertTrue(result)
        
        created_file_full_path = os.path.join(self.test_dir, target_file)
        self.assertTrue(os.path.exists(created_file_full_path))
        
        with open(created_file_full_path, "r", encoding="utf-8") as f:
            read_data = f.read()
        self.assertEqual(read_data, random_code_string)


if __name__ == "__main__":
    unittest.main()