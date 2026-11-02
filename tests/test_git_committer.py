import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
from skills.git_committer import GitCommitter

class TestGitCommitter(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.branch_name = f"feature/{uuid.uuid4().hex[:8]}"
        self.commit_message = f"Auto-commit: {uuid.uuid4().hex}"
        self.file_name = f"{uuid.uuid4().hex}.py"
        self.file_content = f"print('{uuid.uuid4().hex}')"
        self.github_token = f"ghp_{uuid.uuid4().hex}"
        self.repo_owner = f"user_{uuid.uuid4().hex[:6]}"
        self.repo_name = f"repo_{uuid.uuid4().hex[:6]}"
        self.committer = GitCommitter(repo_path=self.repo_path, github_token=self.github_token)

    def test_local_commit_and_push_success(self):
        random_status_output = f"M  {self.file_name}\n".encode('utf-8')
        random_command_output = b""

        mock_subprocess_run = MagicMock()
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stdout=random_command_output),
            MagicMock(returncode=0, stdout=random_command_output),
            MagicMock(returncode=0, stdout=random_status_output),
            MagicMock(returncode=0, stdout=random_command_output),
            MagicMock(returncode=0, stdout=random_command_output)
        ]

        with patch('subprocess.run', mock_subprocess_run):
            result = self.committer.commit_and_push_local(
                files=[self.file_name],
                message=self.commit_message,
                branch=self.branch_name
            )

        self.assertTrue(result)
        self.assertEqual(mock_subprocess_run.call_count, 5)

        called_args_list = [call.args[0] for call in mock_subprocess_run.call_args_list]
        self.assertIn("checkout", called_args_list[0])
        self.assertIn("add", called_args_list[1])
        self.assertIn(self.file_name, called_args_list[1])
        self.assertIn("status", called_args_list[2])
        self.assertIn("commit", called_args_list[3])
        self.assertIn(self.commit_message, called_args_list[3])
        self.assertIn("push", called_args_list[4])

    def test_local_commit_and_push_no_changes(self):
        empty_status_output = b""

        mock_subprocess_run = MagicMock()
        mock_subprocess_run.side_effect = [
            MagicMock(returncode=0, stdout=b""),
            MagicMock(returncode=0, stdout=b""),
            MagicMock(returncode=0, stdout=empty_status_output)
        ]

        with patch('subprocess.run', mock_subprocess_run):
            result = self.committer.commit_and_push_local(
                files=[self.file_name],
                message=self.commit_message,
                branch=self.branch_name
            )

        self.assertFalse(result)
        self.assertEqual(mock_subprocess_run.call_count, 3)

    def test_local_commit_subprocess_exception(self):
        mock_subprocess_run = MagicMock(side_effect=Exception(uuid.uuid4().hex))

        with patch('subprocess.run', mock_subprocess_run):
            result = self.committer.commit_and_push_local(
                files=[self.file_name],
                message=self.commit_message,
                branch=self.branch_name
            )

        self.assertFalse(result)

    def test_github_api_create_file_success(self):
        expected_sha = uuid.uuid4().hex
        api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/contents/{self.file_name}"

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "content": {
                "sha": expected_sha
            }
        }
        mock_response.raw = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))

        with patch('requests.put', return_value=mock_response) as mock_put:
            sha = self.committer.push_via_github_api(
                owner=self.repo_owner,
                repo=self.repo_name,
                file_path=self.file_name,
                content=self.file_content,
                message=self.commit_message,
                branch=self.branch_name
            )

        self.assertEqual(sha, expected_sha)
        mock_put.assert_called_once()
        called_url = mock_put.call_args[0][0]
        self.assertEqual(called_url, api_url)

        called_headers = mock_put.call_args[1]['headers']
        self.assertIn(self.github_token, called_headers.get('Authorization', ''))

    def test_github_api_create_file_failure(self):
        error_message = uuid.uuid4().hex
        mock_response = MagicMock()
        mock_response.status_code = 422
        mock_response.text = error_message
        mock_response.raw = io.BytesIO(error_message.encode('utf-8'))

        with patch('requests.put', return_value=mock_response) as mock_put:
            sha = self.committer.push_via_github_api(
                owner=self.repo_owner,
                repo=self.repo_name,
                file_path=self.file_name,
                content=self.file_content,
                message=self.commit_message,
                branch=self.branch_name
            )

        self.assertIsNone(sha)
        mock_put.assert_called_once()

    def test_github_api_request_exception(self):
        with patch('requests.put', side_effect=Exception(uuid.uuid4().hex)) as mock_put:
            sha = self.committer.push_via_github_api(
                owner=self.repo_owner,
                repo=self.repo_name,
                file_path=self.file_name,
                content=self.file_content,
                message=self.commit_message,
                branch=self.branch_name
            )

        self.assertIsNone(sha)
        mock_put.assert_called_once()
