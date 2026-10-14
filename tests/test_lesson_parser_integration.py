import unittest
import os
import shutil
import tempfile
import uuid
import random
import subprocess
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser

class TestLessonParserIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "init", self.test_dir], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Architect Test"], check=True)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "architect@test.com"], check=True)

        self.unique_id = str(uuid.uuid4())
        self.error_type = random.choice(["syntax_error", "logic_error", "timeout", "segmentation_fault"])

        self.filename = f"ungo_history_{self.unique_id}.log"
        self.file_path = os.path.join(self.test_dir, self.filename)

        log_content = f"ID: {self.unique_id}\nERROR: {self.error_type}\nSTATUS: FAILED\n"
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(log_content)

        subprocess.run(["git", "-C", self.test_dir, "add", self.filename], check=True)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", f"Add failure history {self.unique_id}"], check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_lesson_parser_with_real_git_inspector(self):
        inspector = GitInspector(repo_path=self.test_dir)
        parser = LessonParser(inspector=inspector)

        patterns = parser.extract_error_patterns()

        self.assertTrue(isinstance(patterns, (dict, list)))

        pattern_str = str(patterns)
        found = (self.unique_id in pattern_str or self.error_type in pattern_str)

        self.assertTrue(
            found,
            f"Интеграционный тест не смог обнаружить случайный ID {self.unique_id} или ошибку {self.error_type} через связку GitInspector и LessonParser."
        )

if __name__ == '__main__':
    unittest.main()
