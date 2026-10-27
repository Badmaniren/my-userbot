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
        subprocess.run(["git", "-C", self.test_dir, "init"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Architect"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "architect@test.com"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        init_file = os.path.join(self.test_dir, "README.md")
        with open(init_file, "w", encoding="utf-8") as f:
            f.write("Initial commit")
        subprocess.run(["git", "-C", self.test_dir, "add", "README.md"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        self.inspector = GitInspector(self.test_dir)
        self.parser = LessonParser(self.inspector)
        self.executor = PatchExecutor(self.test_dir, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.test_dir, self.inspector, self.executor)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_verify_and_apply_integration(self):
        unique_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        random_content = f"# Generated content {uuid.uuid4()}"
        random_commit_msg = f"Add feature {random.randint(1000, 9999)}"

        patch_data = {
            "file_path": unique_file_name,
            "content": random_content,
            "commit_message": random_commit_msg
        }

        result = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(result)

        full_path = os.path.join(self.test_dir, unique_file_name)
        self.assertTrue(os.path.exists(full_path))

        with open(full_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, random_content)

        history = self.inspector.get_commit_history(max_count=1)
        self.assertTrue(len(history) > 0)
        self.assertEqual(history[0]["message"], random_commit_msg)

    def test_verify_and_apply_with_syntax_error(self):
        unique_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        random_content = f"print('syntax error here') # {uuid.uuid4()}"

        patch_data = {
            "file_path": unique_file_name,
            "content": random_content,
            "commit_message": "Should fail"
        }

        result = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(result)

        full_path = os.path.join(self.test_dir, unique_file_name)
        self.assertFalse(os.path.exists(full_path))

if __name__ == "__main__":
    unittest.main()