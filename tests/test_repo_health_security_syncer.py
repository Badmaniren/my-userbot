import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import hashlib
import json
import random
import io
import requests

from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncer(unittest.TestCase):
    def setUp(self):
        self.repo_id = str(uuid.uuid4())
        self.health_url = f"http://{uuid.uuid4().hex}.local/health"
        self.security_url = f"http://{uuid.uuid4().hex}.local/security"
        self.target_directory = f"./{uuid.uuid4().hex}_audit"
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            health_url=self.health_url,
            security_url=self.security_url,
            target_directory=self.target_directory
        )

    def tearDown(self):
        if os.path.exists(self.target_directory):
            for f in os.listdir(self.target_directory):
                try:
                    os.remove(os.path.join(self.target_directory, f))
                except Exception:
                    pass
            try:
                os.rmdir(self.target_directory)
            except Exception:
                pass

    def test_synchronize_with_payload_success(self):
        sync_id = str(uuid.uuid4())
        token = uuid.uuid4().hex
        health_score = random.randint(50, 100)
        vulnerabilities = random.randint(0, 5)
        security_score = random.randint(10, 100)

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "vulnerabilities": vulnerabilities,
            "security_score": security_score
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)
        self.assertEqual(result["health_data"]["health_score"], health_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)
        self.assertEqual(result["security_data"]["token"], token)
        self.assertEqual(result["security_data"]["security_score"], security_score)

        expected_file_name = f"audit_{sync_id}.json"
        expected_file_path = os.path.join(self.target_directory, expected_file_name)
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["correlation_id"], sync_id)
            self.assertEqual(data["health_metrics"]["health_score"], health_score)
            self.assertEqual(data["security_metrics"]["vulnerabilities"], vulnerabilities)

    def test_synchronize_with_payload_invalid_token(self):
        sync_id = str(uuid.uuid4())
        token = uuid.uuid4().hex
        wrong_token = uuid.uuid4().hex

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": random.randint(0, 100),
            "vulnerabilities": random.randint(0, 10),
            "security_score": random.randint(0, 100)
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": wrong_token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], sync_id)

    def test_synchronize_remote_success(self):
        health_data_mock = {"status": uuid.uuid4().hex, "score": random.randint(0, 100)}
        security_data_mock = {"status": uuid.uuid4().hex, "vulnerabilities": []}

        mock_health_response = MagicMock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = health_data_mock

        mock_security_response = MagicMock()
        mock_security_response.status_code = 200
        mock_security_response.json.return_value = security_data_mock

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_response, mock_security_response]
            result = self.syncer.synchronize(metric_payload=None)

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"], health_data_mock)
        self.assertEqual(result["security_data"], security_data_mock)
        self.assertEqual(mock_get.call_count, 2)

    def test_synchronize_remote_health_failure(self):
        status_code = random.choice([400, 401, 403, 404, 500, 502])
        error_text = uuid.uuid4().hex

        mock_health_response = MagicMock()
        mock_health_response.status_code = status_code
        mock_health_response.text = error_text

        with patch("requests.get", return_value=mock_health_response) as mock_get:
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], status_code)
        self.assertIn(str(status_code), result["error"])
        self.assertIn(error_text, result["error"])

    def test_synchronize_remote_security_failure(self):
        health_data_mock = {"status": uuid.uuid4().hex}
        status_code = random.choice([400, 401, 403, 404, 500, 503])
        error_text = uuid.uuid4().hex

        mock_health_response = MagicMock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = health_data_mock

        mock_security_response = MagicMock()
        mock_security_response.status_code = status_code
        mock_security_response.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_response, mock_security_response]
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], status_code)
        self.assertIn(str(status_code), result["error"])
        self.assertIn(error_text, result["error"])

    def test_synchronize_exception_handling(self):
        exception_message = uuid.uuid4().hex

        with patch("requests.get", side_effect=Exception(exception_message)) as mock_get:
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertEqual(result["error"], exception_message)

    def test_export_audit_stream_with_raw(self):
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_bytes_read = len(random_bytes)

        mock_response = MagicMock()
        mock_raw = io.BytesIO(random_bytes)
        mock_response.raw = mock_raw

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = self.syncer.export_audit_stream()

        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], expected_bytes_read)

    def test_export_audit_stream_without_raw(self):
        random_bytes = uuid.uuid4().bytes
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_bytes_read = len(random_bytes)

        mock_response = MagicMock(spec=["content"])
        mock_response.content = random_bytes
        del mock_response.raw

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = self.syncer.export_audit_stream()

        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], expected_bytes_read)

if __name__ == "__main__":
    unittest.main()