import unittest
import os
import subprocess
import tempfile
import uuid
import random
from skills.patch_verifier import GitInspector, LessonParser, PatchExecutor, PatchVerifier

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        subprocess_run = subprocess.run(["git", "init", self.repo_path], capture_output=True, text=True)
        if subprocess_run.returncode != 0:
            subprocess.run(["git", "-C", self.repo_path, "init", "-b", "main"], capture_output=True, text=True)
        
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Architect"], check=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "architect@example.com"], check=True)

        dummy_file = os.path.join(self.repo_path, "README.md")
        with open(dummy_file, "w", encoding="utf-8") as f:
            f.write("Initial commit")
        subprocess.run(["git", "-C", self.repo_path, "add", "README.md"], check=True)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True)

        self.inspector = GitInspector(self.repo_path)
        self.parser = LessonParser(self.inspector)
        self.executor = PatchExecutor(self.repo_path, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.repo_path, self.inspector, self.executor)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_patch_verifier_pipeline(self):
        unique_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        random_content = f"# Random payload: {uuid.uuid4()}\nprint({random.randint(1000, 9999)})"
        commit_msg = f"Feature commit {uuid.uuid4().hex[:6]}"

        patch_data = {
            "file_path": unique_file_name,
            "content": random_content,
            "commit_message": commit_msg
        }

        is_verified = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(is_verified, "PatchVerifier should successfully verify and apply valid patch.")

        full_file_path = os.path.join(self.repo_path, unique_file_name)
        self.assertTrue(os.path.exists(full_file_path), "Target file must be created on disk.")

        with open(full_file_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        self.assertEqual(written_content, random_content, "Content written to file must match input patch content.")

        history = self.inspector.get_commit_history(max_count=5)
        self.assertGreaterEqual(len(history), 2, "Git history should contain at least initial commit and patch commit.")
        
        latest_commit = history[0]
        self.assertEqual(latest_commit["message"], commit_msg, "Latest commit message must match patch commit message.")

        invalid_patch_data = {
            "file_path": f"bad_{uuid.uuid4().hex[:8]}.py",
            "content": "syntax error here and fail",
            "commit_message": "Should fail verification"
        }

        is_invalid_verified = self.verifier.verify_and_apply(invalid_patch_data)
        self.assertFalse(is_invalid_verified, "PatchVerifier must reject patches containing syntax errors.")

        bad_file_path = os.path.join(self.repo_path, invalid_patch_data["file_path"])
        self.assertFalse(os.path.exists(bad_file_path), "Rejected patch file must not be committed or remain.")

if __name__ == "__main__":
    unittest.main()