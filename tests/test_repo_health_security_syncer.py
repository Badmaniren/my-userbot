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
        self.repo_id = str(uuid.uuid4())
        self.health_url = f"http://{uuid.uuid4().hex}.local/health"
        self.security_url = f"http://{uuid.uuid4().hex}.local/security"
        self.target_directory = f"./test_audit_dir_{uuid.uuid4().hex[:8]}"
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            health_url=self.health_url,
            security_url=self.security_url,
            target_directory=self.target_directory
        )

    def tearDown(self):
        if os.path.exists(self.target_directory):
            for file in os.listdir(self.target_directory):
                file_path = os.path.join(self.target_directory, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    os.rmdir(file_path)
            os.rmdir(self.target_directory)

    def test_synchronize_with_payload_success_token_match(self):
        sync_id = str(uuid.uuid4())
        token = uuid.uuid4().hex
        health_score = random.randint(1, 100)
        vulnerabilities = random.randint(0, 10)
        security_score = random.randint(1, 100)

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

        expected_file_path = os.path.join(self.target_directory, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))
        with open(expected_file_path, "r", encoding="utf-8") as f:
            audit_data = json.load(f)
        self.assertEqual(audit_data["correlation_id"], sync_id)
        self.assertEqual(audit_data["health_metrics"]["health_score"], health_score)
        self.assertEqual(audit_data["security_metrics"]["vulnerabilities"], vulnerabilities)

    def test_synchronize_with_payload_token_mismatch(self):
        sync_id = str(uuid.uuid4())
        token = uuid.uuid4().hex
        env_token = uuid.uuid4().hex
        health_score = random.randint(1, 100)

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], sync_id)

    def test_synchronize_remote_success(self):
        health_data_mock = {"status": uuid.uuid4().hex, "score": random.randint(50, 100)}
        security_data_mock = {"issues": random.randint(0, 5), "level": uuid.uuid4().hex[:6]}

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

    def test_synchronize_remote_health_fail(self):
        error_text = uuid.uuid4().hex
        status_code = random.choice([400, 401, 403, 404, 500])

        mock_health_response = MagicMock()
        mock_health_response.status_code = status_code
        mock_health_response.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_health_response
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], status_code)
        self.assertIn(error_text, result["error"])

    def test_synchronize_remote_security_fail(self):
        health_data_mock = {"status": uuid.uuid4().hex}
        error_text = uuid.uuid4().hex
        status_code = random.choice([400, 401, 403, 404, 500])

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
        self.assertIn(error_text, result["error"])

    def test_synchronize_remote_exception(self):
        exception_msg = uuid.uuid4().hex

        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception(exception_msg)
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertIn(exception_msg, result["error"])

    def test_export_audit_stream_with_raw(self):
        random_bytes = uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=32)).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_bytes_len = len(random_bytes)

        mock_raw = io.BytesIO(random_bytes)
        mock_response = MagicMock()
        mock_response.raw = mock_raw
        mock_response.content = b"fallback_content"

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response
            result = self.syncer.export_audit_stream()

        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], expected_bytes_len)

    def test_export_audit_stream_fallback_content(self):
        random_bytes = ''.join(random.choices(string.hexdigits, k=64)).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_bytes_len = len(random_bytes)

        mock_response = MagicMock()
        mock_response.raw = None
        mock_response.content = random_bytes

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_response
            result = self.syncer.export_audit_stream()

        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], expected_bytes_len)