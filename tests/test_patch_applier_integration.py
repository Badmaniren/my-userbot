import unittest
import os
import tempfile
import shutil
import uuid
import subprocess
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch
from skills.git_inspector import GitInspector


class TestPatchApplierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "init", self.test_dir], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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

    def test_safe_apply_and_rollback_integration(self):
        applier = PatchApplier(self.test_dir)
        backup_tag = f"backup-{uuid.uuid4()}"
        
        target_file = f"module_{uuid.uuid4().hex[:8]}.py"
        unique_string = f"print('{uuid.uuid4()}')"
        
        patch_content = f"""diff --git a/{target_file} b/{target_file}
new file mode 100644
index 0000000..1234567
--- /dev/null
+++ b/{target_file}
@@ -0,0 +1 @@
+{unique_string}
"""
        patch_path = os.path.join(self.test_dir, "test.patch")
        with open(patch_path, "w", encoding="utf-8") as f:
            f.write(patch_content)

        applier.safe_apply(patch_path, backup_tag)
        
        created_file_path = os.path.join(self.test_dir, target_file)
        self.assertTrue(os.path.exists(created_file_path))
        with open(created_file_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read().strip(), unique_string)

        inspector = GitInspector(self.test_dir)
        history = inspector.get_commit_history(max_count=5)
        self.assertGreaterEqual(len(history), 1)

        bad_patch_content = "INVALID PATCH CONTENT DATA"
        bad_patch_path = os.path.join(self.test_dir, "bad.patch")
        with open(bad_patch_path, "w", encoding="utf-8") as f:
            f.write(bad_patch_content)

        fail_backup_tag = f"backup-fail-{uuid.uuid4()}"
        with self.assertRaises((PatchApplierError, subprocess.SubprocessError)):
            applier.safe_apply(bad_patch_path, fail_backup_tag)

    def test_apply_patch_dict_integration(self):
        file_name = f"feature_{uuid.uuid4().hex[:6]}.py"
        file_content = f"# Generated content {uuid.uuid4()}"
        backup_id = f"b-{uuid.uuid4().hex[:6]}"

        patch_data = {
            "file_path": file_name,
            "content": file_content,
            "backup_id": backup_id
        }

        result = apply_patch(self.test_dir, patch_data)
        self.assertTrue(result)

        full_path = os.path.join(self.test_dir, file_name)
        self.assertTrue(os.path.exists(full_path))
        with open(full_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), file_content)

        applier = PatchApplier(self.test_dir)
        self.assertTrue(applier.verify_repository_state())


if __name__ == "__main__":
    unittest.main()