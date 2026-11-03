import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os
from skills.repo_monitor import GitCommitter

class TestGitCommitter(unittest.TestCase):
    def setUp(self):
        self.random_repo = os.path.join(
            ''.join(random.choices(string.ascii_lowercase, k=8)),
            ''.join(random.choices(string.ascii_lowercase, k=6))
        )
        self.committer = GitCommitter(self.random_repo)

    def test_init_sets_repo_path(self):
        self.assertEqual(self.committer.repo_path, self.random_repo)

    def test_commit_success(self):
        random_msg = f"commit_{uuid.uuid4().hex}"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = self.committer.commit(random_msg)
            
            self.assertTrue(result)
            mock_run.assert_called()
            called_args = mock_run.call_args[0][0]
            self.assertIn(random_msg, called_args)

    def test_commit_failure(self):
        random_msg = f"failed_commit_{uuid.uuid4().hex}"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=random.randint(1, 255))
            
            result = self.committer.commit(random_msg)
            
            self.assertFalse(result)

    def test_commit_changes_success(self):
        random_file = f"{uuid.uuid4().hex}.{random.choice(['py', 'txt', 'md']) }"
        random_msg = f"msg_{uuid.uuid4().hex}"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = self.committer.commit_changes(random_file, random_msg)
            
            self.assertTrue(result)
            self.assertGreaterEqual(mock_run.call_count, 2)
            
            all_calls_args = [call[0][0] for call in mock_run.call_args_list]
            file_add_called = any(random_file in ' '.join(args) for args in all_calls_args)
            msg_commit_called = any(random_msg in ' '.join(args) for args in all_calls_args)
            
            self.assertTrue(file_add_called)
            self.assertTrue(msg_commit_called)

    def test_commit_changes_add_fails(self):
        random_file = f"{uuid.uuid4().hex}.py"
        random_msg = f"msg_{uuid.uuid4().hex}"
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=random.randint(1, 255)),
                MagicMock(returncode=0)
            ]
            
            result = self.committer.commit_changes(random_file, random_msg)
            
            self.assertFalse(result)

    def test_commit_changes_commit_fails(self):
        random_file = f"{uuid.uuid4().hex}.py"
        random_msg = f"msg_{uuid.uuid4().hex}"
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=0),
                MagicMock(returncode=random.randint(1, 255))
            ]
            
            result = self.committer.commit_changes(random_file, random_msg)
            
            self.assertFalse(result)

    def test_commit_exception_handling(self):
        random_msg = f"exc_{uuid.uuid4().hex}"
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception(uuid.uuid4().hex)
            
            result = self.committer.commit(random_msg)
            
            self.assertFalse(result)

    def test_commit_changes_exception_handling(self):
        random_file = f"{uuid.uuid4().hex}.py"
        random_msg = f"exc_{uuid.uuid4().hex}"
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception(uuid.uuid4().hex)
            
            result = self.committer.commit_changes(random_file, random_msg)
            
            self.assertFalse(result)