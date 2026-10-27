import unittest
import tempfile
import os
import shutil
import subprocess
import uuid
import random

from skills.patch_verifier import (
    GitInspector,
    LessonParser,
    HypothesisGenerator,
    PatchExecutor,
    PatchVerifier
)

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "-C", self.test_dir, "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Architect"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "architect@system.local"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Initial commit to have a valid HEAD
        self.initial_file = "README.md"
        initial_path = os.path.join(self.test_dir, self.initial_file)
        with open(initial_path, "w", encoding="utf-8") as f:
            f.write("Initial state\n")
        
        subprocess.run(["git", "-C", self.test_dir, "add", self.initial_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.inspector = GitInspector(self.test_dir)
        self.parser = LessonParser(self.inspector)
        self.hypothesis_gen = HypothesisGenerator(self.inspector, self.parser)
        self.executor = PatchExecutor(self.test_dir, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.test_dir, self.inspector, self.executor)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_patch_verifier_pipeline_integration(self):
        unique_id = str(uuid.uuid4())
        target_file = f"module_{random.randint(1000, 9999)}.py"
        file_content = f"# Generated content {unique_id}\ndef foo():\n    return '{unique_id}'\n"
        commit_msg = f"Add feature {unique_id}"

        patch_data = {
            "file_path": target_file,
            "content": file_content,
            "commit_message": commit_msg
        }

        # Verify and apply valid patch
        success = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(success, "PatchVerifier should successfully verify and apply a clean patch.")

        # Real checks on repository and filesystem
        full_target_path = os.path.join(self.test_dir, target_file)
        self.assertTrue(os.path.exists(full_target_path), "The file should physically exist in the repo directory.")

        with open(full_target_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, file_content, "The file content on disk must match the applied patch content.")

        history = self.inspector.get_commit_history(max_count=5)
        self.assertGreaterEqual(len(history), 2, "Commit history should contain at least initial commit and patch commit.")
        latest_commit = history[0]
        self.assertEqual(latest_commit["message"], commit_msg, "Latest commit message must match the patch commit message.")

        # Test invalid patch verification (syntax error injection simulation)
        bad_target_file = f"bad_{random.randint(1000, 9999)}.py"
        bad_patch_data = {
            "file_path": bad_target_file,
            "content": "syntax error here\n",
            "commit_message": "Bad patch"
        }

        bad_success = self.verifier.verify_and_apply(bad_patch_data)
        self.assertFalse(bad_success, "PatchVerifier must reject patches containing simulated syntax errors.")

        bad_full_path = os.path.join(self.test_dir, bad_target_file)
        self.assertFalse(os.path.exists(bad_full_path), "Rejected patch file should not be persisted or committed.")

if __name__ == "__main__":
    unittest.main()