import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import string
import json
import io
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncer(unittest.TestCase):

    def _generate_random_string(self, length=10):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for _ in range(length))

    def test_synchronize_with_payload_success(self):
        sync_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        health_score = random.randint(1, 100)
        vulnerabilities = random.randint(0, 10)
        security_score = random.randint(1, 100)

        metric_payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "vulnerabilities": vulnerabilities,
            "security_score": security_score
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            syncer = RepoHealthSecuritySyncer()
            result = syncer.synchronize(metric_payload=metric_payload)

            self.assertTrue(result["success"])
            self.assertEqual(result["synced_id"], sync_id)
            self.assertEqual(result["health_data"]["health_score"], health_score)
            self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)
            self.assertEqual(result["security_data"]["security_score"], security_score)
            self.assertEqual(result["security_data"]["token"], token)

    def test_synchronize_with_payload_token_mismatch(self):
        sync_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        env_token = uuid.uuid4().hex

        metric_payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": random.randint(1, 100),
            "vulnerabilities": random.randint(0, 10),
            "security_score": random.randint(1, 100)
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            syncer = RepoHealthSecuritySyncer()
            result = syncer.synchronize(metric_payload=metric_payload)

            self.assertFalse(result["success"])
            self.assertEqual(result["synced_id"], sync_id)

    def test_synchronize_with_payload_and_target_directory(self):
        sync_id = uuid.uuid4().hex
        target_dir = os.path.join(self._generate_random_string(), self._generate_random_string())
        health_score = random.randint(1, 100)
        vulnerabilities = random.randint(0, 10)

        metric_payload = {
            "sync_id": sync_id,
            "health_score": health_score,
            "vulnerabilities": vulnerabilities
        }

        mock_file = MagicMock()
        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_file) as mock_open, \
             patch("json.dump") as mock_json_dump:
            
            syncer = RepoHealthSecuritySyncer(target_directory=target_dir)
            result = syncer.synchronize(metric_payload=metric_payload)

            self.assertTrue(result["success"])
            mock_makedirs.assert_called_once_with(target_dir, exist_ok=True)
            mock_open.assert_called_once()
            mock_json_dump.assert_called_once()
            
            args, _ = mock_json_dump.call_args
            audit_content = args[0]
            self.assertEqual(audit_content["correlation_id"], sync_id)
            self.assertEqual(audit_content["health_metrics"]["health_score"], health_score)
            self.assertEqual(audit_content["security_metrics"]["vulnerabilities"], vulnerabilities)

    def test_synchronize_fetch_success(self):
        health_url = f"http://{self._generate_random_string()}.com/{self._generate_random_string()}"
        security_url = f"http://{self._generate_random_string()}.com/{self._generate_random_string()}"
        
        health_data_mock = {"health_score": random.randint(1, 100)}
        security_data_mock = {"vulnerabilities": random.randint(0, 5)}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_data_mock

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = 200
        mock_sec_resp.json.return_value = security_data_mock

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]

            syncer = RepoHealthSecuritySyncer(health_url=health_url, security_url=security_url)
            result = syncer.synchronize()

            self.assertTrue(result["success"])
            self.assertEqual(result["health_data"], health_data_mock)
            self.assertEqual(result["security_data"], security_data_mock)
            self.assertEqual(mock_get.call_count, 2)

    def test_synchronize_fetch_health_failure(self):
        health_url = f"http://{self._generate_random_string()}.com"
        error_code = random.choice([400, 403, 404, 500])
        error_text = self._generate_random_string(15)

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = error_code
        mock_health_resp.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_health_resp

            syncer = RepoHealthSecuritySyncer(health_url=health_url)
            result = syncer.synchronize()

            self.assertFalse(result["success"])
            self.assertEqual(result["status_code"], error_code)
            self.assertIn(error_text, result["error"])

    def test_synchronize_fetch_security_failure(self):
        health_url = f"http://{self._generate_random_string()}.com"
        security_url = f"http://{self._generate_random_string()}.com"
        
        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = {"ok": True}

        error_code = random.choice([401, 502, 503])
        error_text = self._generate_random_string(12)

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = error_code
        mock_sec_resp.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]

            syncer = RepoHealthSecuritySyncer(health_url=health_url, security_url=security_url)
            result = syncer.synchronize()

            self.assertFalse(result["success"])
            self.assertEqual(result["status_code"], error_code)
            self.assertIn(error_text, result["error"])

    def test_synchronize_exception_handling(self):
        health_url = f"http://{self._generate_random_string()}.com"
        exception_msg = self._generate_random_string(20)

        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception(exception_msg)

            syncer = RepoHealthSecuritySyncer(health_url=health_url)
            result = syncer.synchronize()

            self.assertFalse(result["success"])
            self.assertEqual(result["status_code"], 500)
            self.assertIn(exception_msg, result["error"])

    def test_export_audit_stream_with_raw(self):
        health_url = f"http://{self._generate_random_string()}.com"
        random_bytes = self._generate_random_string(50).encode('utf-8')

        mock_resp = MagicMock()
        mock_raw = io.BytesIO(random_bytes)
        mock_resp.raw = mock_raw

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_resp

            syncer = RepoHealthSecuritySyncer(health_url=health_url)
            result = syncer.export_audit_stream()

            self.assertEqual(result["bytes_read"], len(random_bytes))
            self.assertIn("stream_hash", result)

    def test_export_audit_stream_with_content(self):
        health_url = f"http://{self._generate_random_string()}.com"
        random_bytes = self._generate_random_string(30).encode('utf-8')

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_resp

            syncer = RepoHealthSecuritySyncer(health_url=health_url)
            result = syncer.export_audit_stream()

            self.assertEqual(result["bytes_read"], len(random_bytes))
            self.assertIn("stream_hash", result)

if __name__ == "__main__":
    unittest.main()