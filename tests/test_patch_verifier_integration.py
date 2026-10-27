import unittest
import tempfile
import os
import shutil
import uuid
import random
import subprocess
from skills.patch_verifier import GitInspector, LessonParser, PatchExecutor, PatchVerifier

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess_result = subprocess.run(["git", "init", self.test_dir], capture_output=True, text=True)
        if subprocess_result.returncode != 0:
            # Fallback for git config user if needed in test env
            pass
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "test@example.com"], check=True)
        
        # Create initial commit so git log works
        self.init_file = "README.md"
        self.init_path = os.path.join(self.test_dir, self.init_file)
        with open(self.init_path, "w", encoding="utf-8") as f:
            f.write("Initial state")
        subprocess.run(["git", "-C", self.test_dir, "add", self.init_file], check=True)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True)

        self.inspector = GitInspector(self.test_dir)
        self.parser = LessonParser(self.inspector)
        self.executor = PatchExecutor(self.test_dir, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.test_dir, self.inspector, self.executor)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_patch_verifier_integration_flow(self):
        unique_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        unique_content = f"# Valid content {uuid.uuid4()}\nprint('{random.randint(1000, 9999)}')\n"
        commit_msg = f"Add feature {uuid.uuid4().hex[:6]}"

        patch_data = {
            "file_path": unique_file_name,
            "content": unique_content,
            "commit_message": commit_msg
        }

        # Verify and apply valid patch
        success = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(success, "Valid patch should be verified and applied successfully.")

        # Check real filesystem changes
        target_path = os.path.join(self.test_dir, unique_file_name)
        self.assertTrue(os.path.exists(target_path), "Target file must exist on disk after application.")
        with open(target_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, unique_content, "Content on disk must match patch content.")

        # Check real git history integration
        history = self.inspector.get_commit_history(max_count=5)
        self.assertGreaterEqual(len(history), 2, "Git history should contain initial commit and patch commit.")
        latest_commit = history[0]
        self.assertEqual(latest_commit["message"], commit_msg, "Latest commit message should match.")

        # Verify failing patch with syntax error simulation
        bad_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        bad_patch_data = {
            "file_path": bad_file_name,
            "content": "syntax error here: invalid python code",
            "commit_message": "Bad commit"
        }

        fail_success = self.verifier.verify_and_apply(bad_patch_data)
        self.assertFalse(fail_success, "Patch containing 'syntax error here' must be rejected by verifier.")

        bad_target_path = os.path.join(self.test_dir, bad_file_name)
        self.assertFalse(os.path.exists(bad_target_path), "Rejected patch file should not be committed/created.")

if __name__ == "__main__":
    unittest.main()