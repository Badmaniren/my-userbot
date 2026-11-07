import unittest
from unittest.mock import patch, mock_open
import json
import uuid
import random
import requests
import io

from skills.repo_security_scanner import start_new


class TestRepoSecurityScannerStartNew(unittest.TestCase):

    def test_start_new_success_without_token(self):
        rand_url = f"https://api.github.com/v{random.randint(1,9)}/{uuid.uuid4().hex}"
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        mock_response_data = {rand_key: rand_val}

        with patch("requests.post") as mock_post:
            mock_resp = mock_post.return_value
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_response_data

            result = start_new(repo_url=rand_url)

            mock_post.assert_called_once_with(
                "https://api.github.com/v1/security/scan",
                json={"repository": rand_url},
                headers={},
                timeout=30
            )
            self.assertEqual(result, mock_response_data)

    def test_start_new_success_with_token_and_output(self):
        rand_url = f"https://api.github.com/repo/{uuid.uuid4().hex}"
        rand_token = uuid.uuid4().hex
        rand_path = f"/tmp/{uuid.uuid4().hex}.json"
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        mock_response_data = {rand_key: rand_val}

        with patch("requests.post") as mock_post, patch("builtins.open", new_callable=mock_open()) as mock_file:
            mock_resp = mock_post.return_value
            mock_resp.status_code = 201
            mock_resp.json.return_value = mock_response_data

            result = start_new(repo_url=rand_url, api_token=rand_token, output_path=rand_path)

            mock_post.assert_called_once_with(
                "https://api.github.com/v1/security/scan",
                json={"repository": rand_url},
                headers={"Authorization": f"Bearer {rand_token}"},
                timeout=30
            )
            mock_file.assert_called_once_with(rand_path, "w", encoding="utf-8")
            handle = mock_file()
            handle.write.assert_called()
            self.assertEqual(result, mock_response_data)

    def test_start_new_invalid_json(self):
        rand_url = f"https://api.github.com/repo/{uuid.uuid4().hex}"
        rand_status = random.choice([200, 201, 400, 500])

        with patch("requests.post") as mock_post:
            mock_resp = mock_post.return_value
            mock_resp.status_code = rand_status
            mock_resp.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)

            result = start_new(repo_url=rand_url)

            self.assertEqual(result, {
                "error": "Invalid JSON response",
                "status_code": rand_status
            })

    def test_start_new_request_failed(self):
        rand_url = f"https://api.github.com/repo/{uuid.uuid4().hex}"
        rand_status = random.randint(400, 599)
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        err_data = {rand_key: rand_val}

        with patch("requests.post") as mock_post:
            mock_resp = mock_post.return_value
            mock_resp.status_code = rand_status
            mock_resp.json.return_value = err_data

            result = start_new(repo_url=rand_url)

            self.assertEqual(result, {
                "error": "Request failed",
                "status_code": rand_status,
                "data": err_data
            })

    def test_start_new_connection_error(self):
        rand_url = f"https://api.github.com/repo/{uuid.uuid4().hex}"
        rand_msg = uuid.uuid4().hex

        with patch("requests.post", side_effect=requests.exceptions.ConnectionError(rand_msg)):
            with self.assertRaises(Exception) as ctx:
                start_new(repo_url=rand_url)
            self.assertIn(f"Connection error: {rand_msg}", str(ctx.exception))

    def test_start_new_request_exception(self):
        rand_url = f"https://api.github.com/repo/{uuid.uuid4().hex}"
        rand_msg = uuid.uuid4().hex

        with patch("requests.post", side_effect=requests.exceptions.RequestException(rand_msg)):
            with self.assertRaises(Exception) as ctx:
                start_new(repo_url=rand_url)
            self.assertIn(f"Network error: {rand_msg}", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()