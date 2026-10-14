import unittest
import os
import uuid
import random
import shutil
import tempfile
from git import Repo
from skills.lesson_parser import LessonParser
from skills.git_inspector import GitInspector

class TestLessonParserIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo = Repo.init(self.test_dir)
        self.inspector = GitInspector(self.test_dir)
        self.parser = LessonParser(self.inspector)

        self.lesson_id = str(uuid.uuid4())
        self.content = f"Lesson ID: {self.lesson_id}\nContent: {random.randint(1000, 9999)}"
        self.file_path = os.path.join(self.test_dir, "lesson.txt")

        with open(self.file_path, "w") as f:
            f.write(self.content)

        self.repo.index.add([self.file_path])
        self.repo.index.commit("Initial commit")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_parser_integration_with_real_git_history(self):
        new_lesson_id = str(uuid.uuid4())
        new_content = f"Lesson ID: {new_lesson_id}\nContent: {random.randint(1000, 9999)}"

        with open(self.file_path, "w") as f:
            f.write(new_content)

        self.repo.index.add([self.file_path])
        commit = self.repo.index.commit("Update lesson content")

        parsed_data = self.parser.parse_latest_change(commit.hexsha)

        self.assertIsNotNone(parsed_data)
        self.assertEqual(parsed_data['id'], new_lesson_id)
        self.assertIn(str(new_content), parsed_data['raw_text'])

    def test_parser_raises_exception_on_invalid_format(self):
        invalid_path = os.path.join(self.test_dir, "corrupted.txt")
        with open(invalid_path, "w") as f:
            f.write("INVALID_FORMAT_WITHOUT_ID")

        self.repo.index.add([invalid_path])
        commit = self.repo.index.commit("Corrupted commit")

        with self.assertRaises(ValueError):
            self.parser.parse_latest_change(commit.hexsha)

    def test_parser_tracks_multiple_changes(self):
        history_ids = []
        for _ in range(3):
            uid = str(uuid.uuid4())
            with open(self.file_path, "w") as f:
                f.write(f"ID: {uid}")
            self.repo.index.add([self.file_path])
            self.repo.index.commit(f"Commit {uid}")
            history_ids.append(uid)

        latest_changes = list(self.repo.iter_commits())
        self.assertTrue(len(latest_changes) >= 3)

        parsed = self.parser.parse_latest_change(latest_changes[0].hexsha)
        self.assertEqual(parsed['id'], history_ids[-1])

if __name__ == '__main__':
    unittest.main()