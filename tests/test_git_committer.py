import unittest
from unittest.mock import patch
import subprocess
import uuid
import random
import io
from skills.git_committer import GitCommitter

class TestGitCommitter(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.committer = GitCommitter(repo_path=self.repo_path)

    def test_commit_success_random_message(self):
        random_branch = uuid.uuid4().hex[:8]
        random_message = f"feat: {uuid.uuid4().hex}"
        random_stdout = f"[{random_branch} {uuid.uuid4().hex[:7]}] {random_message}\n 1 file changed, 1 insertion(+)\n"

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = random_stdout
            mock_run.return_value.stderr = ""

            result = self.committer.commit(random_message)

            self.assertTrue(result)
            self.assertEqual(mock_run.call_count, 2)
            
            commit_call_args = mock_run.call_args_list[1][0][0]
            self.assertIn("commit", commit_call_args)
            self.assertIn(random_message, commit_call_args)

    def test_commit_subprocess_called_process_error(self):
        random_cmd = [uuid.uuid4().hex, uuid.uuid4().hex]
        random_stderr = f"fatal: {uuid.uuid4().hex} error"
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=random.randint(1, 255),
                cmd=random_cmd,
                output=b"",
                stderr=random_stderr.encode('utf-8')
            )

            result = self.committer.commit(uuid.uuid4().hex)

            self.assertFalse(result)

    def test_commit_subprocess_timeout_expired(self):
        random_cmd = [uuid.uuid4().hex]
        random_timeout = random.randint(5, 60)

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(
                cmd=random_cmd,
                timeout=random_timeout
            )

            result = self.committer.commit(uuid.uuid4().hex)

            self.assertFalse(result)

    def test_commit_generic_os_error(self):
        random_error_message = uuid.uuid4().hex

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = OSError(random_error_message)

            result = self.committer.commit(uuid.uuid4().hex)

            self.assertFalse(result)

    def test_commit_handles_io_stream_stdout(self):
        random_message = uuid.uuid4().hex
        random_stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = random_stream_data.read().decode('utf-8')
            mock_run.return_value.stderr = ""

            result = self.committer.commit(random_message)

            self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()