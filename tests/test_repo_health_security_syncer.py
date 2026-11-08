import unittest
from unittest.mock import patch
import os
import uuid
import random
import io
import json
import hashlib
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncer(unittest.TestCase):
    def test_synchronize_with_payload_success_and_audit(self):
        rand_sync_id = uuid.uuid4().hex
        rand_token = uuid.uuid4().hex
        rand_health = random.randint(1, 100)
        rand_vuln = random.randint(0, 10)
        rand_sec_score = random.randint(1, 100)
        rand_dir = f"temp_audit_dir_{uuid.uuid4().hex}"

        payload = {
            "sync_id": rand_sync_id,
            "token": rand_token,
            "health_score": rand_health,
            "vulnerabilities": rand_vuln,
            "security_score": rand_sec_score
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": rand_token}):
            syncer = RepoHealthSecuritySyncer(target_directory=rand_dir)
            result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], rand_sync_id)
        self.assertEqual(result["health_data"]["health_score"], rand_health)
        self.assertEqual(result["security_data"]["vulnerabilities"], rand_vuln)
        self.assertEqual(result["security_data"]["security_score"], rand_sec_score)
        self.assertEqual(result["security_data"]["token"], rand_token)

        expected_file_path = os.path.join(rand_dir, f"audit_{rand_sync_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
        self.assertEqual(file_data["correlation_id"], rand_sync_id)
        self.assertEqual(file_data["health_metrics"]["health_score"], rand_health)
        self.assertEqual(file_data["security_metrics"]["vulnerabilities"], rand_vuln)

        if os.path.exists(expected_file_path):
            os.remove(expected_file_path)
        if os.path.exists(rand_dir):
            os.rmdir(rand_dir)

    def test_synchronize_with_payload_token_mismatch(self):
        rand_token = uuid.uuid4().hex
        rand_env_token = uuid.uuid4().hex
        payload = {
            "sync_id": uuid.uuid4().hex,
            "token": rand_token,
            "health_score": random.randint(1, 100),
            "vulnerabilities": random.randint(0, 5),
            "security_score": random.randint(1, 100)
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": rand_env_token}):
            syncer = RepoHealthSecuritySyncer()
            result = syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])

    def test_synchronize_network_success(self):
        rand_health_url = f"http://{uuid.uuid4().hex}.local/health"
        rand_sec_url = f"http://{uuid.uuid4().hex}.local/security"
        rand_health_val = random.randint(10, 99)
        rand_sec_val = uuid.uuid4().hex

        mock_health_resp = unittest.mock.Mock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = {"health_score": rand_health_val}

        mock_sec_resp = unittest.mock.Mock()
        mock_sec_resp.status_code = 200
        mock_sec_resp.json.return_value = {"security_status": rand_sec_val}

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]
            syncer = RepoHealthSecuritySyncer(health_url=rand_health_url, security_url=rand_sec_url)
            result = syncer.synchronize()

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"]["health_score"], rand_health_val)
        self.assertEqual(result["security_data"]["security_status"], rand_sec_val)

    def test_synchronize_health_fail(self):
        rand_health_url = f"http://{uuid.uuid4().hex}.local/health"
        rand_status = random.choice([400, 403, 500, 502])
        rand_error_text = uuid.uuid4().hex

        mock_health_resp = unittest.mock.Mock()
        mock_health_resp.status_code = rand_status
        mock_health_resp.text = rand_error_text

        with patch("requests.get", return_value=mock_health_resp):
            syncer = RepoHealthSecuritySyncer(health_url=rand_health_url)
            result = syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], rand_status)
        self.assertIn(rand_error_text, result["error"])

    def test_synchronize_security_fail(self):
        rand_health_url = f"http://{uuid.uuid4().hex}.local/health"
        rand_sec_url = f"http://{uuid.uuid4().hex}.local/security"
        rand_status = random.choice([401, 404, 503])
        rand_error_text = uuid.uuid4().hex

        mock_health_resp = unittest.mock.Mock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = {"status": "ok"}

        mock_sec_resp = unittest.mock.Mock()
        mock_sec_resp.status_code = rand_status
        mock_sec_resp.text = rand_error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]
            syncer = RepoHealthSecuritySyncer(health_url=rand_health_url, security_url=rand_sec_url)
            result = syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], rand_status)
        self.assertIn(rand_error_text, result["error"])

    def test_synchronize_exception_handling(self):
        rand_url = f"http://{uuid.uuid4().hex}.local/health"
        rand_exc_msg = uuid.uuid4().hex

        with patch("requests.get", side_effect=Exception(rand_exc_msg)):
            syncer = RepoHealthSecuritySyncer(health_url=rand_url)
            result = syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertIn(rand_exc_msg, result["error"])

    def test_export_audit_stream_with_raw(self):
        rand_url = f"http://{uuid.uuid4().hex}.local/stream"
        rand_content = uuid.uuid4().bytes

        mock_resp = unittest.mock.Mock()
        mock_resp.raw = io.BytesIO(rand_content)

        with patch("requests.get", return_value=mock_resp):
            syncer = RepoHealthSecuritySyncer(health_url=rand_url)
            export_result = syncer.export_audit_stream()

        expected_hash = hashlib.sha256(rand_content).hexdigest()
        self.assertEqual(export_result["stream_hash"], expected_hash)
        self.assertEqual(export_result["bytes_read"], len(rand_content))

    def test_export_audit_stream_fallback_content(self):
        rand_url = f"http://{uuid.uuid4().hex}.local/stream"
        rand_content = uuid.uuid4().bytes

        mock_resp = unittest.mock.Mock()
        mock_resp.raw = None
        mock_resp.content = rand_content

        with patch("requests.get", return_value=mock_resp):
            syncer = RepoHealthSecuritySyncer(health_url=rand_url)
            export_result = syncer.export_audit_stream()

        expected_hash = hashlib.sha256(rand_content).hexdigest()
        self.assertEqual(export_result["stream_hash"], expected_hash)
        self.assertEqual(export_result["bytes_read"], len(rand_content))

if __name__ == "__main__":
    unittest.main()