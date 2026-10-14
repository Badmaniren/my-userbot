import unittest
import uuid
import random
import tempfile
import os
import shutil
from skills.lesson_parser import LessonParser, LessonParserError
from skills.git_inspector import GitInspector

class TestLessonParserIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Инициализация реального Git репозитория для честного интеграционного теста
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Architect Test'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")
        
        self.inspector = GitInspector(self.repo_path)
        self.parser = LessonParser(self.inspector)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_integration_parse_and_extract_lessons_with_random_data(self):
        random_suffix = uuid.uuid4().hex[:8]
        file_name = f"lesson_{random_suffix}.txt"
        file_path = os.path.join(self.repo_path, file_name)
        
        unique_commit_message = f"Commit message {random.randint(1000, 9999)}"
        unique_content = f"Lesson content {uuid.uuid4()}"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(unique_content)
            
        os.system(f"git -C {self.repo_path} add {file_name}")
        os.system(f"git -C {self.repo_path} commit -m '{unique_commit_message}'")
        
        parsed_lessons = self.parser.parse_lessons()
        self.assertIsInstance(parsed_lessons, list)
        self.assertTrue(any(unique_content in lesson.get('content', '') for lesson in parsed_lessons))
        
        extracted_lessons = self.parser.extract_lessons(max_commits=5)
        self.assertIsInstance(extracted_lessons, list)
        self.assertTrue(any(unique_content in lesson.get('content', '') for lesson in extracted_lessons))

    def test_integration_forbidden_chars_raises_error(self):
        random_suffix = uuid.uuid4().hex[:8]
        file_name = f"bad_lesson_{random_suffix}.txt"
        file_path = os.path.join(self.repo_path, file_name)
        
        bad_content = f"Contains forbidden char § {uuid.uuid4()}"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(bad_content)
            
        os.system(f"git -C {self.repo_path} add {file_name}")
        os.system(f"git -C {self.repo_path} commit -m 'Add bad lesson'")
        
        with self.assertRaises(LessonParserError):
            self.parser.parse_lessons()

    def test_integration_extract_lessons_filters_forbidden_words(self):
        random_suffix = uuid.uuid4().hex[:8]
        file_name = f"forbidden_word_{random_suffix}.txt"
        file_path = os.path.join(self.repo_path, file_name)
        
        forbidden_content = f"This content is запрещено {uuid.uuid4()}"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(forbidden_content)
            
        os.system(f"git -C {self.repo_path} add {file_name}")
        os.system(f"git -C {self.repo_path} commit -m 'Forbidden word commit'")
        
        extracted_lessons = self.parser.extract_lessons(max_commits=5)
        for lesson in extracted_lessons:
            self.assertNotIn("запрещено", lesson.get('content', ''))

if __name__ == '__main__':
    unittest.main()