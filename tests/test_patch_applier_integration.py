import unittest
import os
import shutil
import subprocess
import uuid
import tempfile
from skills.patch_applier import PatchApplier, PatchApplierError

class TestPatchApplierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, "repo")
        os.makedirs(self.repo_path)
        
        subprocess.run(["git", "init", self.repo_path], check=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Test User"], check=True)

        self.initial_file = os.path.join(self.repo_path, "init.txt")
        with open(self.initial_file, "w") as f:
            f.write("initial content")
        subprocess.run(["git", "-C", self.repo_path, "add", "."], check=True)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True)

        self.applier = PatchApplier(self.repo_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_patch_application_lifecycle(self):
        backup_tag = f"backup_{uuid.uuid4().hex}"
        patch_filename = f"patch_{uuid.uuid4().hex}.patch"
        patch_path = os.path.join(self.test_dir, patch_filename)
        
        target_file = "target.txt"
        target_content = f"content_{uuid.uuid4().hex}"
        
        patch_content = (
            f"--- /dev/null\n"
            f"+++ b/{target_file}\n"
            f"@@ -0,0 +1 @@\n"
            f"+{target_content}\n"
        )
        
        with open(patch_path, "w") as f:
            f.write(patch_content)

        self.applier.create_recovery_point(backup_tag)

        apply_result = self.applier.apply_patch(patch_path)
        self.assertTrue(apply_result)

        final_path = os.path.join(self.repo_path, target_file)
        self.assertTrue(os.path.exists(final_path))
        with open(final_path, "r") as f:
            self.assertEqual(f.read().strip(), target_content)

        self.assertTrue(self.applier.verify_repository_state())

        self.applier.rollback(backup_tag)
        self.assertFalse(os.path.exists(final_path))

    def test_safe_apply_failure_and_rollback(self):
        backup_tag = f"backup_{uuid.uuid4().hex}"
        bad_patch_path = os.path.join(self.test_dir, "bad.patch")

        with open(bad_patch_path, "w") as f:
            f.write("INVALID PATCH CONTENT")

        with self.assertRaises(PatchApplierError):
            self.applier.safe_apply(bad_patch_path, backup_tag)

        cmd = ["git", "-C", self.repo_path, "branch"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertIn(backup_tag, res.stdout)

if __name__ == "__main__":
    unittest.main()