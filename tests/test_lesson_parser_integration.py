import unittest
import os
import uuid
import random
import shutil
import tempfile
import subprocess
from skills.lesson_parser import LessonParser
from skills.git_inspector import GitInspector

class TestLessonParserIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(['git', '-C', self.test_dir, 'init', '-b', 'main'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        subprocess.run(['git', '-C', self.test_dir, 'config', 'user.name', 'TestUser'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        subprocess.run(['git', '-C', self.test_dir, 'config', 'user.email', 'test@example.com'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        self.inspector = GitInspector(self.test_dir)
        self.parser = LessonParser(self.inspector)

        self.lesson_id = str(uuid.uuid4())
        self.content = f"Lesson ID: {self.lesson_id}\nContent: {random.randint(1000, 9999)}"
        self.file_path = os.path.join(self.test_dir, "lesson.txt")

        with open(self.file_path, "w") as f:
            f.write(self.content)

        subprocess.run(['git', '-C', self.test_dir, 'add', 'lesson.txt'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        subprocess.run(['git', '-C', self.test_dir, 'commit', '-m', 'Initial commit'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_parser_integration_with_real_git_history(self):
        new_lesson_id = str(uuid.uuid4())
        new_content = f"Lesson ID: {new_lesson_id}\nContent: {random.randint(1000, 9999)}"

        with open(self.file_path, "w") as f:
            f.write(new_content)

        subprocess.run(['git', '-C', self.test_dir, 'add', 'lesson.txt'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        subprocess.run(['git', '-C', self.test_dir, 'commit', '-m', 'Update lesson content'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        history = self.inspector.get_commit_history()
        commit_hash = history[0]['hash']

        parsed_data = self.parser.parse_latest_change(commit_hash)

        self.assertIsNotNone(parsed_data)
        self.assertEqual(parsed_data['id'], new_lesson_id)
        self.assertIn(str(new_content), parsed_data['raw_text'])

    def test_parser_raises_exception_on_invalid_format(self):
        invalid_path = os.path.join(self.test_dir, "corrupted.txt")
        with open(invalid_path, "w") as f:
            f.write("INVALID_FORMAT_WITHOUT_ID")

        subprocess.run(['git', '-C', self.test_dir, 'add', 'corrupted.txt'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        subprocess.run(['git', '-C', self.test_dir, 'commit', '-m', 'Corrupted commit'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        history = self.inspector.get_commit_history()
        commit_hash = history[0]['hash']

        with self.assertRaises(ValueError):
            self.parser.parse_latest_change(commit_hash)

    def test_parser_tracks_multiple_changes(self):
        history_ids = []
        for _ in range(3):
            uid = str(uuid.uuid4())
            with open(self.file_path, "w") as f:
                f.write(f"ID: {uid}")
            subprocess.run(['git', '-C', self.test_dir, 'add', 'lesson.txt'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            subprocess.run(['git', '-C', self.test_dir, 'commit', '-m', f'Commit {uid}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            history_ids.append(uid)

        latest_changes = self.inspector.get_commit_history()
        self.assertTrue(len(latest_changes) >= 3)

        parsed = self.parser.parse_latest_change(latest_changes[0]['hash'])
        self.assertEqual(parsed['id'], history_ids[-1])

if __name__ == '__main__':
    unittest.main()
