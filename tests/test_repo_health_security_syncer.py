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
        self.random_target_dir = f"/tmp/audit_{uuid.uuid4().hex}"
        
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.random_repo_id,
            health_url=self.random_health_url,
            security_url=self.random_security_url,
            target_directory=self.random_target_dir
        )

    def tearDown(self):
        if os.path.exists(self.random_target_dir):
            for filename in os.listdir(self.random_target_dir):
                file_path = os.path.join(self.random_target_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception:
                    pass
            try:
                os.rmdir(self.random_target_dir)
            except Exception:
                pass

    def test_synchronize_with_payload_success(self):
        random_sync_id = uuid.uuid4().hex
        random_token = uuid.uuid4().hex
        random_health_score = round(random.uniform(1.0, 100.0), 2)
        random_vulnerabilities = random.randint(0, 10)
        random_security_score = round(random.uniform(1.0, 100.0), 2)

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

        expected_file_path = os.path.join(self.random_target_dir, f"audit_{random_sync_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            self.assertEqual(file_data["correlation_id"], random_sync_id)
            self.assertEqual(file_data["health_metrics"]["health_score"], random_health_score)
            self.assertEqual(file_data["security_metrics"]["vulnerabilities"], random_vulnerabilities)

    def test_synchronize_with_payload_token_mismatch(self):
        random_sync_id = uuid.uuid4().hex
        payload_token = uuid.uuid4().hex
        env_token = uuid.uuid4().hex

        payload = {
            "sync_id": random_sync_id,
            "token": payload_token,
            "health_score": random.randint(1, 10),
            "vulnerabilities": 0,
            "security_score": 100.0
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], random_sync_id)

    def test_synchronize_remote_success(self):
        random_health_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        random_security_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = random_health_data

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = 200
        mock_security_resp.json.return_value = random_security_data

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
            
            syncer_no_dir = RepoHealthSecuritySyncer(
                repo_id=self.random_repo_id,
                health_url=self.random_health_url,
                security_url=self.random_security_url
            )
            result = syncer_no_dir.synchronize(metric_payload=None)

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"], random_health_data)
        self.assertEqual(result["security_data"], random_security_data)
        self.assertEqual(mock_get.call_count, 2)

    def test_synchronize_remote_health_failure(self):
        random_status = random.choice([400, 401, 403, 404, 500, 502])
        random_error_text = ''.join(random.choices(string.ascii_letters, k=15))

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = random_status
        mock_health_resp.text = random_error_text

        with patch("requests.get", return_value=mock_health_resp) as mock_get:
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], random_status)
        self.assertIn(random_error_text, result["error"])

    def test_synchronize_remote_security_failure(self):
        random_health_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        random_status = random.choice([400, 401, 403, 404, 500, 502])
        random_error_text = ''.join(random.choices(string.ascii_letters, k=15))

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = random_health_data

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = random_status
        mock_security_resp.text = random_error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], random_status)
        self.assertIn(random_error_text, result["error"])

    def test_synchronize_remote_exception(self):
        random_error_message = ''.join(random.choices(string.ascii_letters, k=20))

        with patch("requests.get", side_effect=Exception(random_error_message)) as mock_get:
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertIn(random_error_message, result["error"])

    def test_export_audit_stream_with_raw(self):
        random_bytes = uuid.uuid4().bytes + ''.join(random.choices(string.printable, k=50)).encode('utf-8')
        import hashlib
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_raw_stream = io.BytesIO(random_bytes)
        mock_resp = MagicMock()
        mock_resp.raw = mock_raw_stream

        with patch("requests.get", return_value=mock_resp) as mock_get:
            result = self.syncer.export_audit_stream()

        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], len(random_bytes))

    def test_export_audit_stream_without_raw(self):
        random_bytes = ''.join(random.choices(string.ascii_letters, k=40)).encode('utf-8')
        import hashlib
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        with patch("requests.get", return_value=mock_resp) as mock_get:
            result = self.syncer.export_audit_stream()

        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], len(random_bytes))

if __name__ == "__main__":
    unittest.main()