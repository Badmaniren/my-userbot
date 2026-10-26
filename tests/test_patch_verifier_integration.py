import unittest
import tempfile
import os
import shutil
import subprocess
import uuid
import random
from skills.patch_verifier import GitInspector, LessonParser, PatchExecutor, PatchVerifier

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "init", self.test_dir], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "test@example.com"], check=True)
        
        self.init_file = "README.md"
        init_path = os.path.join(self.test_dir, self.init_file)
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("Initial commit")
        subprocess.run(["git", "-C", self.test_dir, "add", self.init_file], check=True)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_patch_verifier_integration_pipeline(self):
        inspector = GitInspector(self.test_dir)
        parser = LessonParser(inspector)
        executor = PatchExecutor(self.test_dir, inspector, parser)
        verifier = PatchVerifier(self.test_dir, inspector, executor)

        unique_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        random_content = f"# Generated content {uuid.uuid4()}\nvalue = {random.randint(1, 1000)}"
        commit_msg = f"Add feature {uuid.uuid4().hex[:6]}"

        patch_data = {
            "file_path": unique_file_name,
            "content": random_content,
            "commit_message": commit_msg
        }

        result = verifier.verify_and_apply(patch_data)
        self.assertTrue(result, "Patch verification and application should succeed for valid content.")

        target_file_path = os.path.join(self.test_dir, unique_file_name)
        self.assertTrue(os.path.exists(target_file_path), "The patched file must exist on disk.")

        with open(target_file_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, random_content, "The content written to the file must match the patch data.")

        history = inspector.get_commit_history(max_count=2)
        self.assertTrue(len(history) >= 2, "Git history should contain at least the initial commit and the patch commit.")
        latest_commit = history[0]
        self.assertEqual(latest_commit["message"], commit_msg, "The latest commit message must match the patch commit message.")

        syntax_error_patch = {
            "file_path": unique_file_name,
            "content": "syntax error here",
            "commit_message": "Bad patch"
        }
        fail_result = verifier.verify_and_apply(syntax_error_patch)
        self.assertFalse(fail_result, "Patch verification must fail if content contains syntax error marker.")