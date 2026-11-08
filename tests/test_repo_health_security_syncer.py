import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import string
import json
import io
import hashlib
import requests
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncer(unittest.TestCase):

    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.health_url = f"https://{uuid.uuid4().hex}.internal/health"
        self.security_url = f"https://{uuid.uuid4().hex}.internal/security"
        self.target_dir = f"temp_audit_{uuid.uuid4().hex}"
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            health_url=self.health_url,
            security_url=self.security_url,
            target_directory=self.target_dir
        )

    def tearDown(self):
        if os.path.exists(self.target_dir):
            for file in os.listdir(self.target_dir):
                file_path = os.path.join(self.target_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.target_dir)

    def test_synchronize_with_payload_success(self):
        sync_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        health_score = round(random.uniform(50.0, 100.0), 2)
        security_score = round(random.uniform(50.0, 100.0), 2)
        vulnerabilities = random.randint(0, 10)

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)
        self.assertEqual(result["health_data"]["health_score"], health_score)
        self.assertEqual(result["health_data"]["token"], token)
        self.assertEqual(result["security_data"]["security_score"], security_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)

        expected_file = os.path.join(self.target_dir, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file))
        
        with open(expected_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            
        self.assertEqual(saved_data["correlation_id"], sync_id)
        self.assertEqual(saved_data["health_metrics"]["health_score"], health_score)
        self.assertEqual(saved_data["security_metrics"]["security_score"], security_score)
        self.assertEqual(saved_data["security_metrics"]["vulnerabilities"], vulnerabilities)

    def test_synchronize_with_payload_invalid_token(self):
        sync_id = uuid.uuid4().hex
        env_token = uuid.uuid4().hex
        bad_token = uuid.uuid4().hex
        payload = {
            "sync_id": sync_id,
            "token": bad_token
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], sync_id)

    def test_synchronize_network_success(self):
        health_data_mock = {"health_score": round(random.uniform(0, 100), 2)}
        security_data_mock = {"security_score": round(random.uniform(0, 100), 2)}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_data_mock

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = 200
        mock_security_resp.json.return_value = security_data_mock

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
            result = self.syncer.synchronize(metric_payload=None)

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"], health_data_mock)
        self.assertEqual(result["security_data"], security_data_mock)

    def test_synchronize_network_health_failure(self):
        error_text = ''.join(random.choices(string.ascii_letters, k=15))
        status_code = random.choice([400, 401, 403, 404, 500, 502])

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = status_code
        mock_health_resp.text = error_text

        with patch("requests.get", return_value=mock_health_resp) as mock_get:
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], status_code)
        self.assertEqual(result["error"], error_text)

    def test_synchronize_network_security_failure(self):
        health_data_mock = {"health_score": round(random.uniform(0, 100), 2)}
        error_text = ''.join(random.choices(string.ascii_letters, k=15))
        status_code = random.choice([400, 401, 403, 404, 500, 502])

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_data_mock

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = status_code
        mock_security_resp.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], status_code)
        self.assertEqual(result["error"], error_text)

    def test_synchronize_network_exception(self):
        error_msg = ''.join(random.choices(string.ascii_letters, k=20))

        with patch("requests.get", side_effect=Exception(error_msg)) as mock_get:
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertEqual(result["error"], error_msg)

    def test_export_audit_stream_with_raw(self):
        random_bytes = ''.join(random.choices(string.printable, k=50)).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_resp = MagicMock()
        mock_resp.raw = io.BytesIO(random_bytes)
        
        with patch("requests.get", return_value=mock_resp) as mock_get:
            res = self.syncer.export_audit_stream()

        self.assertEqual(res["stream_hash"], expected_hash)
        self.assertEqual(res["bytes_read"], len(random_bytes))

    def test_export_audit_stream_with_content_fallback(self):
        random_bytes = ''.join(random.choices(string.printable, k=35)).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        with patch("requests.get", return_value=mock_resp) as mock_get:
            res = self.syncer.export_audit_stream()

        self.assertEqual(res["stream_hash"], expected_hash)
        self.assertEqual(res["bytes_read"], len(random_bytes))

if __name__ == "__main__":
    unittest.main()