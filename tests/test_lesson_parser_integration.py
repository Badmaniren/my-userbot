import unittest
import uuid
import random
import tempfile
import os
import subprocess
from skills.lesson_parser import LessonParser, LessonParserError
from skills.git_inspector import GitInspector

class TestLessonParserIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name

        # Initialize git repository using subprocess
        subprocess.run(['git', 'init', self.repo_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(['git', '-C', self.repo_path, 'config', 'user.name', 'Architect Test'], check=True)
        subprocess.run(['git', '-C', self.repo_path, 'config', 'user.email', 'architect@test.com'], check=True)

        self.file_name = f"lesson_{uuid.uuid4().hex[:8]}.txt"
        self.file_path = os.path.join(self.repo_path, self.file_name)

        unique_content = f"Lesson content {uuid.uuid4()}"
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(unique_content)

        subprocess.run(['git', '-C', self.repo_path, 'add', self.file_name], check=True)
        commit_msg = f"Commit message {uuid.uuid4().hex[:6]}"
        subprocess.run(['git', '-C', self.repo_path, 'commit', '-m', commit_msg], check=True)

        res = subprocess.run(['git', '-C', self.repo_path, 'rev-parse', 'HEAD'], check=True, stdout=subprocess.PIPE, text=True)
        self.commit_hash = res.stdout.strip()

        self.inspector = GitInspector(self.repo_path)
        self.parser = LessonParser(self.inspector)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_parse_lessons_integration_success(self):
        lessons = self.parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        self.assertGreaterEqual(len(lessons), 1)

        found = False
        for lesson in lessons:
            if lesson.get('commit') == self.commit_hash or (self.commit_hash and self.commit_hash.startswith(lesson.get('commit', ''))):
                found = True
                self.assertIn('Lesson content', lesson.get('content', ''))
        self.assertTrue(found, "Созданный коммит должен быть найден в результатах парсинга")

    def test_parse_lessons_forbidden_char_error(self):
        bad_content = f"Forbidden content § {uuid.uuid4()}"
        bad_file_path = os.path.join(self.repo_path, f"bad_{uuid.uuid4().hex[:6]}.txt")

        with open(bad_file_path, 'w', encoding='utf-8') as f:
            f.write(bad_content)

        rel_path = os.path.basename(bad_file_path)
        subprocess.run(['git', '-C', self.repo_path, 'add', rel_path], check=True)
        subprocess.run(['git', '-C', self.repo_path, 'commit', '-m', 'Commit with forbidden char'], check=True)

        with self.assertRaises(LessonParserError):
            self.parser.parse_lessons()

    def test_extract_lessons_integration_filtering(self):
        limit = random.randint(5, 15)
        lessons = self.parser.extract_lessons(max_commits=limit)
        self.assertIsInstance(lessons, list)

        for lesson in lessons:
            self.assertIn('commit', lesson)
            self.assertIn('content', lesson)
            self.assertNotIn("запрещено", lesson['content'])
