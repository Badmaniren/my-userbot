import os
import uuid
import hashlib
import json
import random
import io
import unittest
from unittest.mock import patch, MagicMock

from skills.repo_health_security_syncer import RepoHealthSecuritySyncer


class TestRepoHealthSecuritySyncer(unittest.TestCase):

    def test_synchronize_with_metric_payload_success(self):
        rand_sync_id = uuid.uuid4().hex
        rand_token = uuid.uuid4().hex
        rand_health = random.randint(50, 100)
        rand_vulns = random.randint(0, 5)
        rand_sec_score = random.randint(10, 99)

        payload = {
            "sync_id": rand_sync_id,
            "token": rand_token,
            "health_score": rand_health,
            "vulnerabilities": rand_vulns,
            "security_score": rand_sec_score
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": rand_token}):
            syncer = RepoHealthSecuritySyncer(repo_id=uuid.uuid4().hex)
            result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], rand_sync_id)
        self.assertEqual(result["health_data"]["health_score"], rand_health)
        self.assertEqual(result["security_data"]["vulnerabilities"], rand_vulns)
        self.assertEqual(result["security_data"]["security_score"], rand_sec_score)
        self.assertEqual(result["security_data"]["token"], rand_token)

    def test_synchronize_with_metric_payload_invalid_token(self):
        rand_sync_id = uuid.uuid4().hex
        payload_token = uuid.uuid4().hex
        env_token = uuid.uuid4().hex

        payload = {
            "sync_id": rand_sync_id,
            "token": payload_token,
            "health_score": random.randint(1, 100),
            "vulnerabilities": random.randint(0, 10)
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            syncer = RepoHealthSecuritySyncer()
            result = syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], rand_sync_id)

    def test_synchronize_with_target_directory(self):
        rand_sync_id = uuid.uuid4().hex
        rand_dir = f"/tmp/{uuid.uuid4().hex}"
        rand_health = random.randint(1, 100)
        rand_vulns = random.randint(0, 10)

        payload = {
            "sync_id": rand_sync_id,
            "health_score": rand_health,
            "vulnerabilities": rand_vulns
        }

        expected_filename = f"audit_{rand_sync_id}.json"
        expected_filepath = os.path.join(rand_dir, expected_filename)

        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            
            syncer = RepoHealthSecuritySyncer(target_directory=rand_dir)
            result = syncer.synchronize(metric_payload=payload)

            mock_makedirs.assert_called_once_with(rand_dir, exist_ok=True)
            mock_file.assert_called_once_with(expected_filepath, "w", encoding="utf-8")

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], rand_sync_id)

    def test_synchronize_network_fetch_success(self):
        health_url = f"http://{uuid.uuid4().hex}.local/health"
        security_url = f"http://{uuid.uuid4().hex}.local/security"
        
        rand_health_data = {"health_score": random.randint(1, 100), "status": uuid.uuid4().hex}
        rand_sec_data = {"vulnerabilities": random.randint(0, 5), "level": uuid.uuid4().hex}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = rand_health_data

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = 200
        mock_security_resp.json.return_value = rand_sec_data

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]

            syncer = RepoHealthSecuritySyncer(health_url=health_url, security_url=security_url)
            result = syncer.synchronize()

            self.assertTrue(result["success"])
            self.assertEqual(result["health_data"], rand_health_data)
            self.assertEqual(result["security_data"], rand_sec_data)
            self.assertEqual(mock_get.call_count, 2)

    def test_synchronize_network_fetch_health_failure(self):
        health_url = f"http://{uuid.uuid4().hex}.local/health"
        security_url = f"http://{uuid.uuid4().hex}.local/security"
        err_status = random.choice([400, 401, 403, 404, 500, 503])
        err_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = err_status
        mock_health_resp.text = err_text

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_health_resp

            syncer = RepoHealthSecuritySyncer(health_url=health_url, security_url=security_url)
            result = syncer.synchronize()

            self.assertFalse(result["success"])
            self.assertEqual(result["status_code"], err_status)
            self.assertIn(str(err_status), result["error"])
            self.assertIn(err_text, result["error"])

    def test_synchronize_network_fetch_security_failure(self):
        health_url = f"http://{uuid.uuid4().hex}.local/health"
        security_url = f"http://{uuid.uuid4().hex}.local/security"
        err_status = random.choice([400, 401, 403, 404, 500, 503])
        err_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = {"ok": True}

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = err_status
        mock_security_resp.text = err_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]

            syncer = RepoHealthSecuritySyncer(health_url=health_url, security_url=security_url)
            result = syncer.synchronize()

            self.assertFalse(result["success"])
            self.assertEqual(result["status_code"], err_status)
            self.assertIn(str(err_status), result["error"])
            self.assertIn(err_text, result["error"])

    def test_synchronize_exception_handling(self):
        health_url = f"http://{uuid.uuid4().hex}.local/health"
        exception_message = uuid.uuid4().hex

        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception(exception_message)

            syncer = RepoHealthSecuritySyncer(health_url=health_url)
            result = syncer.synchronize()

            self.assertFalse(result["success"])
            self.assertEqual(result["status_code"], 500)
            self.assertEqual(result["error"], exception_message)

    def test_export_audit_stream_with_raw(self):
        health_url = f"http://{uuid.uuid4().hex}.local/stream"
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes

        mock_resp = MagicMock()
        mock_resp.raw = io.BytesIO(random_bytes)

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_resp

            syncer = RepoHealthSecuritySyncer(health_url=health_url)
            result = syncer.export_audit_stream()

            expected_hash = hashlib.sha256(random_bytes).hexdigest()
            self.assertEqual(result["stream_hash"], expected_hash)
            self.assertEqual(result["bytes_read"], len(random_bytes))

    def test_export_audit_stream_fallback_to_content(self):
        health_url = f"http://{uuid.uuid4().hex}.local/stream"
        random_bytes = uuid.uuid4().bytes

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_resp

            syncer = RepoHealthSecuritySyncer(health_url=health_url)
            result = syncer.export_audit_stream()

            expected_hash = hashlib.sha256(random_bytes).hexdigest()
            self.assertEqual(result["stream_hash"], expected_hash)
            self.assertEqual(result["bytes_read"], len(random_bytes))