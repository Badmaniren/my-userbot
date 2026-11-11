import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import string
import json
import io
import hashlib
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncer(unittest.TestCase):
    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.health_url = f"http://{uuid.uuid4().hex[:8]}.local/health"
        self.security_url = f"http://{uuid.uuid4().hex[:8]}.local/security"
        self.target_directory = f"./{uuid.uuid4().hex[:10]}"
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            health_url=self.health_url,
            security_url=self.security_url,
            target_directory=self.target_directory
        )

    def tearDown(self):
        if os.path.exists(self.target_directory):
            for root, dirs, files in os.walk(self.target_directory, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.target_directory)

    def test_synchronize_with_payload_success(self):
        sync_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        health_score = random.randint(50, 100)
        security_score = random.randint(50, 100)
        vulnerabilities = [uuid.uuid4().hex for _ in range(random.randint(1, 3))]

        metric_payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            result = self.syncer.synchronize(metric_payload=metric_payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)
        self.assertEqual(result.get("health_data").get("health_score"), health_score)
        self.assertEqual(result.get("health_data").get("token"), token)
        self.assertEqual(result.get("security_data").get("security_score"), security_score)
        self.assertEqual(result.get("security_data").get("vulnerabilities"), vulnerabilities)

        expected_file = os.path.join(self.target_directory, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file))

        with open(expected_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)
        self.assertEqual(file_data.get("correlation_id"), sync_id)
        self.assertEqual(file_data.get("health_metrics").get("health_score"), health_score)
        self.assertEqual(file_data.get("security_metrics").get("security_score"), security_score)
        self.assertEqual(file_data.get("security_metrics").get("vulnerabilities"), vulnerabilities)

    def test_synchronize_with_payload_token_mismatch(self):
        sync_id = uuid.uuid4().hex
        valid_token = uuid.uuid4().hex
        invalid_token = uuid.uuid4().hex

        metric_payload = {
            "sync_id": sync_id,
            "token": invalid_token,
            "health_score": random.randint(1, 10),
            "security_score": random.randint(1, 10),
            "vulnerabilities": []
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": valid_token}):
            result = self.syncer.synchronize(metric_payload=metric_payload)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)

    def test_synchronize_network_success(self):
        health_data_mock = {"health_score": random.randint(70, 100), "status": uuid.uuid4().hex}
        security_data_mock = {"security_score": random.randint(70, 100), "vulnerabilities": []}

        mock_health_response = MagicMock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = health_data_mock

        mock_security_response = MagicMock()
        mock_security_response.status_code = 200
        mock_security_response.json.return_value = security_data_mock

        with patch('requests.get') as mock_get:
            mock_get.side_effect = [mock_health_response, mock_security_response]
            result = self.syncer.synchronize()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("health_data"), health_data_mock)
        self.assertEqual(result.get("security_data"), security_data_mock)

    def test_synchronize_health_request_failure(self):
        status_code = random.choice([400, 401, 403, 404, 500, 502, 503])
        error_text = uuid.uuid4().hex

        mock_health_response = MagicMock()
        mock_health_response.status_code = status_code
        mock_health_response.text = error_text

        with patch('requests.get') as mock_get:
            mock_get.return_value = mock_health_response
            result = self.syncer.synchronize()

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), status_code)
        self.assertEqual(result.get("error"), error_text)

    def test_synchronize_security_request_failure(self):
        health_data_mock = {"health_score": random.randint(70, 100)}
        status_code = random.choice([400, 401, 403, 404, 500, 502, 503])
        error_text = uuid.uuid4().hex

        mock_health_response = MagicMock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = health_data_mock

        mock_security_response = MagicMock()
        mock_security_response.status_code = status_code
        mock_security_response.text = error_text

        with patch('requests.get') as mock_get:
            mock_get.side_effect = [mock_health_response, mock_security_response]
            result = self.syncer.synchronize()

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), status_code)
        self.assertEqual(result.get("error"), error_text)

    def test_synchronize_exception_handling(self):
        exception_message = uuid.uuid4().hex

        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception(exception_message)
            result = self.syncer.synchronize()

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), 500)
        self.assertIn(exception_message, result.get("error"))

    def test_export_audit_stream_with_raw(self):
        random_bytes = os.urandom(random.randint(16, 64))
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        bytes_expected = len(random_bytes)

        mock_raw = io.BytesIO(random_bytes)
        mock_resp = MagicMock()
        mock_resp.raw = mock_raw

        with patch('requests.get') as mock_get:
            mock_get.return_value = mock_resp
            result = self.syncer.export_audit_stream()

        self.assertEqual(result.get("stream_hash"), expected_hash)
        self.assertEqual(result.get("bytes_read"), bytes_expected)

    def test_export_audit_stream_fallback_content(self):
        random_bytes = os.urandom(random.randint(16, 64))
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        bytes_expected = len(random_bytes)

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        with patch('requests.get') as mock_get:
            mock_get.return_value = mock_resp
            result = self.syncer.export_audit_stream()

        self.assertEqual(result.get("stream_hash"), expected_hash)
        self.assertEqual(result.get("bytes_read"), bytes_expected)