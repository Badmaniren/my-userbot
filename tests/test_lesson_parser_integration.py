import unittest
import uuid
import random
import tempfile
import os
import subprocess
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser


class TestLessonParserIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

        subprocess.run(["git", "init", self.repo_path], check=True, capture_output=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Architect"], check=True, capture_output=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "architect@test.com"], check=True, capture_output=True)

        self.unique_id = str(uuid.uuid4())
        self.error_code = f"ANTICHEAT_VIOLATION_{random.randint(1000, 9999)}"
        self.file_name = f"lesson_{self.unique_id}.txt"
        self.file_path = os.path.join(self.repo_path, self.file_name)

        content = (
            f"Failure history: Failed to load module {self.unique_id}\n"
            f"Fix applied: fixed memory leak in {self.unique_id}\n"
            f"Anticheat error: '{self.error_code}'\n"
        )

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(content)

        subprocess.run(["git", "-C", self.repo_path, "add", self.file_name], check=True, capture_output=True)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", f"Initial commit {self.unique_id}"], check=True, capture_output=True)

        fix_commit_msg = f"fix: resolve issue with {self.unique_id}"
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write("Additional patch data\n")

        subprocess.run(["git", "-C", self.repo_path, "add", self.file_name], check=True, capture_output=True)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", fix_commit_msg], check=True, capture_output=True)

        self.inspector = GitInspector(self.repo_path)
        self.parser = LessonParser(self.inspector)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_extract_failure_history(self):
        history = self.parser.extract_failure_history(max_commits=5)
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 2)

        found_unique_commit = False
        for commit in history:
            self.assertIn('commit_hash', commit)
            self.assertIn('message', commit)
            self.assertIn('diff', commit)
            if self.unique_id in commit['message']:
                found_unique_commit = True
        self.assertTrue(found_unique_commit, "Commit with unique ID must be present in failure history")

    def test_integration_parse_anticheat_errors(self):
        commits = self.inspector.get_commit_history(max_count=1)
        latest_hash = commits[0]['hash']

        errors = self.parser.parse_anticheat_errors(latest_hash, self.file_name)
        self.assertIsInstance(errors, list)
        self.assertIn(self.error_code, errors)

    def test_integration_get_fix_commits(self):
        fixes = self.parser.get_fix_commits()
        self.assertIsInstance(fixes, list)
        self.assertGreaterEqual(len(fixes), 1)

        fix_found = False
        for fix in fixes:
            self.assertIn('hash', fix)
            self.assertIn('message', fix)
            if self.unique_id in fix['message'] and fix['message'].startswith('fix'):
                fix_found = True
        self.assertTrue(fix_found, "Fix commit with unique ID must be detected")

    def test_integration_parse_lesson_history(self):
        lesson_data = self.parser.parse_lesson_history(self.file_name)

        self.assertIsInstance(lesson_data, dict)
        self.assertIn("failures", lesson_data)
        self.assertIn("fixes", lesson_data)
        self.assertIn("anticheat_errors", lesson_data)

        self.assertTrue(any(self.unique_id in f for f in lesson_data["failures"]))
        self.assertTrue(any(self.unique_id in fx for fx in lesson_data["fixes"]))
        self.assertTrue(any(self.error_code in err for err in lesson_data["anticheat_errors"]))

    def test_integration_exception_unbuffered(self):
        empty_dir = tempfile.TemporaryDirectory()
        try:
            empty_inspector = GitInspector(empty_dir.name)
            empty_parser = LessonParser(empty_inspector)

            with self.assertRaises(Exception):
                empty_parser.parse_lesson_history(self.file_name)
        finally:
            empty_dir.cleanup()


if __name__ == '__main__':
    unittest.main()