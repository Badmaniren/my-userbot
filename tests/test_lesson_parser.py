import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
import string

from skills.lesson_parser import LessonParser, LessonParserError

class TestLessonParser(unittest.TestCase):
    def setUp(self):
        self.mock_git_inspector = MagicMock()
        self.parser = LessonParser(self.mock_git_inspector)

    def test_parse_lessons_empty_history(self):
        self.mock_git_inspector.get_history.return_value = []
        self.mock_git_inspector.get_latest_changes.return_value = []

        result = self.parser.parse_lessons()
        self.assertEqual(result, [])

    def success_random_string(self, length=10):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def test_parse_lessons_success(self):
        c_hash = uuid.uuid4().hex
        msg = self.success_random_string(15)
        content_text = self.success_random_string(20)

        self.mock_git_inspector.get_history.return_value = [{'hash': c_hash, 'message': msg}]
        self.mock_git_inspector.get_latest_changes.return_value = [c_hash]

        file_mock = io.BytesIO(content_text.encode('utf-8'))
        self.mock_git_inspector.read_file_at_commit.return_value = file_mock

        result = self.parser.parse_lessons()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['commit'], c_hash)
        self.assertEqual(result[0]['description'], msg)
        self.assertEqual(result[0]['content'], content_text)

    def test_parse_lessons_forbidden_char_raises(self):
        c_hash = uuid.uuid4().hex
        msg = self.success_random_string(10)
        forbidden_char = '§'
        content_text = self.success_random_string(5) + forbidden_char + self.success_random_string(5)

        self.mock_git_inspector.get_history.return_value = [{'hash': c_hash, 'message': msg}]
        self.mock_git_inspector.get_latest_changes.return_value = [c_hash]

        file_mock = io.BytesIO(content_text.encode('utf-8'))
        self.mock_git_inspector.read_file_at_commit.return_value = file_mock

        with self.assertRaises(LessonParserError):
            self.parser.parse_lessons()

    def test_parse_lessons_read_error_fallback(self):
        c_hash = uuid.uuid4().hex
        msg = self.success_random_string(12)

        self.mock_git_inspector.get_history.return_value = [{'hash': c_hash, 'message': msg}]
        self.mock_git_inspector.get_latest_changes.return_value = [c_hash]

        err_msg = self.success_random_string(8)
        self.mock_git_inspector.read_file_at_commit.side_effect = Exception(err_msg)

        result = self.parser.parse_lessons()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['commit'], c_hash)
        self.assertEqual(result[0]['description'], msg)
        self.assertEqual(result[0]['content'], msg)

    def test_extract_lessons_success(self):
        c_hash = uuid.uuid4().hex
        content_text = self.success_random_string(25)
        max_commits_val = random.randint(1, 20)

        self.mock_git_inspector.get_history.return_value = [{'hash': c_hash, 'message': self.success_random_string(5)}]

        file_mock = io.BytesIO(content_text.encode('utf-8'))
        self.mock_git_inspector.read_file_at_commit.return_value = file_mock

        result = self.parser.extract_lessons(max_commits=max_commits_val)

        self.mock_git_inspector.get_history.assert_called_once_with(max_count=max_commits_val)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['commit'], c_hash)
        self.assertEqual(result[0]['content'], content_text)

    def test_extract_lessons_forbidden_word_skipped(self):
        c_hash = uuid.uuid4().hex
        content_text = self.success_random_string(5) + "запрещено" + self.success_random_string(5)

        self.mock_git_inspector.get_history.return_value = [{'hash': c_hash, 'message': self.success_random_string(5)}]

        file_mock = io.BytesIO(content_text.encode('utf-8'))
        self.mock_git_inspector.read_file_at_commit.return_value = file_mock

        result = self.parser.extract_lessons()

        self.assertEqual(result, [])

    def test_extract_lessons_inspector_exception_returns_empty(self):
        err_msg = self.success_random_string(10)
        self.mock_git_inspector.get_history.side_effect = Exception(err_msg)

        result = self.parser.extract_lessons()
        self.assertEqual(result, [])