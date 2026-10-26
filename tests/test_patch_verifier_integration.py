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
        
        subprocess.run(["git", "-C", self.repo_path, "init"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "test@example.com"], check=True)
        
        self.inspector = GitInspector(self.repo_path)
        self.parser = LessonParser(self.inspector)
        self.executor = PatchExecutor(self.repo_path, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.repo_path, self.inspector, self.executor)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_verify_and_apply_integration(self):
        random_filename = f"test_file_{uuid.uuid4().hex}.py"
        random_content = f"print('{uuid.uuid4()}')\n"
        commit_msg = f"Add {random_filename} with id {uuid.uuid4()}"

        patch_data = {
            "file_path": random_filename,
            "content": random_content,
            "commit_message": commit_msg
        }

        result = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(result)

        full_path = os.path.join(self.repo_path, random_filename)
        self.assertTrue(os.path.exists(full_path))

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, random_content)

        history = self.inspector.get_commit_history(max_count=1)
        self.assertTrue(len(history) > 0)
        self.assertEqual(history[0]["message"], commit_msg)

    def test_verify_and_apply_syntax_error(self):
        random_filename = f"error_file_{uuid.uuid4().hex}.py"
        random_content = f"syntax error here {uuid.uuid4()}"
        
        patch_data = {
            "file_path": random_filename,
            "content": random_content,
            "commit_message": "Should fail"
        }

        result = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(result)

        full_path = os.path.join(self.repo_path, random_filename)
        self.assertFalse(os.path.exists(full_path))

if __name__ == "__main__":
    unittest.main()