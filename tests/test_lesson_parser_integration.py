import unittest
import tempfile
import os
import subprocess
import uuid
import random
from skills.lesson_parser import LessonParser, GitInspector

class TestLessonParserIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

        subprocess.run(["git", "init", self.repo_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Architect Test"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "architect@test.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_lesson_parser_and_git_inspector_integration(self):
        unique_id = str(uuid.uuid4())
        lesson_title = f"# Lesson {random.randint(1000, 9999)} - {unique_id}"
        file_name = f"lesson_{random.randint(1, 100)}.md"
        file_path = os.path.join(self.repo_path, file_name)

        file_content = f"{lesson_title}\n\nУрок {unique_id}\nSome dynamic content {random.random()}"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        subprocess.run(["git", "-C", self.repo_path, "add", file_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", f"Add lesson {unique_id}"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        log_result = subprocess.run(["git", "-C", self.repo_path, "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        commit_hash = log_result.stdout.strip()

        inspector = GitInspector(repo_path=self.repo_path)
        parser = LessonParser(git_inspector=inspector)

        parsed_data = parser.parse_lesson_file(commit_hash, file_name)

        self.assertEqual(parsed_data["lesson_id"], unique_id)
        self.assertEqual(parsed_data["title"], lesson_title)
        self.assertIn(file_content, parsed_data["raw_content"])

        stream_content = parser.parse_stream(commit_hash, file_name)
        self.assertEqual(stream_content, file_content)

        history_context = parser.extract_history_context(file_name)
        self.assertIn(commit_hash, history_context)
        self.assertIn(f"Add lesson {unique_id}", history_context)

if __name__ == "__main__":
    unittest.main()