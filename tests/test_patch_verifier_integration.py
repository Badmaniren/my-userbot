import unittest
import tempfile
import os
import subprocess
import uuid
import random
from skills.patch_verifier import (
    GitInspector,
    LessonParser,
    PatchExecutor,
    PatchVerifier,
    PatchExecutorError
)

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        subprocess.run(["git", "-C", self.repo_path, "init", "-b", "main"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Architect Test"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "architect@test.com"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        self.inspector = GitInspector(self.repo_path)
        self.parser = LessonParser(self.inspector)
        self.executor = PatchExecutor(self.repo_path, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.repo_path, self.inspector, self.executor)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_patch_verifier_workflow(self):
        file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        random_content = f"print('Hello, Architect! {random.randint(1000, 9999)}')\n"
        commit_msg = f"Add feature {uuid.uuid4().hex[:6]}"

        patch_data = {
            "file_path": file_name,
            "content": random_content,
            "commit_message": commit_msg
        }

        success = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(success, "Verifier should successfully verify and apply valid patch.")

        full_file_path = os.path.join(self.repo_path, file_name)
        self.assertTrue(os.path.exists(full_file_path), "Target file must be created on disk.")

        with open(full_file_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        self.assertEqual(written_content, random_content, "Content written to file must match patch content.")

        history = self.inspector.get_commit_history(max_count=1)
        self.assertTrue(len(history) > 0, "Git commit history should contain at least one commit.")
        self.assertEqual(history[0]["message"], commit_msg, "Commit message in git history must match patch specification.")

    def test_integration_patch_verifier_syntax_rejection(self):
        file_name = f"broken_{uuid.uuid4().hex[:8]}.py"
        patch_data = {
            "file_path": file_name,
            "content": "syntax error here = True",
            "commit_message": "Break code"
        }

        success = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(success, "Verifier must reject patches containing simulated syntax errors.")

        full_file_path = os.path.join(self.repo_path, file_name)
        self.assertFalse(os.path.exists(full_file_path), "Rejected patch file should not be created or committed.")

if __name__ == "__main__":
    unittest.main()