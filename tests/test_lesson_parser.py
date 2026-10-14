import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
from skills.lesson_parser import LessonParser, LessonParserError

class TestLessonParser(unittest.TestCase):

    def setUp(self):
        self.mock_git_inspector = MagicMock()
        self.parser = LessonParser(self.mock_git_inspector)
        self.random_hash = uuid.uuid4().hex
        self.random_msg = uuid.uuid4().hex
        self.random_content = uuid.uuid4().hex

    def test_parse_lessons_success(self):
        commit_data = {'hash': self.random_hash, 'message': self.random_msg}
        self.mock_git_inspector.get_history.return_value = [commit_data]
        self.mock_git_inspector.get_latest_changes.return_value = []

        file_mock = io.BytesIO(self.random_content.encode('utf-8'))
        self.mock_git_inspector.read_file_at_commit.return_value = file_mock

        lessons = self.parser.parse_lessons()

        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]['commit'], self.random_hash)
        self.assertEqual(lessons[0]['description'], self.random_msg)
        self.assertEqual(lessons[0]['content'], self.random_content)

    def test_parse_lessons_forbidden_char_raises(self):
        forbidden_char = random.choice(['§', '©', '®', '™', 'ø'])
        corrupted_content = f"{self.random_content}{forbidden_char}"

        commit_data = {'hash': self.random_hash, 'message': self.random_msg}
        self.mock_git_inspector.get_history.return_value = [commit_data]
        self.mock_git_inspector.get_latest_changes.return_value = []

        file_mock = io.BytesIO(corrupted_content.encode('utf-8'))
        self.mock_git_inspector.read_file_at_commit.return_value = file_mock

        with self.assertRaises(LessonParserError):
            self.parser.parse_lessons()

    def test_parse_lessons_empty_history_and_changes(self):
        self.mock_git_inspector.get_history.return_value = []
        self.mock_git_inspector.get_latest_changes.return_value = []

        lessons = self.parser.parse_lessons()
        self.assertEqual(lessons, [])

    def test_parse_lessons_invalid_commit_structure(self):
        invalid_commit = uuid.uuid4().hex
        self.mock_git_inspector.get_history.return_value = [invalid_commit]
        self.mock_git_inspector.get_latest_changes.return_value = []

        lessons = self.parser.parse_lessons()
        self.assertEqual(lessons, [])

    def test_parse_lessons_file_read_fallback(self):
        commit_data = {'hash': self.random_hash, 'message': self.random_msg}
        self.mock_git_inspector.get_history.return_value = [commit_data]
        self.mock_git_inspector.get_latest_changes.return_value = []

        err_msg = uuid.uuid4().hex
        self.mock_git_inspector.read_file_at_commit.side_effect = Exception(err_msg)

        lessons = self.parser.parse_lessons()

        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]['commit'], self.random_hash)
        self.assertEqual(lessons[0]['description'], self.random_msg)
        self.assertEqual(lessons[0]['content'], self.random_msg)

    def test_parse_lessons_general_exception_wraps(self):
        err_msg = uuid.uuid4().hex
        self.mock_git_inspector.get_history.side_effect = Exception(err_msg)

        with self.assertRaises(LessonParserError):
            self.parser.parse_lessons()

    def test_extract_lessons_success(self):
        max_commits = random.randint(1, 20)
        commit_data = {'hash': self.random_hash, 'message': self.random_msg}
        self.mock_git_inspector.get_history.return_value = [commit_data]

        file_mock = io.BytesIO(self.random_content.encode('utf-8'))
        self.mock_git_inspector.read_file_at_commit.return_value = file_mock

        lessons = self.parser.extract_lessons(max_commits=max_commits)

        self.mock_git_inspector.get_history.assert_called_once_with(max_count=max_commits)
        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]['commit'], self.random_hash)
        self.assertEqual(lessons[0]['content'], self.random_content)

    def test_extract_lessons_history_none(self):
        self.mock_git_inspector.get_history.return_value = None

        lessons = self.parser.extract_lessons()
        self.assertEqual(lessons, [])

    def test_extract_lessons_skip_forbidden_word(self):
        forbidden_content = f"{uuid.uuid4().hex} запрещено {uuid.uuid4().hex}"
        commit_data = {'hash': self.random_hash, 'message': self.random_msg}
        self.mock_git_inspector.get_history.return_value = [commit_data]

        file_mock = io.BytesIO(forbidden_content.encode('utf-8'))
        self.mock_git_inspector.read_file_at_commit.return_value = file_mock

        lessons = self.parser.extract_lessons()
        self.assertEqual(lessons, [])

    def test_extract_lessons_inspector_exception_returns_empty(self):
        err_msg = uuid.uuid4().hex
        self.mock_git_inspector.get_history.side_effect = Exception(err_msg)

        lessons = self.parser.extract_lessons()
        self.assertEqual(lessons, [])

    def test_parse_lessons_latin1_fallback(self):
        commit_data = {'hash': self.random_hash, 'message': self.random_msg}
        self.mock_git_inspector.get_history.return_value = [commit_data]
        self.mock_git_inspector.get_latest_changes.return_value = []

        invalid_utf8_bytes = b'\xff\xfe\xfd' + self.random_content.encode('latin1')
        file_mock = io.BytesIO(invalid_utf8_bytes)
        self.mock_git_inspector.read_file_at_commit.return_value = file_mock

        lessons = self.parser.parse_lessons()

        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]['commit'], self.random_hash)

if __name__ == '__main__':
    unittest.main()