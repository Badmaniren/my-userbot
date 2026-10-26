import unittest
import os
import tempfile
import shutil
import uuid
import random
import subprocess
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
        subprocess.run(["git", "-C", self.test_dir, "init"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "test@example.com"], check=True)
        
        self.inspector = GitInspector(self.test_dir)
        self.parser = LessonParser(self.inspector)
        self.generator = HypothesisGenerator(self.inspector, self.parser)
        self.executor = PatchExecutor(self.test_dir, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.test_dir, self.inspector, self.executor)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_integration_patch_verification_and_execution(self):
        unique_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        random_content = f"# Random payload {uuid.uuid4()}\nprint('{random.randint(1000, 9999)}')\n"
        random_commit_msg = f"Commit message {uuid.uuid4().hex[:6]}"

        patch_data = {
            "file_path": unique_file_name,
            "content": random_content,
            "commit_message": random_commit_msg
        }

        is_verified = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(is_verified, "Patch verification and application should succeed.")

        full_file_path = os.path.join(self.test_dir, unique_file_name)
        self.assertTrue(os.path.exists(full_file_path), "The patched file must exist on disk.")

        with open(full_file_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        self.assertEqual(written_content, random_content, "Content written to file must match patch data.")

        history = self.inspector.get_commit_history(max_count=1)
        self.assertTrue(len(history) > 0, "Git history should contain at least one commit.")
        latest_commit = history[0]
        self.assertEqual(latest_commit["message"], random_commit_msg, "Latest git commit message must match.")

    def test_integration_patch_syntax_error_rejection(self):
        unique_file_name = f"error_module_{uuid.uuid4().hex[:8]}.py"
        bad_content = f"syntax error here {uuid.uuid4()}"

        patch_data = {
            "file_path": unique_file_name,
            "content": bad_content,
            "commit_message": "Bad patch"
        }

        is_verified = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(is_verified, "Patch with syntax error trigger must be rejected.")

        full_file_path = os.path.join(self.test_dir, unique_file_name)
        self.assertFalse(os.path.exists(full_file_path), "Rejected patch file should not be created.")

    def test_integration_hypothesis_and_execution_chain(self):
        hypotheses = self.generator.generate_hypotheses()
        self.assertIsInstance(hypotheses, list)
        prioritized = self.generator.prioritize_hypotheses(hypotheses)
        self.assertIsInstance(prioritized, list)

        execution_result = self.executor.execute_from_lessons()
        self.assertIsInstance(execution_result, dict)
        self.assertIn("status", execution_result)

if __name__ == "__main__":
    unittest.main()