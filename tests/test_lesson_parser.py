import io
import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.lesson_parser import LessonParser
from skills.git_inspector import GitInspector


class TestLessonParser(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.random_commit_hash = uuid.uuid4().hex
        self.random_file_path = f"{uuid.uuid4().hex}.py"
        self.random_error_code = f"ANTICHEAT_VIOLATION_{uuid.uuid4().hex.upper()}"
        self.random_message = f"fix: {uuid.uuid4().hex}"

    def test_init_with_git_inspector_instance(self):
        mock_inspector = MagicMock(spec=GitInspector)
        mock_inspector.repo_path = self.random_repo_path
        parser = LessonParser(mock_inspector)
        self.assertEqual(parser.inspector, mock_inspector)
        self.assertEqual(parser.repo_path, self.random_repo_path)

    def test_init_with_repo_path_string(self):
        with patch('skills.lesson_parser.GitInspector') as mock_inspector_cls:
            instance = mock_inspector_cls.return_value
            instance.repo_path = self.random_repo_path
            parser = LessonParser(self.random_repo_path)
            mock_inspector_cls.assert_called_once_with(self.random_repo_path)
            self.assertEqual(parser.repo_path, self.random_repo_path)

    def test_extract_failure_history_success(self):
        mock_inspector = MagicMock(spec=GitInspector)
        commit_hash_1 = uuid.uuid4().hex
        commit_hash_2 = uuid.uuid4().hex
        msg_1 = uuid.uuid4().hex
        msg_2 = uuid.uuid4().hex
        diff_1 = uuid.uuid4().hex
        diff_2 = uuid.uuid4().hex

        mock_inspector.get_commit_history.return_value = [
            {'hash': commit_hash_1, 'message': msg_1},
            {'hash': commit_hash_2, 'message': msg_2}
        ]
        mock_inspector.get_file_diff.side_effect = [diff_1, diff_2]

        parser = LessonParser(mock_inspector)
        history = parser.extract_failure_history(max_commits=2)

        mock_inspector.get_commit_history.assert_called_once_with(max_count=2)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['commit_hash'], commit_hash_1)
        self.assertEqual(history[0]['message'], msg_1)
        self.assertEqual(history[0]['diff'], diff_1)
        self.assertEqual(history[1]['commit_hash'], commit_hash_2)
        self.assertEqual(history[1]['message'], msg_2)
        self.assertEqual(history[1]['diff'], diff_2)

    def test_parse_anticheat_errors_with_bytes_io(self):
        mock_inspector = MagicMock(spec=GitInspector)
        content_lines = [
            f"some log line {uuid.uuid4().hex}",
            f"error occurred '{self.random_error_code}' details",
            f'another error "{self.random_error_code}" payload',
            f"raw error {self.random_error_code}"
        ]
        file_content = "\n".join(content_lines).encode('utf-8')
        mock_inspector.read_file_at_commit.return_value = io.BytesIO(file_content)

        parser = LessonParser(mock_inspector)
        errors = parser.parse_anticheat_errors(self.random_commit_hash, self.random_file_path)

        mock_inspector.read_file_at_commit.assert_called_once_with(self.random_commit_hash, self.random_file_path)
        self.assertIn(self.random_error_code, errors)
        self.assertGreaterEqual(len(errors), 3)

    def test_parse_anticheat_errors_with_string(self):
        mock_inspector = MagicMock(spec=GitInspector)
        file_content = f"Critical alert: {self.random_error_code} detected in module"
        mock_inspector.read_file_at_commit.return_value = file_content

        parser = LessonParser(mock_inspector)
        errors = parser.parse_anticheat_errors(self.random_commit_hash, self.random_file_path)

        self.assertIn(self.random_error_code, errors)

    def test_get_fix_commits_success(self):
        mock_inspector = MagicMock(spec=GitInspector)
        fix_hash = uuid.uuid4().hex
        other_hash = uuid.uuid4().hex
        fix_msg = f"fix: {uuid.uuid4().hex}"
        other_msg = f"feat: {uuid.uuid4().hex}"

        mock_inspector.get_commit_history.return_value = [
            {'hash': fix_hash, 'message': fix_msg},
            {'hash': other_hash, 'message': other_msg}
        ]

        parser = LessonParser(mock_inspector)
        fixes = parser.get_fix_commits()

        mock_inspector.get_commit_history.assert_called_once()
        self.assertEqual(len(fixes), 1)
        self.assertEqual(fixes[0]['hash'], fix_hash)
        self.assertEqual(fixes[0]['message'], fix_msg)

    def test_parse_lesson_history_success(self):
        mock_inspector = MagicMock(spec=GitInspector)
        latest_hash = uuid.uuid4().hex
        failure_text = uuid.uuid4().hex
        fix_text = uuid.uuid4().hex
        ac_text = uuid.uuid4().hex

        mock_inspector.get_commit_history.return_value = [
            {'hash': latest_hash, 'message': uuid.uuid4().hex}
        ]

        file_content = (
            f"Failure history: {failure_text}\n"
            f"Fix applied: {fix_text}\n"
            f"Anticheat error: {ac_text}\n"
        ).encode('utf-8')
        mock_inspector.read_file_at_commit.return_value = io.BytesIO(file_content)

        parser = LessonParser(mock_inspector)
        lesson_data = parser.parse_lesson_history(self.random_file_path)

        mock_inspector.get_commit_history.assert_called_once()
        mock_inspector.read_file_at_commit.assert_called_once_with(latest_hash, self.random_file_path)
        self.assertEqual(lesson_data["failures"], [failure_text])
        self.assertEqual(lesson_data["fixes"], [fix_text])
        self.assertEqual(lesson_data["anticheat_errors"], [ac_text])

    def test_parse_lesson_history_no_commits_raises_exception(self):
        mock_inspector = MagicMock(spec=GitInspector)
        mock_inspector.get_commit_history.return_value = []

        parser = LessonParser(mock_inspector)

        with self.assertRaises(Exception) as context:
            parser.parse_lesson_history(self.random_file_path)

        self.assertIn("No commits found", str(context.exception))


if __name__ == '__main__':
    unittest.main()