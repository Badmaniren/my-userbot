import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import subprocess
from skills.git_inspector import GitInspector

class TestGitInspector(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.inspector = GitInspector(self.repo_path)

    def test_get_commit_history_success(self):
        random_hash = uuid.uuid4().hex[:7]
        random_author = ''.join(random.choices(string.ascii_letters, k=10))
        random_message = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        mock_git_output = f"{random_hash}|{random_author}|{random_message}\n"

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_git_output.encode('utf-8')
            )
            
            max_count = random.randint(1, 50)
            history = self.inspector.get_commit_history(max_count=max_count)

            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]['hash'], random_hash)
            self.assertEqual(history[0]['author'], random_author)
            self.assertEqual(history[0]['message'], random_message)
            mock_run.assert_called_once()

    def test_get_commit_history_subprocess_error(self):
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=random.randint(1, 255),
                cmd=['git', 'log']
            )
            
            history = self.inspector.get_commit_history()
            self.assertEqual(history, [])

    def test_get_file_diff_success(self):
        random_filename = f"{uuid.uuid4().hex}.py"
        random_diff_line = f"+def {uuid.uuid4().hex}():"
        mock_git_output = f"diff --git a/{random_filename} b/{random_filename}\n{random_diff_line}\n"

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_git_output.encode('utf-8')
            )

            random_commit_hash = uuid.uuid4().hex[:10]
            diff = self.inspector.get_file_diff(random_commit_hash)

            self.assertIn(random_filename, diff)
            self.assertIn(random_diff_line, diff)
            mock_run.assert_called_once()

    def test_analyze_repository_metrics(self):
        random_file_count = random.randint(5, 100)
        random_commit_count = random.randint(10, 500)

        with patch.object(self.inspector, 'get_commit_history') as mock_history:
            mock_history.return_value = [{'hash': uuid.uuid4().hex} for _ in range(random_commit_count)]
            
            with patch('os.walk') as mock_walk:
                mock_walk.return_value = [
                    (self.repo_path, [], [f"{uuid.uuid4().hex}.py" for _ in range(random_file_count)])
                ]

                metrics = self.inspector.analyze_repository()

                self.assertEqual(metrics['total_commits'], random_commit_count)
                self.assertEqual(metrics['total_files'], random_file_count)
                self.assertEqual(metrics['repo_path'], self.repo_path)

    def test_read_file_at_commit(self):
        random_commit = uuid.uuid4().hex[:8]
        random_path = f"{uuid.uuid4().hex}.txt"
        random_content = ''.join(random.choices(string.ascii_letters, k=50))

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=random_content.encode('utf-8')
            )

            content = self.inspector.read_file_at_commit(random_commit, random_path)

            self.assertEqual(content, random_content)
            mock_run.assert_called_once()