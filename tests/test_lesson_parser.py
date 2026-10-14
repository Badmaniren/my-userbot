import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
import subprocess

from skills.lesson_parser import GitInspector, LessonParser

class TestLessonParserModule(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.commit_hash = uuid.uuid4().hex[:8]
        self.file_path = f"lessons/{uuid.uuid4().hex}.md"
        self.lesson_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        self.title_text = f"Title {uuid.uuid4().hex[:6]}"

    def test_git_inspector_init(self):
        inspector = GitInspector(repo_path=self.repo_path)
        self.assertEqual(inspector.repo_path, self.repo_path)

    @patch('subprocess.run')
    def test_git_inspector_run_git(self, mock_subprocess):
        random_output = uuid.uuid4().hex
        mock_result = MagicMock()
        mock_result.stdout = random_output
        mock_subprocess.return_value = mock_result

        inspector = GitInspector(repo_path=self.repo_path)
        arg = uuid.uuid4().hex
        res = inspector._run_git([arg])

        self.assertEqual(res, random_output)
        mock_subprocess.assert_called_once_with(
            ["git", "-C", self.repo_path, arg],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
        )

    @patch('subprocess.run')
    def test_read_file_at_commit_success(self, mock_subprocess):
        file_content = f"# {self.title_text}\nLesson ID: {self.lesson_id}"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = file_content
        mock_subprocess.return_value = mock_result

        inspector = GitInspector(repo_path=self.repo_path)
        content = inspector.read_file_at_commit(self.commit_hash, self.file_path)

        self.assertEqual(content, file_content)

    @patch('subprocess.run')
    def test_read_file_at_commit_failure(self, mock_subprocess):
        error_msg = f"fatal: {uuid.uuid4().hex}"
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = error_msg
        mock_subprocess.return_value = mock_result

        inspector = GitInspector(repo_path=self.repo_path)
        with self.assertRaises(Exception) as ctx:
            inspector.read_file_at_commit(self.commit_hash, self.file_path)

        self.assertIn(error_msg, str(ctx.exception))

    def test_read_file_stream(self):
        file_content = uuid.uuid4().hex
        inspector = GitInspector(repo_path=self.repo_path)

        with patch.object(inspector, 'read_file_at_commit', return_value=file_content) as mock_read:
            stream = inspector.read_file_stream(self.commit_hash, self.file_path)
            self.assertIsInstance(stream, io.BytesIO)
            self.assertEqual(stream.read().decode('utf-8'), file_content)
            mock_read.assert_called_once_with(self.commit_hash, self.file_path)

    @patch('subprocess.run')
    def test_get_commit_history(self, mock_subprocess):
        commit_line = f"{uuid.uuid4().hex} - {uuid.uuid4().hex}"
        mock_result = MagicMock()
        mock_result.stdout = f"{commit_line}\n"
        mock_subprocess.return_value = mock_result

        inspector = GitInspector(repo_path=self.repo_path)
        history = inspector.get_commit_history(max_count=random.randint(1, 20))

        self.assertEqual(history, [commit_line])

    @patch('subprocess.run')
    def test_get_file_diff(self, mock_subprocess):
        diff_output = uuid.uuid4().hex
        mock_result = MagicMock()
        mock_result.stdout = diff_output
        mock_subprocess.return_value = mock_result

        inspector = GitInspector(repo_path=self.repo_path)
        res = inspector.get_file_diff(commit_hash=self.commit_hash)

        self.assertEqual(res, diff_output)

    @patch('subprocess.run')
    def test_get_latest_changes_with_diff(self, mock_subprocess):
        diff_output = uuid.uuid4().hex
        mock_result = MagicMock()
        mock_result.stdout = diff_output
        mock_subprocess.return_value = mock_result

        inspector = GitInspector(repo_path=self.repo_path)
        res = inspector.get_latest_changes()

        self.assertEqual(res, diff_output)

    @patch('subprocess.run')
    def test_get_latest_changes_fallback_to_show(self, mock_subprocess):
        show_output = uuid.uuid4().hex

        def side_effect(cmd, *args, **kwargs):
            res = MagicMock()
            if "diff" in cmd:
                res.stdout = ""
            else:
                res.stdout = show_output
            return res

        mock_subprocess.side_effect = side_effect

        inspector = GitInspector(repo_path=self.repo_path)
        res = inspector.get_latest_changes()

        self.assertEqual(res, show_output)

    def test_lesson_parser_init_default(self):
        parser = LessonParser(repo_path=self.repo_path)
        self.assertIsInstance(parser.git_inspector, GitInspector)
        self.assertEqual(parser.git_inspector.repo_path, self.repo_path)

    def test_lesson_parser_init_custom_inspector(self):
        mock_inspector = MagicMock(spec=GitInspector)
        parser = LessonParser(git_inspector=mock_inspector)
        self.assertEqual(parser.git_inspector, mock_inspector)

    def test_parse_lesson_file(self):
        content = f"# {self.title_text}\nLesson ID: {self.lesson_id}\nSome body text {uuid.uuid4().hex}"
        mock_inspector = MagicMock(spec=GitInspector)
        mock_inspector.read_file_at_commit.return_value = content

        parser = LessonParser(git_inspector=mock_inspector)
        parsed = parser.parse_lesson_file(self.commit_hash, self.file_path)

        self.assertEqual(parsed["lesson_id"], self.lesson_id)
        self.assertEqual(parsed["title"], f"# {self.title_text}")
        self.assertEqual(parsed["raw_content"], content)
        mock_inspector.read_file_at_commit.assert_called_once_with(self.commit_hash, self.file_path)

    def test_parse_lesson_file_missing_meta(self):
        content = f"Just some text without tags {uuid.uuid4().hex}"
        mock_inspector = MagicMock(spec=GitInspector)
        mock_inspector.read_file_at_commit.return_value = content

        parser = LessonParser(git_inspector=mock_inspector)
        parsed = parser.parse_lesson_file(self.commit_hash, self.file_path)

        self.assertEqual(parsed["lesson_id"], "unknown")
        self.assertEqual(parsed["title"], "Lesson unknown")
        self.assertEqual(parsed["raw_content"], content)

    def test_parse_stream(self):
        file_content = uuid.uuid4().hex
        mock_inspector = MagicMock(spec=GitInspector)
        mock_inspector.read_file_stream.return_value = io.BytesIO(file_content.encode('utf-8'))

        parser = LessonParser(git_inspector=mock_inspector)
        res = parser.parse_stream(self.commit_hash, self.file_path)

        self.assertEqual(res, file_content)
        mock_inspector.read_file_stream.assert_called_once_with(self.commit_hash, self.file_path)

    def test_extract_history_context(self):
        c1 = f"{uuid.uuid4().hex} - {uuid.uuid4().hex}"
        c2 = f"{uuid.uuid4().hex} - {uuid.uuid4().hex}"
        diff1 = uuid.uuid4().hex
        diff2 = uuid.uuid4().hex

        mock_inspector = MagicMock(spec=GitInspector)
        mock_inspector.get_commit_history.return_value = [c1, c2]
        mock_inspector.get_file_diff.side_effect = [diff1, diff2]

        parser = LessonParser(git_inspector=mock_inspector)
        context = parser.extract_history_context(self.file_path)

        self.assertIn(diff1, context)
        self.assertIn(diff2, context)
        mock_inspector.get_commit_history.assert_called_once_with(max_count=10)
        mock_inspector.get_file_diff.assert_any_call(c1.split()[0])
        mock_inspector.get_file_diff.assert_any_call(c2.split()[0])

    def test_parse_lesson_context(self):
        raw = uuid.uuid4().hex
        parser = LessonParser(repo_path=self.repo_path)
        self.assertEqual(parser.parse_lesson_context(raw), raw)

if __name__ == '__main__':
    unittest.main()