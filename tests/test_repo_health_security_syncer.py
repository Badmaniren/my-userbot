import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import json
import io
import hashlib
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncer(unittest.TestCase):
    def setUp(self):
        self.repo_id = str(uuid.uuid4())
        self.health_url = f"https://api.github.test/{uuid.uuid4().hex}/health"
        self.security_url = f"https://api.github.test/{uuid.uuid4().hex}/security"
        self.target_directory = f"./test_audit_dir_{uuid.uuid4().hex}"
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            health_url=self.health_url,
            security_url=self.security_url,
            target_directory=self.target_directory
        )

    def tearDown(self):
        if os.path.exists(self.target_directory):
            for file_name in os.listdir(self.target_directory):
                file_path = os.path.join(self.target_directory, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.target_directory)

    def test_synchronize_with_payload_success(self):
        sync_id = str(uuid.uuid4())
        token = uuid.uuid4().hex
        health_score = random.randint(50, 100)
        vulnerabilities = random.randint(0, 5)
        security_score = random.randint(10, 99)

        metric_payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "vulnerabilities": vulnerabilities,
            "security_score": security_score
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            result = self.syncer.synchronize(metric_payload=metric_payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)
        self.assertEqual(result["health_data"]["health_score"], health_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)
        self.assertEqual(result["security_data"]["token"], token)
        self.assertEqual(result["security_data"]["security_score"], security_score)

        expected_file_path = os.path.join(self.target_directory, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))
        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
        self.assertEqual(file_data["correlation_id"], sync_id)
        self.assertEqual(file_data["health_metrics"]["health_score"], health_score)
        self.assertEqual(file_data["security_metrics"]["vulnerabilities"], vulnerabilities)

    def test_synchronize_with_payload_token_mismatch(self):
        sync_id = str(uuid.uuid4())
        token = uuid.uuid4().hex
        env_token = uuid.uuid4().hex

        metric_payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": random.randint(1, 100),
            "vulnerabilities": random.randint(0, 10)
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = self.syncer.synchronize(metric_payload=metric_payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], sync_id)

    def test_synchronize_network_success(self):
        health_data_mock = {"health_status": uuid.uuid4().hex, "score": random.randint(1, 100)}
        security_data_mock = {"security_status": uuid.uuid4().hex, "vulns": random.randint(0, 5)}

        mock_health_response = MagicMock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = health_data_mock

        mock_security_response = MagicMock()
        mock_security_response.status_code = 200
        mock_security_response.json.return_value = security_data_mock

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_response, mock_security_response]
            result = self.syncer.synchronize()

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"], health_data_mock)
        self.assertEqual(result["security_data"], security_data_mock)

    def test_synchronize_health_fail(self):
        status_code = random.choice([400, 401, 403, 404, 500, 502])
        error_text = uuid.uuid4().hex

        mock_health_response = MagicMock()
        mock_health_response.status_code = status_code
        mock_health_response.text = error_text

        with patch("requests.get", return_value=mock_health_response) as mock_get:
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], status_code)
        self.assertIn(str(status_code), result["error"])
        self.assertIn(error_text, result["error"])

    def test_synchronize_security_fail(self):
        health_data_mock = {"status": "ok"}
        status_code = random.choice([400, 404, 500, 503])
        error_text = uuid.uuid4().hex

        mock_health_response = MagicMock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = health_data_mock

        mock_security_response = MagicMock()
        mock_security_response.status_code = status_code
        mock_security_response.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_response, mock_security_response]
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], status_code)
        self.assertIn(str(status_code), result["error"])
        self.assertIn(error_text, result["error"])

    def test_synchronize_exception(self):
        exception_msg = uuid.uuid4().hex

        with patch("requests.get", side_effect=Exception(exception_msg)) as mock_get:
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertEqual(result["error"], exception_msg)

    def test_export_audit_stream_with_raw(self):
        random_bytes = os.urandom(random.randint(16, 128))
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        bytes_len = len(random_bytes)

        mock_raw_stream = io.BytesIO(random_bytes)
        mock_response = MagicMock()
        mock_response.raw = mock_raw_stream

        with patch("requests.get", return_value=mock_response) as mock_get:
            stream_result = self.syncer.export_audit_stream()

        self.assertEqual(stream_result["stream_hash"], expected_hash)
        self.assertEqual(stream_result["bytes_read"], bytes_len)

    def test_export_audit_stream_with_content_fallback(self):
        random_bytes = os.urandom(random.randint(16, 128))
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        bytes_len = len(random_bytes)

        mock_response = MagicMock()
        mock_response.raw = None
        mock_response.content = random_bytes

        with patch("requests.get", return_value=mock_response) as mock_get:
            stream_result = self.syncer.export_audit_stream()

        self.assertEqual(stream_result["stream_hash"], expected_hash)
        self.assertEqual(stream_result["bytes_read"], bytes_len)