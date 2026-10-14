import unittest
import uuid
import random
import tempfile
import os
import subprocess
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser
from skills.hypothesis_generator import HypothesisGenerator, HypothesisGeneratorError

class TestHypothesisGeneratorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

        subprocess.run(["git", "init"], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo_path, capture_output=True, check=True)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_full_cycle_real_repo(self):
        unique_id = str(uuid.uuid4())[:8]
        component_name = f"comp_{unique_id}"
        error_sig = f"err_sig_{unique_id}"
        root_cause_text = f"cause_{random.randint(1000, 9999)}"
        lesson_text = f"fix_action_{random.randint(1000, 9999)}"

        commit_message = f"Fix issue\n\nfailure_signature: {error_sig}\ncomponent: {component_name}\nroot_cause: {root_cause_text}\nlesson: {lesson_text}"

        file_path = os.path.join(self.repo_path, "test_file.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"initial content {unique_id}\n")

        subprocess.run(["git", "add", "test_file.txt"], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_path, capture_output=True, check=True)

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"modified content {unique_id}\n")

        subprocess.run(["git", "add", "test_file.txt"], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", commit_message], cwd=self.repo_path, capture_output=True, check=True)

        git_inspector = GitInspector(self.repo_path)
        lesson_parser = LessonParser(git_inspector)
        generator = HypothesisGenerator(lesson_parser=lesson_parser, git_inspector=git_inspector)

        cycle_result = generator.run_cycle_analysis(max_commits=10)

        self.assertIn("patterns", cycle_result)
        self.assertIn("hypotheses", cycle_result)
        self.assertIn("recommendations", cycle_result)

        patterns = cycle_result["patterns"]
        self.assertIn(error_sig, patterns)
        self.assertEqual(patterns[error_sig]["component"], component_name)
        self.assertEqual(patterns[error_sig]["count"], 1)
        self.assertIn(root_cause_text, patterns[error_sig]["root_causes"])

        hypotheses = cycle_result["hypotheses"]
        found_hypothesis = next((h for h in hypotheses if h["pattern_id"] == error_sig), None)
        self.assertIsNotNone(found_hypothesis)
        self.assertEqual(found_hypothesis["component"], component_name)
        self.assertEqual(found_hypothesis["count"], 1)
        self.assertEqual(found_hypothesis["confidence"], 1.0)
        self.assertIn(root_cause_text, found_hypothesis["root_causes"])

        recommendations = cycle_result["recommendations"]
        found_rec = next((r for r in recommendations if error_sig in r and component_name in r), None)
        self.assertIsNotNone(found_rec)
        self.assertIn(root_cause_text, found_rec)
        self.assertIn(lesson_text, found_rec)

        commits = git_inspector.get_commit_history(max_count=1)
        self.assertTrue(len(commits) > 0)
        latest_hash = commits[0].get("hash") or commits[0].get("commit")

        if not latest_hash:
            res_log = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_path, capture_output=True, text=True, check=True)
            latest_hash = res_log.stdout.strip()

        context = generator.enrich_failure_context(latest_hash)
        self.assertEqual(context["commit_hash"], latest_hash)
        self.assertIn("diff", context)
        self.assertTrue(len(context["diff"]) > 0)

if __name__ == "__main__":
    unittest.main()