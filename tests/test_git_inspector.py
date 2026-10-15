import unittest
from unittest.mock import patch, MagicMock
import subprocess
import os
import random
import uuid
import io

from skills.git_inspector import GitInspector

class TestGitInspector(unittest.TestCase):
    def setUp(self):
        self.random_repo_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.inspector = GitInspector(self.random_repo_path)

    @patch('subprocess.run')
    def test_get_commit_history_success(self, mock_subprocess_run):
        rand_hash = uuid.uuid4().hex[:7]
        rand_author = f"Author_{uuid.uuid4().hex[:5]}"
        rand_msg = f"Message_{uuid.uuid4().hex[:8]}"
        mock_output = f"{rand_hash}|{rand_author}|{rand_msg}\n"
        
        mock_result = MagicMock()
        mock_result.stdout = mock_output.encode('utf-8')
        mock_subprocess_run.return_value = mock_result

        rand_max = random.randint(1, 100)
        history = self.inspector.get_commit_history(max_count=rand_max)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['hash'], rand_hash)
        self.assertEqual(history[0]['author'], rand_author)
        self.assertEqual(history[0]['message'], rand_msg)

        mock_subprocess_run.assert_called_once()
        called_args = mock_subprocess_run.call_args[0][0]
        self.assertIn(str(rand_max), called_args)
        self.assertIn(self.random_repo_path, called_args)

    @patch('subprocess.run')
    def test_get_commit_history_empty_output(self, mock_subprocess_run):
        mock_result = MagicMock()
        mock_result.stdout = b""
        mock_subprocess_run.return_value = mock_result

        history = self.inspector.get_commit_history()
        self.assertEqual(history, [])

    @patch('subprocess.run')
    def test_get_commit_history_process_error(self, mock_subprocess_run):
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(random.randint(1, 255), 'git')

        history = self.inspector.get_commit_history()
        self.assertEqual(history, [])

    @patch('subprocess.run')
    def test_get_file_diff_success(self, mock_subprocess_run):
        rand_commit = uuid.uuid4().hex
        rand_diff = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n+{uuid.uuid4().hex}"
        
        mock_result = MagicMock()
        mock_result.stdout = rand_diff.encode('utf-8')
        mock_subprocess_run.return_value = mock_result

        result = self.inspector.get_file_diff(rand_commit)
        self.assertEqual(result, rand_diff)

        called_args = mock_subprocess_run.call_args[0][0]
        self.assertIn(rand_commit, called_args)

    @patch('subprocess.run')
    def test_get_file_diff_error(self, mock_subprocess_run):
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, 'git')
        rand_commit = uuid.uuid4().hex

        result = self.inspector.get_file_diff(rand_commit)
        self.assertEqual(result, "")

    @patch('os.walk')
    @patch('subprocess.run')
    def test_analyze_repository(self, mock_subprocess_run, mock_os_walk):
        rand_hash = uuid.uuid4().hex[:7]
        rand_author = uuid.uuid4().hex[:5]
        rand_msg = uuid.uuid4().hex[:10]
        mock_output = f"{rand_hash}|{rand_author}|{rand_msg}\n"

        mock_result = MagicMock()
        mock_result.stdout = mock_output.encode('utf-8')
        mock_subprocess_run.return_value = mock_result

        rand_files_count = random.randint(1, 15)
        mock_files = [uuid.uuid4().hex for _ in range(rand_files_count)]
        mock_os_walk.return_value = [
            (self.random_repo_path, [uuid.uuid4().hex], mock_files)
        ]

        analysis = self.inspector.analyze_repository()

        self.assertEqual(analysis['total_commits'], 1)
        self.assertEqual(analysis['total_files'], rand_files_count)
        self.assertEqual(analysis['repo_path'], self.random_repo_path)

    @patch('subprocess.run')
    def test_read_file_at_commit_success(self, mock_subprocess_run):
        rand_commit = uuid.uuid4().hex
        rand_filepath = f"src/{uuid.uuid4().hex}.py"
        rand_content = f"print('{uuid.uuid4().hex}')"

        mock_result = MagicMock()
        mock_result.stdout = rand_content.encode('utf-8')
        mock_subprocess_run.return_value = mock_result

        result = self.inspector.read_file_at_commit(rand_commit, rand_filepath)
        self.assertEqual(result, rand_content)

        called_args = mock_subprocess_run.call_args[0][0]
        self.assertIn(f"{rand_commit}:{rand_filepath}", called_args)

    @patch('subprocess.run')
    def test_read_file_at_commit_error(self, mock_subprocess_run):
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, 'git')
        result = self.inspector.read_file_at_commit(uuid.uuid4().hex, uuid.uuid4().hex)
        self.assertEqual(result, "")

    @patch('subprocess.run')
    def test_get_history_alias(self, mock_subprocess_run):
        rand_hash = uuid.uuid4().hex[:7]
        mock_output = f"{rand_hash}|Author|Msg\n"
        mock_result = MagicMock()
        mock_result.stdout = mock_output.encode('utf-8')
        mock_subprocess_run.return_value = mock_result

        history = self.inspector.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['hash'], rand_hash)

        rand_max = random.randint(1, 50)
        history_max = self.inspector.get_history(max_count=rand_max)
        self.assertEqual(len(history_max), 1)

    @patch('subprocess.run')
    def test_get_latest_changes_success(self, mock_subprocess_run):
        rand_output = f"commit {uuid.uuid4().hex}\nAuthor: {uuid.uuid4().hex}\n\n    {uuid.uuid4().hex}"
        mock_result = MagicMock()
        mock_result.stdout = rand_output.encode('utf-8')
        mock_subprocess_run.return_value = mock_result

        result = self.inspector.get_latest_changes()
        self.assertEqual(result, rand_output)

        called_args = mock_subprocess_run.call_args[0][0]
        self.assertIn('HEAD', called_args)

    @patch('subprocess.run')
    def test_get_latest_changes_error(self, mock_subprocess_run):
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, 'git')
        result = self.inspector.get_latest_changes()
        self.assertEqual(result, "")

if __name__ == '__main__':
    unittest.main()