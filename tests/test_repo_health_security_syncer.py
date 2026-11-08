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

    def _random_string(self, length=10):
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def test_synchronize_with_payload_success(self):
        repo_id = uuid.uuid4().hex
        health_url = f"https://{self._random_string()}.local/health"
        security_url = f"https://{self._random_string()}.local/security"
        
        syncer = RepoHealthSecuritySyncer(
            repo_id=repo_id,
            health_url=health_url,
            security_url=security_url
        )

        sync_id = uuid.uuid4().hex
        health_score = round(random.uniform(0.0, 100.0), 2)
        security_score = round(random.uniform(0.0, 100.0), 2)
        vulnerabilities = [self._random_string(5) for _ in range(random.randint(1, 3))]
        token = self._random_string(16)

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)
        self.assertEqual(result.get("health_data", {}).get("health_score"), health_score)
        self.assertEqual(result.get("security_data", {}).get("security_score"), security_score)
        self.assertEqual(result.get("security_data", {}).get("vulnerabilities"), vulnerabilities)
        self.assertEqual(result.get("security_data", {}).get("token"), token)

    def test_synchronize_with_payload_invalid_token(self):
        repo_id = uuid.uuid4().hex
        syncer = RepoHealthSecuritySyncer(repo_id=repo_id)

        sync_id = uuid.uuid4().hex
        payload = {
            "sync_id": sync_id,
            "token": self._random_string(8),
            "health_score": random.randint(10, 90),
        }

        correct_env_token = self._random_string(8)

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": correct_env_token}):
            result = syncer.synchronize(metric_payload=payload)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)

    def test_synchronize_with_payload_target_directory(self):
        repo_id = uuid.uuid4().hex
        target_dir = f"./tmp_audit_{uuid.uuid4().hex}"
        syncer = RepoHealthSecuritySyncer(
            repo_id=repo_id,
            target_directory=target_dir
        )

        sync_id = uuid.uuid4().hex
        health_score = random.randint(50, 100)
        vulnerabilities = [self._random_string() for _ in range(2)]

        payload = {
            "sync_id": sync_id,
            "health_score": health_score,
            "vulnerabilities": vulnerabilities
        }

        try:
            result = syncer.synchronize(metric_payload=payload)
            self.assertTrue(result.get("success"))

            expected_file_name = f"audit_{sync_id}.json"
            expected_file_path = os.path.join(target_dir, expected_file_name)

            self.assertTrue(os.path.exists(expected_file_path))

            with open(expected_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertEqual(data.get("correlation_id"), sync_id)
            self.assertEqual(data.get("health_metrics", {}).get("health_score"), health_score)
            self.assertEqual(data.get("security_metrics", {}).get("vulnerabilities"), vulnerabilities)

        finally:
            if os.path.exists(target_dir):
                for f_name in os.listdir(target_dir):
                    os.remove(os.path.join(target_dir, f_name))
                os.rmdir(target_dir)

    def test_synchronize_network_requests_success(self):
        health_url = f"https://{self._random_string()}.net/health"
        security_url = f"https://{self._random_string()}.net/security"
        
        syncer = RepoHealthSecuritySyncer(
            health_url=health_url,
            security_url=security_url
        )

        health_payload = {"status": self._random_string(), "score": random.randint(1, 100)}
        security_payload = {"issues": random.randint(0, 5), "level": self._random_string()}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_payload

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = 200
        mock_sec_resp.json.return_value = security_payload

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]
            result = syncer.synchronize(metric_payload=None)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("health_data"), health_payload)
        self.assertEqual(result.get("security_data"), security_payload)

    def test_synchronize_network_health_fail(self):
        health_url = f"https://{self._random_string()}.net/health"
        security_url = f"https://{self._random_string()}.net/security"
        
        syncer = RepoHealthSecuritySyncer(
            health_url=health_url,
            security_url=security_url
        )

        error_code = random.choice([400, 401, 403, 404, 500, 503])
        error_text = self._random_string(15)

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = error_code
        mock_health_resp.text = error_text

        with patch("requests.get", return_value=mock_health_resp) as mock_get:
            result = syncer.synchronize(metric_payload=None)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), error_code)
        self.assertIn(error_text, result.get("error"))

    def test_synchronize_network_security_fail(self):
        health_url = f"https://{self._random_string()}.net/health"
        security_url = f"https://{self._random_string()}.net/security"
        
        syncer = RepoHealthSecuritySyncer(
            health_url=health_url,
            security_url=security_url
        )

        health_payload = {"ok": True}
        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_payload

        error_code = random.choice([400, 500, 502])
        error_text = self._random_string(12)

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = error_code
        mock_sec_resp.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]
            result = syncer.synchronize(metric_payload=None)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), error_code)
        self.assertIn(error_text, result.get("error"))

    def test_synchronize_exception_handling(self):
        syncer = RepoHealthSecuritySyncer(
            health_url=f"https://{self._random_string()}.io/health"
        )

        exception_message = self._random_string(20)

        with patch("requests.get", side_effect=Exception(exception_message)):
            result = syncer.synchronize(metric_payload=None)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), 500)
        self.assertEqual(result.get("error"), exception_message)

    def test_export_audit_stream_with_raw(self):
        health_url = f"https://{self._random_string()}.stream/data"
        syncer = RepoHealthSecuritySyncer(health_url=health_url)

        random_bytes = self._random_string(50).encode("utf-8")
        stream_mock = io.BytesIO(random_bytes)

        mock_resp = MagicMock()
        mock_resp.raw = stream_mock

        with patch("requests.get", return_value=mock_resp):
            export_result = syncer.export_audit_stream()

        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        self.assertEqual(export_result.get("stream_hash"), expected_hash)
        self.assertEqual(export_result.get("bytes_read"), len(random_bytes))

    def test_export_audit_stream_with_content(self):
        health_url = f"https://{self._random_string()}.stream/data"
        syncer = RepoHealthSecuritySyncer(health_url=health_url)

        random_bytes = self._random_string(35).encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        with patch("requests.get", return_value=mock_resp):
            export_result = syncer.export_audit_stream()

        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        self.assertEqual(export_result.get("stream_hash"), expected_hash)
        self.assertEqual(export_result.get("bytes_read"), len(random_bytes))