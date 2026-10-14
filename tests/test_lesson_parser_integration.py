import unittest
import uuid
import random
import io
import os
import tempfile
import shutil
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser, LessonParserError

class TestLessonParserIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.system(f"git init -q {self.test_dir}")
        os.system(f"git -C {self.test_dir} config user.name 'Architect'")
        os.system(f"git -C {self.test_dir} config user.email 'architect@test.com'")

        self.inspector = GitInspector(self.test_dir)
        self.parser = LessonParser(self.inspector)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_parse_lessons_integration_with_real_git(self):
        random_commit_msg = f"Commit message {uuid.uuid4()}"
        random_file_content = f"Content text {uuid.uuid4()}"

        file_path = os.path.join(self.test_dir, "lesson.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(random_file_content)

        os.system(f"git -C {self.test_dir} add lesson.txt")
        os.system(f"git -C {self.test_dir} commit -m '{random_commit_msg}' -q")

        lessons = self.parser.parse_lessons()

        self.assertIsInstance(lessons, list)
        self.assertTrue(len(lessons) > 0)

        found = False
        for lesson in lessons:
            if lesson.get('description') == random_commit_msg:
                self.assertEqual(lesson.get('content'), random_file_content)
                self.assertIn('commit', lesson)
                found = True
                break
        self.assertTrue(found, "Созданный в реальном репозитории коммит не найден парсером.")

    def test_extract_lessons_filtering_and_random_data(self):
        forbidden_word_content = f"This contains запрещено word {uuid.uuid4()}"
        normal_content = f"Clean content {uuid.uuid4()}"
        normal_msg = f"Msg {uuid.uuid4()}"

        f1_path = os.path.join(self.test_dir, "f1.txt")
        with open(f1_path, "w", encoding="utf-8") as f:
            f.write(forbidden_word_content)
        os.system(f"git -C {self.test_dir} add f1.txt")
        os.system(f"git -C {self.test_dir} commit -m 'Add f1' -q")

        f2_path = os.path.join(self.test_dir, "f2.txt")
        with open(f2_path, "w", encoding="utf-8") as f:
            f.write(normal_content)
        os.system(f"git -C {self.test_dir} add f2.txt")
        os.system(f"git -C {self.test_dir} commit -m '{normal_msg}' -q")

        extracted = self.parser.extract_lessons(max_commits=5)

        self.assertIsInstance(extracted, list)
        contents = [item['content'] for item in extracted]

        self.assertIn(normal_content, contents)
        self.assertNotIn(forbidden_word_content, contents)

    def test_parse_lessons_forbidden_chars_exception(self):
        bad_char = random.choice(['§', '©', '®', '™', 'ø'])
        bad_content = f"Text with forbidden {bad_char} {uuid.uuid4()}"

        f_path = os.path.join(self.test_dir, "bad.txt")
        with open(f_path, "w", encoding="utf-8") as f:
            f.write(bad_content)

        os.system(f"git -C {self.test_dir} add bad.txt")
        os.system(f"git -C {self.test_dir} commit -m 'Bad commit' -q")

        with self.assertRaises(LessonParserError):
            self.parser.parse_lessons()

if __name__ == '__main__':
    unittest.main()