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
    
    def _gen_random_str(self, length=10):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def test_init_properties(self):
        repo_id = self._gen_random_str()
        health_url = f"http://{self._gen_random_str()}.local/health"
        security_url = f"http://{self._gen_random_str()}.local/security"
        target_directory = f"/tmp/{self._gen_random_str()}"

        syncer = RepoHealthSecuritySyncer(
            repo_id=repo_id,
            health_url=health_url,
            security_url=security_url,
            target_directory=target_directory
        )

        self.assertEqual(syncer.repo_id, repo_id)
        self.assertEqual(syncer.health_url, health_url)
        self.assertEqual(syncer.security_url, security_url)
        self.assertEqual(syncer.target_directory, target_directory)

    def test_synchronize_with_payload_no_token_env(self):
        sync_id = uuid.uuid4().hex
        health_score = round(random.uniform(10.0, 100.0), 2)
        security_score = round(random.uniform(10.0, 100.0), 2)
        vulnerabilities = random.randint(0, 50)
        token = self._gen_random_str()
        target_dir = f"/tmp/{uuid.uuid4().hex}"

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }

        syncer = RepoHealthSecuritySyncer(target_directory=target_dir)

        with patch.dict(os.environ, {}, clear=True):
            result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)
        self.assertEqual(result["health_data"]["health_score"], health_score)
        self.assertEqual(result["health_data"]["token"], token)
        self.assertEqual(result["security_data"]["security_score"], security_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)
        self.assertEqual(result["security_data"]["token"], token)

        expected_file = os.path.join(target_dir, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file))
        with open(expected_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["correlation_id"], sync_id)
            self.assertEqual(data["health_metrics"]["health_score"], health_score)
            self.assertEqual(data["security_metrics"]["security_score"], security_score)
            self.assertEqual(data["security_metrics"]["vulnerabilities"], vulnerabilities)

        if os.path.exists(expected_file):
            os.remove(expected_file)
        if os.path.exists(target_dir):
            os.rmdir(target_dir)

    def test_synchronize_with_payload_token_mismatch(self):
        sync_id = uuid.uuid4().hex
        env_token = self._gen_random_str()
        payload_token = self._gen_random_str()
        while env_token == payload_token:
            payload_token = self._gen_random_str()

        payload = {
            "sync_id": sync_id,
            "token": payload_token,
            "health_score": random.randint(1, 100)
        }

        syncer = RepoHealthSecuritySyncer()

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], sync_id)

    def test_synchronize_with_payload_token_match(self):
        sync_id = uuid.uuid4().hex
        token = self._gen_random_str()
        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": random.randint(1, 100)
        }

        syncer = RepoHealthSecuritySyncer()

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)

    def test_synchronize_remote_health_failure(self):
        health_url = f"http://{self._gen_random_str()}.local/health"
        security_url = f"http://{self._gen_random_str()}.local/sec"
        err_code = random.choice([400, 401, 403, 404, 500, 502])
        err_text = self._gen_random_str(15)

        syncer = RepoHealthSecuritySyncer(health_url=health_url, security_url=security_url)

        mock_resp = MagicMock()
        mock_resp.status_code = err_code
        mock_resp.text = err_text

        with patch("requests.get", return_value=mock_resp) as mock_get:
            result = syncer.synchronize()

        mock_get.assert_called_once_with(health_url)
        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], err_code)
        self.assertEqual(result["error"], err_text)

    def test_synchronize_remote_security_failure(self):
        health_url = f"http://{self._gen_random_str()}.local/health"
        security_url = f"http://{self._gen_random_str()}.local/sec"
        err_code = random.choice([400, 403, 404, 500, 503])
        err_text = self._gen_random_str(12)

        syncer = RepoHealthSecuritySyncer(health_url=health_url, security_url=security_url)

        health_resp = MagicMock()
        health_resp.status_code = 200

        security_resp = MagicMock()
        security_resp.status_code = err_code
        security_resp.text = err_text

        with patch("requests.get", side_effect=[health_resp, security_resp]) as mock_get:
            result = syncer.synchronize()

        self.assertEqual(mock_get.call_count, 2)
        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], err_code)
        self.assertEqual(result["error"], err_text)

    def test_synchronize_remote_success(self):
        health_url = f"http://{self._gen_random_str()}.local/health"
        security_url = f"http://{self._gen_random_str()}.local/sec"

        health_json = {"score": random.randint(1, 100), "id": self._gen_random_str()}
        security_json = {"vulns": random.randint(0, 10), "id": self._gen_random_str()}

        syncer = RepoHealthSecuritySyncer(health_url=health_url, security_url=security_url)

        health_resp = MagicMock()
        health_resp.status_code = 200
        health_resp.json.return_value = health_json

        security_resp = MagicMock()
        security_resp.status_code = 200
        security_resp.json.return_value = security_json

        with patch("requests.get", side_effect=[health_resp, security_resp]) as mock_get:
            result = syncer.synchronize()

        self.assertEqual(mock_get.call_count, 2)
        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"], health_json)
        self.assertEqual(result["security_data"], security_json)

    def test_synchronize_exception_handling(self):
        health_url = f"http://{self._gen_random_str()}.local/health"
        syncer = RepoHealthSecuritySyncer(health_url=health_url)
        exception_msg = self._gen_random_str(20)

        with patch("requests.get", side_effect=Exception(exception_msg)) as mock_get:
            result = syncer.synchronize()

        mock_get.assert_called_once_with(health_url)
        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertEqual(result["error"], exception_msg)

    def test_export_audit_stream_with_raw_read(self):
        health_url = f"http://{self._gen_random_str()}.local/health"
        syncer = RepoHealthSecuritySyncer(health_url=health_url)
        random_bytes = self._gen_random_str(50).encode('utf-8')

        mock_resp = MagicMock()
        mock_resp.raw = io.BytesIO(random_bytes)
        
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_len = len(random_bytes)

        with patch("requests.get", return_value=mock_resp) as mock_get:
            result = syncer.export_audit_stream()

        mock_get.assert_called_once_with(health_url)
        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], expected_len)

    def test_export_audit_stream_fallback_content(self):
        health_url = f"http://{self._gen_random_str()}.local/health"
        syncer = RepoHealthSecuritySyncer(health_url=health_url)
        random_bytes = self._gen_random_str(40).encode('utf-8')

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_len = len(random_bytes)

        with patch("requests.get", return_value=mock_resp) as mock_get:
            result = syncer.export_audit_stream()

        mock_get.assert_called_once_with(health_url)
        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], expected_len)