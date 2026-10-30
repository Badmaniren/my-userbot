import unittest
import tempfile
import shutil
import os
import uuid
import random
import subprocess
from skills.patch_applier import PatchApplier, apply_patch, PatchApplierError
from skills.git_inspector import GitInspector


class TestPatchApplierIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        subprocess.run(["git", "init", self.test_dir], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Architect Bot"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "architect@bot.local"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.initial_file = os.path.join(self.test_dir, "README.md")
        self.rand_content = f"Initial state: {uuid.uuid4()}"
        self.initial_file_content = self.rand_content
        with open(self.initial_file, "w", encoding="utf-8") as f:
            f.write(self.rand_content)
            
        subprocess.run(["git", "-C", self.test_dir, "add", "README.md"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_patch_applier_and_git_inspector_integration(self):
        backup_tag = f"backup_{uuid.uuid4().hex[:8]}"
        target_filename = f"module_{random.randint(1000, 9999)}.py"
        file_content = f"# Generated code uuid: {uuid.uuid4()}\nprint('OK')"
        
        patch_payload = {
            "file_path": target_filename,
            "content": file_content,
            "backup_id": backup_tag
        }

        success = apply_patch(self.test_dir, patch_payload)
        self.assertTrue(success)

        inspector = GitInspector(self.test_dir)
        history = inspector.get_commit_history(max_count=5)
        
        found_commit = False
        for commit in history:
            if "Apply patch via PatchApplier" in commit.get("message", ""):
                found_commit = True
                break
        self.assertTrue(found_commit, "Commit from apply_patch not found via GitInspector")

        full_target_path = os.path.join(self.test_dir, target_filename)
        self.assertTrue(os.path.exists(full_target_path))
        with open(full_target_path, "r", encoding="utf-8") as f:
            read_data = f.read()
        self.assertEqual(read_data, file_content)

        applier = PatchApplier(self.test_dir)
        rollback_tag = f"rollback_{uuid.uuid4().hex[:8]}"
        applier.create_recovery_point(rollback_tag)

        bad_filename = f"bad_{uuid.uuid4().hex[:8]}.py"
        bad_payload = {
            "file_path": bad_filename,
            "content": "syntax error here =",
            "backup_id": rollback_tag
        }
        
        apply_patch(self.test_dir, bad_payload)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, bad_filename)))

        applier.rollback(rollback_tag)
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, bad_filename)))
        applier.verify_repository_state()


if __name__ == "__main__":
    unittest.main()