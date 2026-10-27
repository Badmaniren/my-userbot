import os
import subprocess
import tempfile
import unittest
import uuid
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
        
        subprocess.run(["git", "init", self.repo_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Test User"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "test@example.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        init_file = os.path.join(self.repo_path, "README.md")
        with open(init_file, "w", encoding="utf-8") as f:
            f.write("Initial commit")
            
        subprocess.run(["git", "-C", self.repo_path, "add", "README.md"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.inspector = GitInspector(self.repo_path)
        self.parser = LessonParser(self.inspector)
        self.executor = PatchExecutor(self.repo_path, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.repo_path, self.inspector, self.executor)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_patch_verifier_integration_success_and_failure(self):
        unique_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        unique_content = f"print('{uuid.uuid4().hex}')\n"
        commit_msg = f"Add feature {uuid.uuid4().hex[:6]}"

        patch_data = {
            "file_path": unique_file_name,
            "content": unique_content,
            "commit_message": commit_msg
        }

        result = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(result, "Verifier should successfully verify and apply valid patch")

        full_file_path = os.path.join(self.repo_path, unique_file_name)
        self.assertTrue(os.path.exists(full_file_path), "Patched file must physically exist in the repository")

        with open(full_file_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        self.assertEqual(written_content, unique_content, "Content of the written file must match patch content")

        history = self.inspector.get_commit_history(max_count=2)
        found_commit = any(commit["message"] == commit_msg for commit in history)
        self.assertTrue(found_commit, "Commit history must contain the message from the applied patch")

        invalid_file_name = f"broken_{uuid.uuid4().hex[:8]}.py"
        invalid_patch_data = {
            "file_path": invalid_file_name,
            "content": "syntax error here",
            "commit_message": "Should fail"
        }

        invalid_result = self.verifier.verify_and_apply(invalid_patch_data)
        self.assertFalse(invalid_result, "Verifier must reject patches containing syntax error markers")

        invalid_full_path = os.path.join(self.repo_path, invalid_file_name)
        self.assertFalse(os.path.exists(invalid_full_path), "Rejected patch file must not be committed or permanently stored")

if __name__ == "__main__":
    unittest.main()