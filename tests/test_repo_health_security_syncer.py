import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import hashlib
import random
import json
import io
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncer(unittest.TestCase):

    def test_synchronize_with_payload_success(self):
        rand_repo_id = uuid.uuid4().hex
        rand_health_url = f"https://{uuid.uuid4().hex}.com/health"
        rand_security_url = f"https://{uuid.uuid4().hex}.com/security"
        rand_dir = os.path.join("tmp", uuid.uuid4().hex)
        
        syncer = RepoHealthSecuritySyncer(
            repo_id=rand_repo_id,
            health_url=rand_health_url,
            security_url=rand_security_url,
            target_directory=rand_dir
        )

        rand_sync_id = uuid.uuid4().hex
        rand_token = uuid.uuid4().hex
        rand_score = random.randint(1, 100)
        rand_vuln_count = random.randint(0, 10)
        rand_vuln = [uuid.uuid4().hex for _ in range(rand_vuln_count)]

        metric_payload = {
            "sync_id": rand_sync_id,
            "token": rand_token,
            "health_score": rand_score,
            "vulnerabilities": rand_vuln,
            "security_score": rand_score
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": rand_token}):
            result = syncer.synchronize(metric_payload=metric_payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], rand_sync_id)
        self.assertEqual(result["health_data"]["health_score"], rand_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], rand_vuln)
        self.assertEqual(result["security_data"]["token"], rand_token)
        self.assertEqual(result["security_data"]["security_score"], rand_score)

        expected_file_name = f"audit_{rand_sync_id}.json"
        expected_file_path = os.path.join(rand_dir, expected_file_name)
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
        self.assertEqual(file_data["correlation_id"], rand_sync_id)
        self.assertEqual(file_data["health_metrics"]["health_score"], rand_score)
        self.assertEqual(file_data["security_metrics"]["vulnerabilities"], rand_vuln)

        if os.path.exists(expected_file_path):
            os.remove(expected_file_path)
        if os.path.exists(rand_dir):
            os.rmdir(rand_dir)

    def test_synchronize_with_payload_token_mismatch(self):
        syncer = RepoHealthSecuritySyncer()
        rand_sync_id = uuid.uuid4().hex
        rand_token = uuid.uuid4().hex
        rand_env_token = uuid.uuid4().hex

        metric_payload = {
            "sync_id": rand_sync_id,
            "token": rand_token,
            "health_score": random.randint(1, 100)
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": rand_env_token}):
            result = syncer.synchronize(metric_payload=metric_payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], rand_sync_id)

    def test_synchronize_network_requests_success(self):
        rand_health_url = f"https://{uuid.uuid4().hex}.com/health"
        rand_security_url = f"https://{uuid.uuid4().hex}.com/security"
        syncer = RepoHealthSecuritySyncer(
            health_url=rand_health_url,
            security_url=rand_security_url
        )

        rand_health_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_security_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = rand_health_data

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = 200
        mock_security_resp.json.return_value = rand_security_data

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
            result = syncer.synchronize()

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"], rand_health_data)
        self.assertEqual(result["security_data"], rand_security_data)

    def test_synchronize_health_check_failure(self):
        syncer = RepoHealthSecuritySyncer(
            health_url=f"https://{uuid.uuid4().hex}.com/health",
            security_url=f"https://{uuid.uuid4().hex}.com/security"
        )
        rand_status = random.choice([400, 401, 403, 404, 500, 502])
        rand_error_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = rand_status
        mock_health_resp.text = rand_error_text

        with patch("requests.get", return_value=mock_health_resp):
            result = syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], rand_status)
        self.assertIn(str(rand_status), result["error"])
        self.assertIn(rand_error_text, result["error"])

    def test_synchronize_security_check_failure(self):
        syncer = RepoHealthSecuritySyncer(
            health_url=f"https://{uuid.uuid4().hex}.com/health",
            security_url=f"https://{uuid.uuid4().hex}.com/security"
        )
        rand_status = random.choice([400, 401, 403, 404, 500, 502])
        rand_error_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = {}

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = rand_status
        mock_security_resp.text = rand_error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
            result = syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], rand_status)
        self.assertIn(str(rand_status), result["error"])
        self.assertIn(rand_error_text, result["error"])

    def test_synchronize_exception_handling(self):
        syncer = RepoHealthSecuritySyncer(
            health_url=f"https://{uuid.uuid4().hex}.com/health",
            security_url=f"https://{uuid.uuid4().hex}.com/security"
        )
        rand_exception_msg = uuid.uuid4().hex

        with patch("requests.get", side_effect=Exception(rand_exception_msg)):
            result = syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertIn(rand_exception_msg, result["error"])

    def test_export_audit_stream_with_raw(self):
        syncer = RepoHealthSecuritySyncer(
            health_url=f"https://{uuid.uuid4().hex}.com/stream"
        )
        random_bytes = uuid.uuid4().hex.encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.raw = io.BytesIO(random_bytes)

        with patch("requests.get", return_value=mock_resp):
            result = syncer.export_audit_stream()

        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], len(random_bytes))

    def test_export_audit_stream_fallback_content(self):
        syncer = RepoHealthSecuritySyncer(
            health_url=f"https://{uuid.uuid4().hex}.com/stream"
        )
        random_bytes = uuid.uuid4().hex.encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        with patch("requests.get", return_value=mock_resp):
            result = syncer.export_audit_stream()

        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], len(random_bytes))

if __name__ == "__main__":
    unittest.main()