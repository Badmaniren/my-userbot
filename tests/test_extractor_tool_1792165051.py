import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from skills.extractor_tool_1792165051 import (
    AnomalyDetectorError,
    AutonomousEngineError,
    CodeSanitizerError,
    CodeValidatorError,
    GitInspector,
    HypothesisGeneratorError,
    LessonParserError,
    PatchAutocorrectorError,
    PatchExecutorError,
    StabilityDigestError,
    SystemTelemetryError
)


class TestArchitectInquisitorExtractorTool(unittest.TestCase):

    def setUp(self):
        self.rand_prefix = uuid.uuid4().hex[:8]
        self.rand_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.py"
        self.rand_hash = uuid.uuid4().hex

    def test_exceptions_hierarchy_and_raising(self):
        exc_classes = [
            AnomalyDetectorError,
            AutonomousEngineError,
            CodeSanitizerError,
            CodeValidatorError,
            HypothesisGeneratorError,
            LessonParserError,
            PatchAutocorrectorError,
            PatchExecutorError,
            StabilityDigestError,
            SystemTelemetryError
        ]
        
        for exc_cls in exc_classes:
            msg = f"{self.rand_prefix}_{uuid.uuid4().hex}"
            with self.subTest(exc=exc_cls):
                try:
                    raise exc_cls(msg)
                except exc_cls as e:
                    self.assertIn(msg, str(e))
                except Exception as ex:
                    self.fail(f"Exception {exc_cls} raised unexpected base exception: {ex}")

    @patch('skills.extractor_tool_1792165051.subprocess.Popen')
    def test_git_inspector_initialization_and_repo_path(self, mock_popen):
        inspector = GitInspector(self.rand_path)
        self.assertEqual(inspector.repo_path, self.rand_path)

    @patch('skills.extractor_tool_1792165051.subprocess.run')
    def test_git_inspector_get_commit_history_random_payload(self, mock_run):
        random_count = random.randint(1, 100)
        expected_output = f"commit {self.rand_hash}\nAuthor: {uuid.uuid4().hex} <{uuid.uuid4().hex}@test.com>\nDate:   {random.randint(1000, 9999)}"
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = expected_output
        mock_run.return_value = mock_result

        inspector = GitInspector(self.rand_path)
        history = inspector.get_commit_history(max_count=random_count)
        
        self.assertIn(self.rand_hash, history)
        mock_run.assert_called_once()
        args_used = mock_run.call_args[0][0]
        self.assertIn(str(random_count), args_used)

    @patch('skills.extractor_tool_1792165051.subprocess.run')
    def test_git_inspector_get_file_diff_semantic(self, mock_run):
        diff_marker = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = diff_marker
        mock_run.return_value = mock_result

        inspector = GitInspector(self.rand_path)
        diff_result = inspector.get_file_diff(self.rand_hash)

        self.assertEqual(diff_result, diff_marker)
        mock_run.assert_called_once()

    @patch('skills.extractor_tool_1792165051.subprocess.run')
    def test_git_inspector_analyze_repository_entropy(self, mock_run):
        analysis_data = f"repo_stats_{uuid.uuid4().hex}"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = analysis_data
        mock_run.return_value = mock_result

        inspector = GitInspector(self.rand_path)
        result = inspector.analyze_repository()

        self.assertIsInstance(result, (str, dict, list))

    def test_git_inspector_read_file_at_commit_io_stream(self):
        file_target = f"src/{uuid.uuid4().hex}.py"
        random_content = "".join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        
        with patch('skills.extractor_tool_1792165051.subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = random_content.decode('utf-8')
            mock_run.return_value = mock_result

            inspector = GitInspector(self.rand_path)
            content = inspector.read_file_at_commit(self.rand_hash, file_target)
            
            self.assertIn(random_content.decode('utf-8'), content)

    @patch('skills.extractor_tool_1792165051.subprocess.run')
    def test_git_inspector_get_history_and_latest_changes(self, mock_run):
        random_history_chunk = f"commit_node_{uuid.uuid4().hex}"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = random_history_chunk
        mock_run.return_value = mock_result

        inspector = GitInspector(self.rand_path)
        
        hist = inspector.get_history()
        self.assertIsNotNone(hist)

        latest = inspector.get_latest_changes()
        self.assertIsNotNone(latest)

    def test_git_inspector_io_edge_case_bytes_handling(self):
        random_trash = b'\xff\xfe\x00\x01' + uuid.uuid4().bytes
        stream = io.BytesIO(random_trash)
        
        with patch('skills.extractor_tool_1792165051.open', return_value=stream, create=True):
            inspector = GitInspector(self.rand_path)
            self.assertEqual(inspector.repo_path, self.rand_path)


if __name__ == '__main__':
    unittest.main()