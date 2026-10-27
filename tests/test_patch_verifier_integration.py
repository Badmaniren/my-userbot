import unittest
import tempfile
import shutil
import os
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
        
        subprocess.run(["git", "-C", self.test_dir, "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Architect Test"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "architect@test.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.initial_file = "init_file.txt"
        self.initial_path = os.path.join(self.test_dir, self.initial_file)
        with open(self.initial_path, "w", encoding="utf-8") as f:
            f.write("Initial repository state")
            
        subprocess.run(["git", "-C", self.test_dir, "add", self.initial_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.inspector = GitInspector(self.test_dir)
        self.parser = LessonParser(self.inspector)
        self.generator = HypothesisGenerator(self.inspector, self.parser)
        self.executor = PatchExecutor(self.test_dir, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.test_dir, self.inspector, self.executor)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_full_patch_pipeline_integration(self):
        unique_id = str(uuid.uuid4())
        target_file = f"module_{random.randint(1000, 9999)}.py"
        random_content = f"# Generated content {unique_id}\nprint('Hello, Integration!')"
        commit_msg = f"Add feature {unique_id}"

        patch_data = {
            "file_path": target_file,
            "content": random_content,
            "commit_message": commit_msg
        }

        verified_result = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(verified_result, "Patch verification and application pipeline failed.")

        full_target_path = os.path.join(self.test_dir, target_file)
        self.assertTrue(os.path.exists(full_target_path), "File was not created on disk by the pipeline.")

        with open(full_target_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        self.assertEqual(written_content, random_content, "Content written to disk does not match expected random content.")

        history = self.inspector.get_commit_history(max_count=5)
        self.assertGreaterEqual(len(history), 2, "Commit history is missing the patch commit.")
        latest_commit = history[0]
        self.assertEqual(latest_commit["message"], commit_msg, "Latest commit message does not match.")

        file_diff = self.inspector.get_file_diff(latest_commit["hash"])
        self.assertIn(unique_id, file_diff, "Git diff does not contain the unique patch identifier.")

        hypotheses = self.generator.generate_hypotheses()
        prioritized = self.generator.prioritize_hypotheses(hypotheses)
        self.assertIsInstance(prioritized, list, "Hypothesis generation or prioritization failed.")

    def test_syntax_error_rejection_integration(self):
        target_file = f"broken_{random.randint(1000, 9999)}.py"
        bad_content = "syntax error here: invalid python syntax = True"

        patch_data = {
            "file_path": target_file,
            "content": bad_content,
            "commit_message": "Add broken code"
        }

        verified_result = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(verified_result, "Patch with syntax error should have been rejected by verifier.")

        full_target_path = os.path.join(self.test_dir, target_file)
        self.assertFalse(os.path.exists(full_target_path), "Rejected patch file should not exist on disk.")

if __name__ == "__main__":
    unittest.main()