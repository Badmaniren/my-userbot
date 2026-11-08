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
        self.repo_id = uuid.uuid4().hex
        self.health_url = f"https://{uuid.uuid4().hex}.local/health"
        self.security_url = f"https://{uuid.uuid4().hex}.local/security"
        self.target_dir = os.path.join(os.getcwd(), uuid.uuid4().hex)
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            health_url=self.health_url,
            security_url=self.security_url,
            target_directory=self.target_dir
        )

    def tearDown(self):
        if os.path.exists(self.target_dir):
            for root, dirs, files in os.walk(self.target_dir, topdown=False):
                for name in files:
                    try:
                        os.remove(os.path.join(root, name))
                    except OSError:
                        pass
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except OSError:
                        pass
            try:
                os.rmdir(self.target_dir)
            except OSError:
                pass

    def test_synchronize_with_payload_success(self):
        sync_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        health_score = random.randint(50, 100)
        security_score = random.randint(50, 100)
        vulnerabilities_count = random.randint(0, 5)
        vulnerabilities = [uuid.uuid4().hex for _ in range(vulnerabilities_count)]

        metric_payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            result = self.syncer.synchronize(metric_payload=metric_payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)
        self.assertEqual(result["health_data"]["health_score"], health_score)
        self.assertEqual(result["security_data"]["security_score"], security_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)

        expected_file_path = os.path.join(self.target_dir, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))
        with open(expected_file_path, "r", encoding="utf-8") as f:
            audit_data = json.load(f)
        self.assertEqual(audit_data["correlation_id"], sync_id)
        self.assertEqual(audit_data["health_metrics"]["health_score"], health_score)
        self.assertEqual(audit_data["security_metrics"]["vulnerabilities"], vulnerabilities)

    def test_synchronize_with_payload_token_mismatch(self):
        sync_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        env_token = uuid.uuid4().hex

        metric_payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": random.randint(0, 50),
            "security_score": random.randint(0, 50),
            "vulnerabilities": []
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = self.syncer.synchronize(metric_payload=metric_payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], sync_id)

    def test_synchronize_network_success(self):
        health_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        security_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_data

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = 200
        mock_security_resp.json.return_value = security_data

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
            result = self.syncer.synchronize(metric_payload=None)

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"], health_data)
        self.assertEqual(result["security_data"], security_data)
        self.assertEqual(mock_get.call_count, 2)

    def test_synchronize_health_fail(self):
        status_code = random.choice([400, 401, 403, 404, 500, 502])
        error_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = status_code
        mock_health_resp.text = error_text

        with patch("requests.get", return_value=mock_health_resp) as mock_get:
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], status_code)
        self.assertIn(str(status_code), result["error"])
        self.assertIn(error_text, result["error"])

    def test_synchronize_security_fail(self):
        health_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        status_code = random.choice([400, 403, 404, 500, 503])
        error_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_data

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = status_code
        mock_security_resp.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
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

    def test_export_audit_stream(self):
        random_bytes = uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=64)).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_bytes_read = len(random_bytes)

        mock_resp = MagicMock()
        mock_resp.raw = io.BytesIO(random_bytes)

        with patch("requests.get", return_value=mock_resp) as mock_get:
            result = self.syncer.export_audit_stream()

        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], expected_bytes_read)
        mock_get.assert_called_once_with(self.health_url, timeout=10)

    def test_export_audit_stream_fallback_content(self):
        random_bytes = uuid.uuid4().bytes + ''.join(random.choices(string.digits, k=32)).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_bytes_read = len(random_bytes)

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        with patch("requests.get", return_value=mock_resp) as mock_get:
            result = self.syncer.export_audit_stream()

        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], expected_bytes_read)