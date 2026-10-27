import unittest
import os
import subprocess
import tempfile
import uuid
import random
from skills.patch_verifier import (
    GitInspector,
    LessonParser,
    HypothesisGenerator,
    PatchExecutor,
    PatchVerifier,
    HypothesisGeneratorError,
    LessonParserError,
    PatchExecutorError
)

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        subprocess_run = subprocess.run(["git", "init", self.repo_path], capture_output=True, text=True)
        if subprocess_run.returncode != 0:
            subprocess.run(["git", "-C", self.repo_path, "init"], check=True)

        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Architect Test"], check=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "architect@test.com"], check=True)
        
        init_file = os.path.join(self.repo_path, "README.md")
        unique_content = f"Initial commit {uuid.uuid4()}"
        with open(init_file, "w", encoding="utf-8") as f:
            f.write(unique_content)
            
        subprocess.run(["git", "-C", self.repo_path, "add", "README.md"], check=True)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_pipeline_integration(self):
        inspector = GitInspector(self.repo_path)
        parser = LessonParser(inspector)
        generator = HypothesisGenerator(inspector, parser)
        executor = PatchExecutor(self.repo_path, inspector, parser)
        verifier = PatchVerifier(self.repo_path, inspector, executor)

        history = inspector.get_commit_history(max_count=5)
        self.assertTrue(len(history) > 0)
        self.assertEqual(history[0]["message"], "Initial commit")

        lessons = parser.parse_lessons()
        self.assertIsInstance(lessons, list)

        hypotheses = generator.generate_hypotheses()
        prioritized = generator.prioritize_hypotheses(hypotheses)
        self.assertIsInstance(prioritized, list)

        random_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        random_string = uuid.uuid4().hex
        patch_content = f"print('{random_string}')\n"
        commit_msg = f"Add feature {random_string}"

        patch_data = {
            "file_path": random_file_name,
            "content": patch_content,
            "commit_message": commit_msg
        }

        verification_result = verifier.verify_and_apply(patch_data)
        self.assertTrue(verification_result)

        full_target_path = os.path.join(self.repo_path, random_file_name)
        self.assertTrue(os.path.exists(full_target_path))

        with open(full_target_path, "r", encoding="utf-8") as f:
            read_data = f.read()
        self.assertEqual(read_data, patch_content)

        latest_changes = inspector.get_latest_changes()
        self.assertIn(random_string, latest_changes)

        bad_file_name = f"bad_{uuid.uuid4().hex[:8]}.py"
        bad_patch_data = {
            "file_path": bad_file_name,
            "content": "syntax error here: invalid python syntax",
            "commit_message": "Bad patch"
        }

        bad_verification_result = verifier.verify_and_apply(bad_patch_data)
        self.assertFalse(bad_verification_result)
        self.assertFalse(os.path.exists(os.path.join(self.repo_path, bad_file_name)))

if __name__ == "__main__":
    unittest.main()