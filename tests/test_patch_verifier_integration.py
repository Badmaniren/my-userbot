import unittest
import os
import tempfile
import shutil
import uuid
import random
import subprocess

from skills.patch_verifier import PatchVerifier
from skills.patch_sanitizer import PatchSanitizer
from skills.patch_executor import PatchExecutor
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess_result = subprocess.run(
            ["git", "init", self.test_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        subprocess.run(
            ["git", "-C", self.test_dir, "config", "user.name", "Test User"],
            check=True
        )
        subprocess.run(
            ["git", "-C", self.test_dir, "config", "user.email", "test@example.com"],
            check=True
        )
        
        self.inspector = GitInspector(self.test_dir)
        self.parser = LessonParser(self.inspector)
        self.executor = PatchExecutor(self.test_dir, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.test_dir, self.inspector, self.executor)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_verify_and_apply_integration(self):
        unique_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        unique_content_string = f"print('{uuid.uuid4()}')"
        unique_commit_msg = f"Commit {uuid.uuid4().hex[:6]}"

        patch_data = {
            "file_path": unique_file_name,
            "content": unique_content_string,
            "commit_message": unique_commit_msg
        }

        result = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(result)

        full_path = os.path.join(self.test_dir, unique_file_name)
        self.assertTrue(os.path.exists(full_path))

        with open(full_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        
        self.assertIn(unique_content_string, written_content)

        history = self.inspector.get_commit_history(max_count=1)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["message"], unique_commit_msg)

if __name__ == "__main__":
    unittest.main()
