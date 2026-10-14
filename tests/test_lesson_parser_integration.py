import unittest
import logging
import io
import uuid
import random
from skills.lesson_parser import LessonParser, LessonParserError

class MockGitInspector:
    def __init__(self, history_data=None, changes_data=None, files_map=None, fail_on_read=False):
        self.history_data = history_data or []
        self.changes_data = changes_data or []
        self.files_map = files_map or {}
        self.fail_on_read = fail_on_read

    def get_history(self, max_count=None):
        if max_count is not None:
            return self.history_data[:max_count]
        return self.history_data

    def get_latest_changes(self):
        return self.changes_data

    def get_commit_history(self, max_count=10):
        return self.get_history(max_count)

    def get_file_diff(self, commit_hash):
        return ""

    def analyze_repository(self):
        return {}

    def get_changed_files_at_commit(self, commit_hash):
        return self.files_map.get(commit_hash, {}).get("changed_files", [])

    def read_file_at_commit(self, commit_hash, file_path):
        if self.fail_on_read:
            raise RuntimeError("Critical storage failure")
        
        file_contents = self.files_map.get(commit_hash, {}).get("contents", {})
        content = file_contents.get(file_path, b"")
        if isinstance(content, str):
            content = content.encode('utf-8')
        return io.BytesIO(content)

class TestLessonParserIntegration(unittest.TestCase):
    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_integration_parse_lessons_success_and_random_stability(self):
        random_hash = uuid.uuid4().hex
        random_msg = f"Commit message {uuid.uuid4()}"
        random_filename = f"lesson_{uuid.uuid4().hex[:6]}.py"
        random_content = f"print('Hello {uuid.uuid4()}')".encode('utf-8')

        history = [
            {"hash": random_hash, "message": random_msg}
        ]
        files_map = {
            random_hash: {
                "changed_files": [random_filename],
                "contents": {random_filename: random_content}
            }
        }

        inspector = MockGitInspector(history_data=history, files_map=files_map)
        parser = LessonParser(inspector)

        lessons = parser.parse_lessons()

        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]["commit"], random_hash)
        self.assertEqual(lessons[0]["description"], random_msg)
        self.assertEqual(lessons[0]["content"], random_content.decode('utf-8'))

    def test_integration_parse_lessons_forbidden_char_raises(self):
        random_hash = uuid.uuid4().hex
        random_msg = f"Msg {uuid.uuid4()}"
        random_filename = "bad_file.txt"
        forbidden_char = random.choice(['§', '©', '®', '™', 'ø'])
        bad_content = f"Invalid content with forbidden {forbidden_char}".encode('utf-8')

        history = [{"hash": random_hash, "message": random_msg}]
        files_map = {
            random_hash: {
                "changed_files": [random_filename],
                "contents": {random_filename: bad_content}
            }
        }

        inspector = MockGitInspector(history_data=history, files_map=files_map)
        parser = LessonParser(inspector)

        with self.assertRaises(LessonParserError):
            parser.parse_lessons()

    def test_integration_extract_lessons_filters_forbidden_words(self):
        clean_hash = uuid.uuid4().hex
        forbidden_hash = uuid.uuid4().hex
        
        clean_filename = f"file_{uuid.uuid4().hex[:4]}.txt"
        forbidden_filename = f"file_{uuid.uuid4().hex[:4]}.txt"

        clean_content = f"Normal lesson text {uuid.uuid4()}".encode('utf-8')
        forbidden_content = f"This content contains запрещено and id {uuid.uuid4()}".encode('utf-8')

        history = [
            {"hash": clean_hash, "message": "clean"},
            {"hash": forbidden_hash, "message": "forbidden"}
        ]
        files_map = {
            clean_hash: {
                "changed_files": [clean_filename],
                "contents": {clean_filename: clean_content}
            },
            forbidden_hash: {
                "changed_files": [forbidden_filename],
                "contents": {forbidden_filename: forbidden_content}
            }
        }

        inspector = MockGitInspector(history_data=history, files_map=files_map)
        parser = LessonParser(inspector)

        lessons = parser.extract_lessons(max_commits=5)

        self.assertEqual(len(lessons), 1)
        self.assertEqual(lessons[0]["commit"], clean_hash)
        self.assertEqual(lessons[0]["content"], clean_content.decode('utf-8'))

    def test_integration_extract_lessons_inspector_failure_resilience(self):
        inspector = MockGitInspector(fail_on_read=True)
        parser = LessonParser(inspector)

        history = [{"hash": uuid.uuid4().hex, "message": "fail test"}]
        inspector.history_data = history

        lessons = parser.extract_lessons(max_commits=2)
        self.assertIsInstance(lessons, list)

if __name__ == '__main__':
    unittest.main()