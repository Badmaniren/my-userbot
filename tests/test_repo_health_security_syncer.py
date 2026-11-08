import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import hashlib
import io
import os
import json
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncer(unittest.TestCase):

    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.health_url = f"https://{uuid.uuid4().hex}.internal/health"
        self.security_url = f"https://{uuid.uuid4().hex}.internal/security"
        self.target_directory = f"/tmp/{uuid.uuid4().hex}"
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            health_url=self.health_url,
            security_url=self.security_url,
            target_directory=self.target_directory
        )

    def test_synchronize_with_payload_success_token_match(self):
        sync_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        health_score = random.randint(1, 100)
        vulnerabilities = [uuid.uuid4().hex for _ in range(random.randint(1, 3))]
        security_score = random.randint(1, 100)

        metric_payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "vulnerabilities": vulnerabilities,
            "security_score": security_score
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            result = self.syncer.synchronize(metric_payload=metric_payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)
        self.assertEqual(result.get("health_data", {}).get("health_score"), health_score)
        self.assertEqual(result.get("security_data", {}).get("security_score"), security_score)
        self.assertEqual(result.get("security_data", {}).get("vulnerabilities"), vulnerabilities)

    def test_synchronize_with_payload_failure_token_mismatch(self):
        sync_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        env_token = uuid.uuid4().hex
        health_score = random.randint(1, 100)

        metric_payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = self.syncer.synchronize(metric_payload=metric_payload)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)

    def test_synchronize_with_payload_file_creation(self):
        sync_id = uuid.uuid4().hex
        health_score = random.randint(1, 100)
        vulnerabilities = [uuid.uuid4().hex]

        metric_payload = {
            "sync_id": sync_id,
            "health_score": health_score,
            "vulnerabilities": vulnerabilities
        }

        expected_file_name = f"audit_{sync_id}.json"
        expected_file_path = os.path.join(self.target_directory, expected_file_name)

        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            
            result = self.syncer.synchronize(metric_payload=metric_payload)

            mock_makedirs.assert_called_once_with(self.target_directory, exist_ok=True)
            mock_file.assert_called_once_with(expected_file_path, "w", encoding="utf-8")
            self.assertTrue(result.get("success"))

    def test_synchronize_network_success(self):
        health_payload = {"health_score": random.randint(1, 100), "id": uuid.uuid4().hex}
        security_payload = {"security_score": random.randint(1, 100), "issues": []}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_payload

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = 200
        mock_security_resp.json.return_value = security_payload

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
            result = self.syncer.synchronize()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("health_data"), health_payload)
        self.assertEqual(result.get("security_data"), security_payload)

    def test_synchronize_health_fail(self):
        status_code = random.choice([400, 401, 403, 404, 500, 502])
        error_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = status_code
        mock_health_resp.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_health_resp
            result = self.syncer.synchronize()

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), status_code)
        self.assertIn(error_text, result.get("error"))

    def test_synchronize_security_fail(self):
        health_payload = {"health_score": random.randint(1, 100)}
        status_code = random.choice([400, 401, 403, 404, 500, 502])
        error_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_payload

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = status_code
        mock_security_resp.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
            result = self.syncer.synchronize()

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), status_code)
        self.assertIn(error_text, result.get("error"))

    def test_synchronize_exception_handling(self):
        exception_message = uuid.uuid4().hex

        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception(exception_message)
            result = self.syncer.synchronize()

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), 500)
        self.assertEqual(result.get("error"), exception_message)

    def test_export_audit_stream_with_raw(self):
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_resp = MagicMock()
        mock_raw = io.BytesIO(random_bytes)
        mock_resp.raw = mock_raw

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_resp
            res = self.syncer.export_audit_stream()

        self.assertEqual(res.get("stream_hash"), expected_hash)
        self.assertEqual(res.get("bytes_read"), len(random_bytes))

    def test_export_audit_stream_with_content(self):
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_resp
            res = self.syncer.export_audit_stream()

        self.assertEqual(res.get("stream_hash"), expected_hash)
        self.assertEqual(res.get("bytes_read"), len(random_bytes))

if __name__ == "__main__":
    unittest.main()