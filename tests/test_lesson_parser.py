import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
import string
from skills.lesson_parser import LessonParser

class TestLessonParser(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.mock_inspector = MagicMock()
        self.parser = LessonParser(git_inspector=self.mock_inspector)

    def test_parse_lesson_with_valid_data(self):
        lesson_id = uuid.uuid4().hex
        content = f"Lesson ID: {lesson_id} | Content: {''.join(random.choices(string.ascii_letters, k=20))}"

        with patch('builtins.open', return_value=io.StringIO(content)):
            result = self.parser.parse(f"{uuid.uuid4().hex}.txt")
            self.assertEqual(result['id'], lesson_id)

    def test_parse_triggers_exception_on_malformed_data(self):
        bad_content = "".join(random.choices(string.punctuation, k=50))

        with patch('builtins.open', return_value=io.StringIO(bad_content)):
            with self.assertRaises(ValueError):
                self.parser.parse(f"{uuid.uuid4().hex}.txt")

    def test_integration_with_git_inspector_context(self):
        commit_hash = uuid.uuid4().hex
        file_path = f"{uuid.uuid4().hex}.py"
        diff_data = f"diff --git a/{file_path} b/{file_path}\n+{uuid.uuid4().hex}"

        self.mock_inspector.get_latest_changes.return_value = [{'hash': commit_hash, 'file': file_path}]
        self.mock_inspector.get_file_diff.return_value = diff_data

        with patch('builtins.open', return_value=io.StringIO(f"ID: {uuid.uuid4().hex}")):
            context = self.parser.get_context_for_file(file_path)

            self.mock_inspector.get_file_diff.assert_called_with(commit_hash)
            self.assertIn(commit_hash, context['history'])
            self.assertEqual(context['diff'], diff_data)

    def test_strict_error_handling_no_suppression(self):
        # Проверка, что парсер не глотает ошибки файловой системы
        random_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}"

        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            with self.assertRaises(FileNotFoundError):
                self.parser.parse(random_path)

    def test_data_integrity_with_random_payload(self):
        # Проверка обработки случайного бинарного мусора
        random_bytes = bytes([random.randint(0, 255) for _ in range(100)])

        with patch('builtins.open', return_value=io.BytesIO(random_bytes)):
            with self.assertRaises(Exception):
                self.parser.parse(f"{uuid.uuid4().hex}.bin")

    def test_inspector_interaction_logic(self):
        # Проверка, что парсер запрашивает историю именно для переданного файла
        target_file = f"{uuid.uuid4().hex}.md"
        self.parser.analyze_file_history(target_file)

        self.mock_inspector.get_history.assert_called_once()
        args, _ = self.mock_inspector.get_history.call_args
        self.assertTrue(any(target_file in str(arg) for arg in args))

if __name__ == '__main__':
    unittest.main()