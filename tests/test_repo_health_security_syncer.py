import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import string
import json
import io
import requests

from skills.repo_health_security_syncer import RepoHealthSecuritySyncer


class TestRepoHealthSecuritySyncer(unittest.TestCase):

    def setUp(self):
        self.random_repo_id = uuid.uuid4().hex
        self.random_health_url = f"http://{uuid.uuid4().hex}.local/health"
        self.random_security_url = f"http://{uuid.uuid4().hex}.local/security"
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.random_repo_id,
            health_url=self.random_health_url,
            security_url=self.random_security_url
        )

    def test_synchronize_with_payload_success(self):
        random_sync_id = uuid.uuid4().hex
        random_token = uuid.uuid4().hex
        random_health_score = random.randint(1, 100)
        random_vulnerabilities = random.randint(0, 10)
        random_security_score = random.randint(1, 100)

        payload = {
            "sync_id": random_sync_id,
            "token": random_token,
            "health_score": random_health_score,
            "vulnerabilities": random_vulnerabilities,
            "security_score": random_security_score
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": random_token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], random_sync_id)
        self.assertEqual(result["health_data"]["health_score"], random_health_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], random_vulnerabilities)
        self.assertEqual(result["security_data"]["security_score"], random_security_score)
        self.assertEqual(result["security_data"]["token"], random_token)

    def test_synchronize_with_payload_invalid_token(self):
        random_sync_id = uuid.uuid4().hex
        random_token = uuid.uuid4().hex
        env_token = uuid.uuid4().hex

        payload = {
            "sync_id": random_sync_id,
            "token": random_token,
            "health_score": random.randint(1, 100),
            "vulnerabilities": random.randint(0, 10),
            "security_score": random.randint(1, 100)
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], random_sync_id)

    def test_synchronize_with_target_directory(self):
        random_dir = os.path.join("/tmp", uuid.uuid4().hex)
        random_sync_id = uuid.uuid4().hex
        random_health_score = random.randint(1, 100)
        random_vulnerabilities = random.randint(0, 10)

        syncer_with_dir = RepoHealthSecuritySyncer(
            repo_id=self.random_repo_id,
            target_directory=random_dir
        )

        payload = {
            "sync_id": random_sync_id,
            "health_score": random_health_score,
            "vulnerabilities": random_vulnerabilities
        }

        expected_file_name = f"audit_{random_sync_id}.json"
        expected_file_path = os.path.join(random_dir, expected_file_name)

        try:
            result = syncer_with_dir.synchronize(metric_payload=payload)
            self.assertTrue(result["success"])
            self.assertTrue(os.path.exists(expected_file_path))

            with open(expected_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.assertEqual(data["correlation_id"], random_sync_id)
                self.assertEqual(data["health_metrics"]["health_score"], random_health_score)
                self.assertEqual(data["security_metrics"]["vulnerabilities"], random_vulnerabilities)
        finally:
            if os.path.exists(expected_file_path):
                os.remove(expected_file_path)
            if os.path.exists(random_dir):
                os.rmdir(random_dir)

    def test_synchronize_remote_success(self):
        random_health_data = {uuid.uuid4().hex: random.randint(1, 100)}
        random_security_data = {uuid.uuid4().hex: random.randint(1, 100)}

        mock_health_response = MagicMock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = random_health_data

        mock_security_response = MagicMock()
        mock_security_response.status_code = 200
        mock_security_response.json.return_value = random_security_data

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_response, mock_security_response]
            result = self.syncer.synchronize()

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"], random_health_data)
        self.assertEqual(result["security_data"], random_security_data)

    def test_synchronize_remote_health_failure(self):
        random_status_code = random.choice([400, 401, 403, 404, 500, 502, 503])
        random_error_text = uuid.uuid4().hex

        mock_health_response = MagicMock()
        mock_health_response.status_code = random_status_code
        mock_health_response.text = random_error_text

        with patch("requests.get", return_value=mock_health_response):
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], random_status_code)
        self.assertIn(str(random_status_code), result["error"])
        self.assertIn(random_error_text, result["error"])

    def test_synchronize_remote_security_failure(self):
        random_health_data = {uuid.uuid4().hex: random.randint(1, 100)}
        random_status_code = random.choice([400, 401, 403, 404, 500, 502, 503])
        random_error_text = uuid.uuid4().hex

        mock_health_response = MagicMock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = random_health_data

        mock_security_response = MagicMock()
        mock_security_response.status_code = random_status_code
        mock_security_response.text = random_error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_response, mock_security_response]
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], random_status_code)
        self.assertIn(str(random_status_code), result["error"])
        self.assertIn(random_error_text, result["error"])

    def test_synchronize_remote_exception(self):
        random_error_message = uuid.uuid4().hex

        with patch("requests.get", side_effect=Exception(random_error_message)):
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertEqual(result["error"], random_error_message)

    def test_export_audit_stream_with_raw(self):
        random_bytes = uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=64)).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_len = len(random_bytes)

        mock_raw_stream = io.BytesIO(random_bytes)
        mock_response = MagicMock()
        mock_response.raw = mock_raw_stream

        with patch("requests.get", return_value=mock_response):
            result = self.syncer.export_audit_stream()

        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], expected_len)

    def test_export_audit_stream_with_content(self):
        random_bytes = uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=64)).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_len = len(random_bytes)

        mock_response = MagicMock()
        mock_response.raw = None
        mock_response.content = random_bytes

        with patch("requests.get", return_value=mock_response):
            result = self.syncer.export_audit_stream()

        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], expected_len)

if __name__ == "__main__":
    unittest.main()