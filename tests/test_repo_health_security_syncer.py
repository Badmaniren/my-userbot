import os
import uuid
import json
import random
import string
import hashlib
import io
import unittest
from unittest.mock import patch, MagicMock
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncer(unittest.TestCase):
    
    def setUp(self):
        self.random_repo_id = uuid.uuid4().hex
        self.random_health_url = f"http://{''.join(random.choices(string.ascii_lowercase, k=8))}.local/health"
        self.random_security_url = f"http://{''.join(random.choices(string.ascii_lowercase, k=8))}.local/security"
        self.random_target_dir = f"dir_{uuid.uuid4().hex[:8]}"
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.random_repo_id,
            health_url=self.random_health_url,
            security_url=self.random_security_url,
            target_directory=self.random_target_dir
        )

    def tearDown(self):
        if os.path.exists(self.random_target_dir):
            for root, dirs, files in os.walk(self.random_target_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.random_target_dir)

    def test_synchronize_with_payload_no_token_env(self):
        sync_id = uuid.uuid4().hex
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

        with patch.dict(os.environ, {}, clear=True):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)
        self.assertEqual(result["health_data"]["health_score"], health_score)
        self.assertEqual(result["health_data"]["token"], token)
        self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)
        self.assertEqual(result["security_data"]["security_score"], security_score)
        self.assertEqual(result["security_data"]["token"], token)

        expected_file = os.path.join(self.random_target_dir, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file))
        with open(expected_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)
        self.assertEqual(file_data["correlation_id"], sync_id)
        self.assertEqual(file_data["health_metrics"]["health_score"], health_score)
        self.assertEqual(file_data["security_metrics"]["security_score"], security_score)
        self.assertEqual(file_data["security_metrics"]["vulnerabilities"], vulnerabilities)

    def test_synchronize_with_payload_valid_env_token(self):
        sync_id = uuid.uuid4().hex
        env_token = uuid.uuid4().hex
        health_score = random.randint(10, 90)
        vulnerabilities = random.randint(1, 5)
        security_score = random.randint(10, 90)

        payload = {
            "sync_id": sync_id,
            "token": env_token,
            "health_score": health_score,
            "vulnerabilities": vulnerabilities,
            "security_score": security_score
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)

    def test_synchronize_with_payload_invalid_env_token(self):
        sync_id = uuid.uuid4().hex
        env_token = uuid.uuid4().hex
        wrong_token = uuid.uuid4().hex

        payload = {
            "sync_id": sync_id,
            "token": wrong_token,
            "health_score": random.randint(1, 50),
            "vulnerabilities": random.randint(1, 50),
            "security_score": random.randint(1, 50)
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], sync_id)

    def test_synchronize_remote_success(self):
        health_json = {"score": random.randint(50, 100), "status": uuid.uuid4().hex}
        security_json = {"issues": random.randint(0, 5), "level": uuid.uuid4().hex}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_json

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = 200
        mock_security_resp.json.return_value = security_json

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
            result = self.syncer.synchronize(metric_payload=None)

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"], health_json)
        self.assertEqual(result["security_data"], security_json)

    def test_synchronize_remote_health_fail(self):
        error_code = random.choice([400, 401, 403, 404, 500])
        error_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = error_code
        mock_health_resp.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_health_resp
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], error_code)
        self.assertEqual(result["error"], error_text)

    def test_synchronize_remote_security_fail(self):
        health_json = {"score": random.randint(50, 100)}
        error_code = random.choice([400, 401, 403, 404, 500])
        error_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_json

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = error_code
        mock_security_resp.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], error_code)
        self.assertEqual(result["error"], error_text)

    def test_synchronize_remote_exception(self):
        exception_message = uuid.uuid4().hex

        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception(exception_message)
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertIn(exception_message, result["error"])

    def test_export_audit_stream_with_raw(self):
        random_bytes = uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=32)).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_length = len(random_bytes)

        mock_resp = MagicMock()
        mock_resp.raw = io.BytesIO(random_bytes)

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_resp
            result = self.syncer.export_audit_stream()

        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], expected_length)

    def test_export_audit_stream_fallback_content(self):
        random_bytes = uuid.uuid4().hex.encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_length = len(random_bytes)

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_resp
            result = self.syncer.export_audit_stream()

        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], expected_length)

if __name__ == "__main__":
    unittest.main()