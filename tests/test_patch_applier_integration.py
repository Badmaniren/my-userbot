import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.patch_applier import PatchApplier, apply_patch, PatchApplierError
from skills.git_inspector import GitInspector

class TestPatchApplierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess_init = ["git", "init", self.test_dir]
        import subprocess
        subprocess.run(subprocess_init, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        subprocess_config = ["git", "-C", self.test_dir, "config", "user.email", "test@architect.local"]
        subprocess.run(subprocess_config, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess_config_name = ["git", "-C", self.test_dir, "config", "user.name", "Architect Test"]
        subprocess.run(subprocess_config_name, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.initial_file = "README.md"
        self.initial_path = os.path.join(self.test_dir, self.initial_file)
        with open(self.initial_path, "w", encoding="utf-8") as f:
            f.write("# Initial Repository\n")

        subprocess.run(["git", "-C", self.test_dir, "add", self.initial_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_patch_applier_full_integration_workflow(self):
        applier = PatchApplier(self.test_dir)
        inspector = GitInspector(self.test_dir)

        random_suffix = uuid.uuid4().hex[:8]
        target_filename = f"module_{random_suffix}.py"
        random_content = f"# Random generated payload: {uuid.uuid4()}\nVALUE = {random.randint(1000, 9999)}\n"
        backup_tag_name = f"backup_tag_{uuid.uuid4().hex[:6]}"

        patch_data = {
            "file_path": target_filename,
            "content": random_content,
            "backup_id": backup_tag_name
        }

        success = apply_patch(self.test_dir, patch_data)
        self.assertTrue(success)

        target_full_path = os.path.join(self.test_dir, target_filename)
        self.assertTrue(os.path.exists(target_full_path))

        with open(target_full_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        self.assertEqual(written_content, random_content)

        history = inspector.get_commit_history(max_count=5)
        self.assertTrue(any("Apply patch via PatchApplier" in commit.get("message", "") for commit in history))

        rollback_tag = f"rollback_{uuid.uuid4().hex[:6]}"
        applier.create_recovery_point(rollback_tag)

        bad_filename = f"corrupt_{uuid.uuid4().hex[:8]}.py"
        bad_full_path = os.path.join(self.test_dir, bad_filename)
        with open(bad_full_path, "w", encoding="utf-8") as f:
            f.write("CORRUPTED DATA STREAM")

        with self.assertRaises(PatchApplierError):
            applier.verify_repository_state()

        applier.rollback(rollback_tag)
        applier.verify_repository_state()
        self.assertFalse(os.path.exists(bad_full_path))

if __name__ == "__main__":
    unittest.main()