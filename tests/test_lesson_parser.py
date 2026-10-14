import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
import string
from skills.lesson_parser import LessonParser, LessonParserError

class TestLessonParser(unittest.TestCase):

    def setUp(self):
        self.mock_inspector = MagicMock()
        self.parser = LessonParser(self.mock_inspector)
        self.random_hash = uuid.uuid4().hex
        self.random_msg = "".join(random.choices(string.ascii_letters + string.digits, k=16))

    def test_parse_lessons_empty_history(self):
        self.mock_inspector.get_history.return_value = []
        self.mock_inspector.get_latest_changes.return_value = []
        
        result = self.parser.parse_lessons()
        self.assertEqual(result, [])

    def test_parse_lessons_success_flow(self):
        commit_data = {'hash': self.random_hash, 'message': self.random_msg}
        self.mock_inspector.get_history.return_value = [commit_data]
        self.mock_inspector.get_latest_changes.return_value = [1]
        
        random_content_str = "".join(random.choices(string.ascii_letters + string.whitespace, k=20))
        mock_file = io.BytesIO(random_content_str.encode('utf-8'))
        self.mock_inspector.read_file_at_commit.return_value = mock_file

        result = self.parser.parse_lessons()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['commit'], self.random_hash)
        self.assertEqual(result[0]['description'], self.random_msg)
        self.assertEqual(result[0]['content'], random_content_str)

    def test_parse_lessons_forbidden_char_raises(self):
        commit_data = {'hash': self.random_hash, 'message': self.random_msg}
        self.mock_inspector.get_history.return_value = [commit_data]
        self.mock_inspector.get_latest_changes.return_value = [1]
        
        forbidden_char = random.choice(['§', '©', '®', '™', 'ø'])
        bad_content = f"content {forbidden_char} payload"
        mock_file = io.BytesIO(bad_content.encode('utf-8'))
        self.mock_inspector.read_file_at_commit.return_value = mock_file

        with self.assertRaises(LessonParserError):
            self.parser.parse_lessons()

    def test_parse_lessons_read_file_failure_fallback(self):
        commit_data = {'hash': self.random_hash, 'message': self.random_msg}
        self.mock_inspector.get_history.return_value = [commit_data]
        self.mock_inspector.get_latest_changes.return_value = [1]
        
        random_error_msg = uuid.uuid4().hex
        self.mock_inspector.read_file_at_commit.side_effect = Exception(random_error_msg)

        result = self.parser.parse_lessons()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['commit'], self.random_hash)
        self.assertEqual(result[0]['description'], self.random_msg)
        self.assertEqual(result[0]['content'], self.random_msg)

    def test_parse_lessons_invalid_commit_structure_skips(self):
        invalid_commit = {"invalid_key": uuid.uuid4().hex}
        self.mock_inspector.get_history.return_value = [invalid_commit]
        self.mock_inspector.get_latest_changes.return_value = [1]

        result = self.parser.parse_lessons()
        self.assertEqual(result, [])

    def test_extract_lessons_empty_history(self):
        max_c = random.randint(1, 20)
        self.mock_inspector.get_history.return_value = None
        
        result = self.parser.extract_lessons(max_commits=max_c)
        self.assertEqual(result, [])
        self.mock_inspector.get_history.assert_called_once_with(max_count=max_c)

    def test_extract_lessons_success(self):
        commit_data = {'hash': self.random_hash, 'message': self.random_msg}
        self.mock_inspector.get_history.return_value = [commit_data]
        
        random_payload = "".join(random.choices(string.ascii_letters, k=15))
        mock_file = io.BytesIO(random_payload.encode('utf-8'))
        self.mock_inspector.read_file_at_commit.return_value = mock_file

        result = self.parser.extract_lessons()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['commit'], self.random_hash)
        self.assertEqual(result[0]['content'], random_payload)

    def test_extract_lessons_forbidden_word_skips(self):
        commit_data = {'hash': self.random_hash, 'message': self.random_msg}
        self.mock_inspector.get_history.return_value = [commit_data]
        
        forbidden_content = "text containing запрещено word"
        mock_file = io.BytesIO(forbidden_content.encode('utf-8'))
        self.mock_inspector.read_file_at_commit.return_value = mock_file

        result = self.parser.extract_lessons()
        self.assertEqual(result, [])

    def test_extract_lessons_inspector_exception_returns_empty(self):
        random_err = uuid.uuid4().hex
        self.mock_inspector.get_history.side_effect = Exception(random_err)
        
        result = self.parser.extract_lessons()
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()