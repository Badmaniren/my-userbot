import os
import shutil
import subprocess
import tempfile
import unittest
import uuid
from skills.patch_applier import PatchApplier, PatchApplierError, apply_patch
from skills.git_inspector import GitInspector


class TestPatchApplierIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "-C", self.test_dir, "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Test Architect"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "architect@test.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.initial_file = "README.md"
        self.initial_content = f"Initial state: {uuid.uuid4()}\n"
        full_path = os.path.join(self.test_dir, self.initial_file)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)
            
        subprocess.run(["git", "-C", self.test_dir, "add", self.initial_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_integration_apply_patch_dictionary_flow(self):
        unique_file = f"module_{uuid.uuid4().hex[:8]}.py"
        unique_content = f"print('{uuid.uuid4()}')\n"
        backup_id = f"backup_{uuid.uuid4().hex[:8]}"

        patch_data = {
            "file_path": unique_file,
            "content": unique_content,
            "backup_id": backup_id
        }

        result = apply_patch(self.test_dir, patch_data)
        self.assertTrue(result)

        target_file_path = os.path.join(self.test_dir, unique_file)
        self.assertTrue(os.path.exists(target_file_path))

        with open(target_file_path, "r", encoding="utf-8") as f:
            read_data = f.read()
        self.assertEqual(read_data, unique_content)

        inspector = GitInspector(self.test_dir)
        history = inspector.get_commit_history(max_count=2)
        self.assertGreaterEqual(len(history), 1)

    def test_integration_safe_apply_and_rollback_on_error(self):
        applier = PatchApplier(self.test_dir)
        backup_tag = f"tag_{uuid.uuid4().hex[:8]}"
        
        non_existent_patch = os.path.join(self.test_dir, f"missing_{uuid.uuid4().hex}.patch")

        with self.assertRaises((PatchApplierError, FileNotFoundError, Exception)):
            applier.safe_apply(non_existent_patch, backup_tag)

        cmd = ["git", "-C", self.test_dir, "branch", "--list", backup_tag]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        inspector = GitInspector(self.test_dir)
        latest_changes = inspector.get_latest_changes()
        self.assertIsNotNone(latest_changes)


if __name__ == "__main__":
    unittest.main()