import unittest
from unittest.mock import patch, MagicMock
import subprocess
import os
import uuid
import random
import string
from skills.git_committer import GitCommitter

class TestGitCommitter(unittest.TestCase):

    def setUp(self):
        self.random_repo = f"/tmp/{uuid.uuid4().hex}"
        self.committer = GitCommitter(self.random_repo)

    def test_commit_success(self):
        random_msg = f"feat: {uuid.uuid4().hex[:8]}"
        
        with patch("subprocess.run") as mock_run:
            mock_process_add = MagicMock()
            mock_process_add.returncode = 0
            
            mock_process_commit = MagicMock()
            mock_process_commit.returncode = 0
            
            mock_run.side_effect = [mock_process_add, mock_process_commit]
            
            result = self.committer.commit(random_msg)
            
            self.assertTrue(result)
            self.assertEqual(mock_run.call_count, 2)
            mock_run.assert_any_call(
                ["git", "-C", self.random_repo, "add", "."],
                capture_output=True,
                text=True,
                check=True
            )
            mock_run.assert_any_call(
                ["git", "-C", self.random_repo, "commit", "-m", random_msg],
                capture_output=True,
                text=True,
                check=True
            )

    def test_commit_subprocess_exception(self):
        random_msg = f"fix: {uuid.uuid4().hex[:8]}"
        random_err_msg = f"error_{uuid.uuid4().hex}"
        
        exceptions_to_test = [
            subprocess.CalledProcessError(random.randint(1, 255), ["git"], random_err_msg),
            subprocess.TimeoutExpired(["git"], random.uniform(0.1, 5.0)),
            OSError(random.randint(1, 100), f"OS Error {uuid.uuid4().hex}")
        ]
        
        for exc in exceptions_to_test:
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = exc
                
                result = self.committer.commit(random_msg)
                
                self.assertFalse(result)

    def test_commit_changes_file_not_exists(self):
        random_file = f"{uuid.uuid4().hex}.txt"
        random_msg = f"docs: {uuid.uuid4().hex[:8]}"
        
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            
            with patch("subprocess.run") as mock_run:
                result = self.committer.commit_changes(random_file, random_msg)
                
                self.assertFalse(result)
                mock_run.assert_not_called()

    def test_commit_changes_success(self):
        random_file = f"src/{uuid.uuid4().hex}/{uuid.uuid4().hex}.py"
        random_msg = f"refactor: {uuid.uuid4().hex[:8]}"
        
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            
            with patch("subprocess.run") as mock_run:
                mock_process_add = MagicMock()
                mock_process_add.returncode = 0
                
                mock_process_commit = MagicMock()
                mock_process_commit.returncode = 0
                
                mock_run.side_effect = [mock_process_add, mock_process_commit]
                
                result = self.committer.commit_changes(random_file, random_msg)
                
                self.assertTrue(result)
                self.assertEqual(mock_run.call_count, 2)
                mock_run.assert_any_call(
                    ["git", "-C", self.random_repo, "add", random_file],
                    capture_output=True,
                    text=True,
                    check=True
                )
                mock_run.assert_any_call(
                    ["git", "-C", self.random_repo, "commit", "-m", random_msg],
                    capture_output=True,
                    text=True,
                    check=True
                )

    def test_commit_changes_subprocess_exception(self):
        random_file = f"{uuid.uuid4().hex}.log"
        random_msg = f"chore: {uuid.uuid4().hex[:8]}"
        
        exceptions_to_test = [
            subprocess.CalledProcessError(random.randint(1, 255), ["git"], "fail"),
            subprocess.TimeoutExpired(["git"], random.uniform(1.0, 10.0)),
            OSError(random.randint(1, 50), "Disk error")
        ]
        
        for exc in exceptions_to_test:
            with patch("os.path.exists") as mock_exists:
                mock_exists.return_value = True
                
                with patch("subprocess.run") as mock_run:
                    mock_run.side_effect = exc
                    
                    result = self.committer.commit_changes(random_file, random_msg)
                    
                    self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()