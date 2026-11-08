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
    def test_synchronize_with_payload_success(self):
        rand_repo_id = uuid.uuid4().hex
        rand_sync_id = uuid.uuid4().hex
        rand_score = random.randint(1, 100)
        rand_vuln_count = random.randint(0, 10)
        rand_sec_score = random.randint(1, 100)
        
        payload = {
            "sync_id": rand_sync_id,
            "health_score": rand_score,
            "vulnerabilities": rand_vuln_count,
            "security_score": rand_sec_score
        }

        syncer = RepoHealthSecuritySyncer(repo_id=rand_repo_id)
        result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], rand_sync_id)
        self.assertEqual(result["health_data"]["health_score"], rand_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], rand_vuln_count)
        self.assertEqual(result["security_data"]["security_score"], rand_sec_score)

    def test_synchronize_with_payload_token_mismatch(self):
        rand_repo_id = uuid.uuid4().hex
        rand_token = uuid.uuid4().hex
        rand_env_token = uuid.uuid4().hex
        
        payload = {
            "token": rand_token,
            "health_score": random.randint(1, 50),
            "vulnerabilities": random.randint(1, 5)
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": rand_env_token}):
            syncer = RepoHealthSecuritySyncer(repo_id=rand_repo_id)
            result = syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])

    def test_synchronize_with_payload_and_target_directory(self):
        rand_repo_id = uuid.uuid4().hex
        rand_dir = os.path.join(uuid.uuid4().hex, uuid.uuid4().hex)
        rand_sync_id = uuid.uuid4().hex
        rand_score = random.randint(50, 100)
        
        payload = {
            "sync_id": rand_sync_id,
            "health_score": rand_score,
            "vulnerabilities": random.randint(0, 3)
        }

        with patch("os.makedirs") as mock_makedirs, patch("builtins.open") as mock_open:
            syncer = RepoHealthSecuritySyncer(repo_id=rand_repo_id, target_directory=rand_dir)
            result = syncer.synchronize(metric_payload=payload)

            self.assertTrue(result["success"])
            mock_makedirs.assert_called_once_with(rand_dir, exist_ok=True)
            mock_open.assert_called_once()

    def test_synchronize_via_http_success(self):
        rand_repo_id = uuid.uuid4().hex
        rand_health_url = f"https://{uuid.uuid4().hex}.com/health"
        rand_sec_url = f"https://{uuid.uuid4().hex}.com/security"
        
        health_payload = {uuid.uuid4().hex: random.randint(1, 100)}
        sec_payload = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_payload

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = 200
        mock_sec_resp.json.return_value = sec_payload

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]
            
            syncer = RepoHealthSecuritySyncer(
                repo_id=rand_repo_id,
                health_url=rand_health_url,
                security_url=rand_sec_url
            )
            result = syncer.synchronize()

            self.assertTrue(result["success"])
            self.assertEqual(result["health_data"], health_payload)
            self.assertEqual(result["security_data"], sec_payload)

    def test_synchronize_via_http_health_fail(self):
        rand_repo_id = uuid.uuid4().hex
        rand_health_url = f"https://{uuid.uuid4().hex}.com/health"
        rand_sec_url = f"https://{uuid.uuid4().hex}.com/security"
        rand_status = random.choice([400, 401, 403, 404, 500])
        rand_err_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = rand_status
        mock_health_resp.text = rand_err_text

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_health_resp
            
            syncer = RepoHealthSecuritySyncer(
                repo_id=rand_repo_id,
                health_url=rand_health_url,
                security_url=rand_sec_url
            )
            result = syncer.synchronize()

            self.assertFalse(result["success"])
            self.assertEqual(result["status_code"], rand_status)
            self.assertIn(rand_err_text, result["error"])

    def test_synchronize_via_http_security_fail(self):
        rand_repo_id = uuid.uuid4().hex
        rand_health_url = f"https://{uuid.uuid4().hex}.com/health"
        rand_sec_url = f"https://{uuid.uuid4().hex}.com/security"
        rand_status = random.choice([500, 502, 503])
        rand_err_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = {}

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = rand_status
        mock_sec_resp.text = rand_err_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]
            
            syncer = RepoHealthSecuritySyncer(
                repo_id=rand_repo_id,
                health_url=rand_health_url,
                security_url=rand_sec_url
            )
            result = syncer.synchronize()

            self.assertFalse(result["success"])
            self.assertEqual(result["status_code"], rand_status)
            self.assertIn(rand_err_text, result["error"])

    def test_synchronize_exception_handling(self):
        rand_repo_id = uuid.uuid4().hex
        rand_health_url = f"https://{uuid.uuid4().hex}.com/health"
        rand_exception_msg = uuid.uuid4().hex

        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception(rand_exception_msg)
            
            syncer = RepoHealthSecuritySyncer(
                repo_id=rand_repo_id,
                health_url=rand_health_url
            )
            result = syncer.synchronize()

            self.assertFalse(result["success"])
            self.assertEqual(result["status_code"], 500)
            self.assertIn(rand_exception_msg, result["error"])

    def test_export_audit_stream_with_raw(self):
        rand_repo_id = uuid.uuid4().hex
        rand_health_url = f"https://{uuid.uuid4().hex}.com/stream"
        rand_data = uuid.uuid4().hex.encode('utf-8')
        
        mock_resp = MagicMock()
        mock_raw = io.BytesIO(rand_data)
        mock_resp.raw = mock_raw

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_resp
            
            syncer = RepoHealthSecuritySyncer(
                repo_id=rand_repo_id,
                health_url=rand_health_url
            )
            result = syncer.export_audit_stream()

            expected_hash = hashlib.sha256(rand_data).hexdigest()
            self.assertEqual(result["stream_hash"], expected_hash)
            self.assertEqual(result["bytes_read"], len(rand_data))

    def test_export_audit_stream_with_content_fallback(self):
        rand_repo_id = uuid.uuid4().hex
        rand_health_url = f"https://{uuid.uuid4().hex}.com/content"
        rand_data = uuid.uuid4().hex.encode('utf-8')
        
        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = rand_data

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_resp
            
            syncer = RepoHealthSecuritySyncer(
                repo_id=rand_repo_id,
                health_url=rand_health_url
            )
            result = syncer.export_audit_stream()

            expected_hash = hashlib.sha256(rand_data).hexdigest()
            self.assertEqual(result["stream_hash"], expected_hash)
            self.assertEqual(result["bytes_read"], len(rand_data))

if __name__ == "__main__":
    unittest.main()