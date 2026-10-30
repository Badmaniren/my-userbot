import unittest
import os
import subprocess
import tempfile
import shutil
import uuid
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch


class TestPatchApplierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "-C", self.test_dir, "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "ArchitectTest"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "architect@test.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.initial_file = "README.md"
        self.initial_path = os.path.join(self.test_dir, self.initial_file)
        self.initial_content = f"Initial content {uuid.uuid4()}"
        with open(self.initial_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)
            
        subprocess.run(["git", "-C", self.test_dir, "add", self.initial_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_patch_applier_lifecycle_and_recovery(self):
        applier = PatchApplier(self.test_dir)
        backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        
        applier.create_recovery_point(backup_tag)
        
        new_file_name = f"file_{uuid.uuid4().hex[:6]}.txt"
        new_file_content = f"Random payload {uuid.uuid4()}"
        patch_path = os.path.join(self.test_dir, f"patch_{uuid.uuid4().hex[:6]}.diff")
        
        diff_content = f"diff --git a/{new_file_name} b/{new_file_name}\nnew file mode 100644\n--- /dev/null\n+++ b/{new_file_name}\n@@ -0,0 +1 @@\n+{new_file_content}\n"
        with open(patch_path, "w", encoding="utf-8") as f:
            f.write(diff_content)

        applier.apply_patch(patch_path)
        applier.verify_repository_state()
        
        target_applied_file = os.path.join(self.test_dir, new_file_name)
        self.assertTrue(os.path.exists(target_applied_file))
        with open(target_applied_file, "r", encoding="utf-8") as f:
            self.assertEqual(f.read().strip(), new_file_content)

        applier.rollback(backup_tag)
        self.assertFalse(os.path.exists(target_applied_file))

    def test_apply_patch_integration_function(self):
        target_file = f"module_{uuid.uuid4().hex[:6]}.py"
        target_content = f"# Generated content {uuid.uuid4()}"
        backup_id = f"bk_{uuid.uuid4().hex[:8]}"
        
        patch_data = {
            "file_path": target_file,
            "content": target_content,
            "backup_id": backup_id
        }
        
        result = apply_patch(self.test_dir, patch_data)
        self.assertTrue(result)
        
        created_file_path = os.path.join(self.test_dir, target_file)
        self.assertTrue(os.path.exists(created_file_path))
        with open(created_file_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), target_content)

        applier = PatchApplier(self.test_dir)
        applier.verify_repository_state()


if __name__ == "__main__":
    unittest.main()