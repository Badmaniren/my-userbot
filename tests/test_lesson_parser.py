import unittest
from unittest.mock import MagicMock, patch
import io
import random
import uuid
import string

from skills.lesson_parser import LessonParser, LessonParserError

class TestLessonParserUnit(unittest.TestCase):
    def setUp(self):
        self.git_inspector_mock = MagicMock()
        self.parser = LessonParser(self.git_inspector_mock)

    def test_parse_lessons_empty_history_and_changes(self):
        self.git_inspector_mock.get_history.return_value = []
        self.git_inspector_mock.get_latest_changes.return_value = []
        
        result = self.parser.parse_lessons()
        self.assertEqual(result, [])

    def test_parse_lessons_invalid_commit_structure(self):
        rand_invalid = random.choice([uuid.uuid4().hex, 123, None, []])
        self.git_inspector_mock.get_history.return_value = [rand_invalid]
        self.git_inspector_mock.get_latest_changes.return_value = []

        result = self.parser.parse_lessons()
        self.assertEqual(result, [])

    def test_parse_lessons_success_with_file_obj(self):
        c_hash = uuid.uuid4().hex
        msg = uuid.uuid4().hex
        file_content = uuid.uuid4().hex.encode('utf-8')

        commit = {'hash': c_hash, 'message': msg}
        self.git_inspector_mock.get_history.return_value = [commit]
        self.git_inspector_mock.get_latest_changes.return_value = []

        file_obj = io.BytesIO(file_content)
        self.git_inspector_mock.read_file_at_commit.return_value = file_obj

        result = self.parser.parse_lessons()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['commit'], c_hash)
        self.assertEqual(result[0]['description'], msg)
        self.assertEqual(result[0]['content'], file_content.decode('utf-8'))

    def test_parse_lessons_forbidden_chars_raises_error(self):
        c_hash = uuid.uuid4().hex
        msg = uuid.uuid4().hex
        forbidden_char = random.choice(['§', '©', '®', '™', 'ø'])
        file_content = f"{uuid.uuid4().hex}{forbidden_char}{uuid.uuid4().hex}".encode('utf-8')

        commit = {'hash': c_hash, 'message': msg}
        self.git_inspector_mock.get_history.return_value = [commit]
        self.git_inspector_mock.get_latest_changes.return_value = []

        file_obj = io.BytesIO(file_content)
        self.git_inspector_mock.read_file_at_commit.return_value = file_obj

        with self.assertRaises(LessonParserError):
            self.parser.parse_lessons()

    def test_extract_lessons_history_none(self):
        self.git_inspector_mock.get_history.return_value = None
        result = self.parser.extract_lessons(max_commits=random.randint(1, 20))
        self.assertEqual(result, [])

    def test_extract_lessons_success_filtering(self):
        c_hash = uuid.uuid4().hex
        msg = uuid.uuid4().hex
        commit = {'hash': c_hash, 'message': msg}

        self.git_inspector_mock.get_history.return_value = [commit]
        file_obj = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        self.git_inspector_mock.read_file_at_commit.return_value = file_obj

        result = self.parser.extract_lessons(max_commits=5)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['commit'], c_hash)

    def test_extract_lessons_skips_forbidden_words(self):
        c_hash = uuid.uuid4().hex
        msg = f"some text with запрещено inside {uuid.uuid4().hex}"
        commit = {'hash': c_hash, 'message': msg}

        self.git_inspector_mock.get_history.return_value = [commit]
        self.git_inspector_mock.read_file_at_commit.return_value = None

        result = self.parser.extract_lessons(max_commits=5)
        self.assertEqual(result, [])