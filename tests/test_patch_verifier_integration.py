import unittest
import os
import tempfile
import shutil
import uuid
import random
import subprocess
from skills.patch_verifier import GitInspector, LessonParser, HypothesisGenerator, PatchExecutor, PatchVerifier

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "-C", self.test_dir, "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Test User"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "test@example.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.dummy_file = "README.md"
        full_path = os.path.join(self.test_dir, self.dummy_file)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("Initial commit")
            
        subprocess.run(["git", "-C", self.test_dir, "add", self.dummy_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.inspector = GitInspector(self.test_dir)
        self.parser = LessonParser(self.inspector)
        self.executor = PatchExecutor(self.test_dir, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.test_dir, self.inspector, self.executor)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_secure_patch_pipeline_integration(self):
        unique_id = str(uuid.uuid4())
        target_file = f"module_{random.randint(1000, 9999)}.py"
        random_content = f"# Generated content {unique_id}\nprint('Hello {unique_id}')"

        patch_data = {
            "file_path": target_file,
            "content": random_content,
            "commit_message": f"Add feature {unique_id}"
        }

        success = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(success, "Verifier should successfully verify and apply valid patch without syntax errors.")

        full_target_path = os.path.join(self.test_dir, target_file)
        self.assertTrue(os.path.exists(full_target_path), "Target file must be created on disk by the patch pipeline.")

        with open(full_target_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        self.assertEqual(file_content, random_content, "File content on disk must match the provided patch content.")

        history = self.inspector.get_commit_history(max_count=5)
        self.assertGreaterEqual(len(history), 2, "Git history should contain at least initial commit and the patch commit.")
        latest_commit = history[0]
        self.assertIn(unique_id, latest_commit["message"], "Latest commit message should reflect the applied patch data.")

    def test_patch_verifier_rejects_syntax_errors(self):
        unique_id = str(uuid.uuid4())
        target_file = f"faulty_{random.randint(1000, 9999)}.py"
        bad_content = f"syntax error here {unique_id}"

        patch_data = {
            "file_path": target_file,
            "content": bad_content,
            "commit_message": f"Attempting bad patch {unique_id}"
        }

        success = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(success, "Verifier must reject patches containing syntax error markers.")

        full_target_path = os.path.join(self.test_dir, target_file)
        self.assertFalse(os.path.exists(full_target_path), "Rejected patch must not leave files on disk.")

if __name__ == "__main__":
    unittest.main()