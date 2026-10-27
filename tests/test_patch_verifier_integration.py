import unittest
import tempfile
import shutil
import os
import uuid
import random
import subprocess
from skills.patch_verifier import GitInspector, LessonParser, PatchExecutor, PatchVerifier

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "init", self.test_dir], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Test User"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "test@example.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.initial_file = "README.md"
        self.initial_content = f"Initial content {uuid.uuid4()}"
        initial_path = os.path.join(self.test_dir, self.initial_file)
        with open(initial_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)
        
        subprocess.run(["git", "-C", self.test_dir, "add", self.initial_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.inspector = GitInspector(self.test_dir)
        self.parser = LessonParser(self.inspector)
        self.executor = PatchExecutor(self.test_dir, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.test_dir, self.inspector, self.executor)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_verify_and_apply_integration_success(self):
        target_file = f"module_{uuid.uuid4().hex[:8]}.py"
        random_payload = f"print('Hello {uuid.uuid4()}')"
        commit_msg = f"Add feature {uuid.uuid4().hex[:6]}"

        patch_data = {
            "file_path": target_file,
            "content": random_payload,
            "commit_message": commit_msg
        }

        result = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(result)

        full_path = os.path.join(self.test_dir, target_file)
        self.assertTrue(os.path.exists(full_path))
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, random_payload)

        history = self.inspector.get_commit_history(max_count=1)
        self.assertTrue(len(history) > 0)
        self.assertEqual(history[0]["message"], commit_msg)

    def test_verify_and_apply_integration_failure_syntax(self):
        target_file = f"module_{uuid.uuid4().hex[:8]}.py"
        random_payload = f"syntax error here {uuid.uuid4()}"
        commit_msg = f"Bad commit {uuid.uuid4().hex[:6]}"
        
        patch_data = {
            "file_path": target_file,
            "content": random_payload,
            "commit_message": commit_msg
        }

        result = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(result)

        full_path = os.path.join(self.test_dir, target_file)
        self.assertFalse(os.path.exists(full_path))

if __name__ == "__main__":
    unittest.main()