import unittest
import tempfile
import shutil
import os
import uuid
import random
import subprocess
from skills.patch_verifier import GitInspector, LessonParser, HypothesisGenerator, PatchExecutor, PatchVerifier

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "init", self.test_dir], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "test@example.com"], check=True)

        self.initial_file = "README.md"
        initial_path = os.path.join(self.test_dir, self.initial_file)
        with open(initial_path, "w", encoding="utf-8") as f:
            f.write("# Initial Repository\n")

        subprocess.run(["git", "-C", self.test_dir, "add", self.initial_file], check=True)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_patch_verification_pipeline_integration(self):
        inspector = GitInspector(self.test_dir)
        parser = LessonParser(inspector)
        generator = HypothesisGenerator(inspector, parser)
        executor = PatchExecutor(self.test_dir, inspector, parser)
        verifier = PatchVerifier(self.test_dir, inspector, executor)

        history = inspector.get_commit_history()
        self.assertTrue(len(history) > 0)

        lessons = parser.parse_lessons()
        self.assertIsInstance(lessons, list)

        hypotheses = generator.generate_hypotheses()
        prioritized = generator.prioritize_hypotheses(hypotheses)
        self.assertIsInstance(prioritized, list)

        unique_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        random_content = f"# Random content {uuid.uuid4()}\nprint('{random.randint(1000, 9999)}')\n"
        commit_message = f"Feature update {uuid.uuid4().hex[:6]}"

        patch_data = {
            "file_path": unique_file_name,
            "content": random_content,
            "commit_message": commit_message
        }

        is_verified = verifier.verify_and_apply(patch_data)
        self.assertTrue(is_verified)

        full_file_path = os.path.join(self.test_dir, unique_file_name)
        self.assertTrue(os.path.exists(full_file_path))

        with open(full_file_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, random_content)

        latest_changes = inspector.get_latest_changes()
        self.assertIn(commit_message, latest_changes)

        bad_patch_data = {
            "file_path": f"bad_{uuid.uuid4().hex[:8]}.py",
            "content": "syntax error here",
            "commit_message": "Bad patch"
        }
        is_bad_verified = verifier.verify_and_apply(bad_patch_data)
        self.assertFalse(is_bad_verified)

if __name__ == "__main__":
    unittest.main()