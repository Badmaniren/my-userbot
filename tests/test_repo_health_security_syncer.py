import os
import io
import json
import uuid
import random
import string
import hashlib
import unittest
from unittest.mock import patch, MagicMock
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncer(unittest.TestCase):

    def setUp(self):
        self.rand_repo_id = uuid.uuid4().hex
        self.rand_health_url = f"http://{uuid.uuid4().hex}.local/health"
        self.rand_security_url = f"http://{uuid.uuid4().hex}.local/security"
        self.rand_target_dir = os.path.join("temp_audit_" + uuid.uuid4().hex)
        
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.rand_repo_id,
            health_url=self.rand_health_url,
            security_url=self.rand_security_url,
            target_directory=self.rand_target_dir
        )

    def tearDown(self):
        if os.path.exists(self.rand_target_dir):
            for filename in os.listdir(self.rand_target_dir):
                file_path = os.path.join(self.rand_target_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.rand_target_dir)

    def test_synchronize_with_payload_success(self):
        rand_sync_id = uuid.uuid4().hex
        rand_token = uuid.uuid4().hex
        rand_health_score = random.randint(1, 100)
        rand_security_score = random.randint(1, 100)
        rand_vuln_name = uuid.uuid4().hex
        
        metric_payload = {
            "sync_id": rand_sync_id,
            "token": rand_token,
            "health_score": rand_health_score,
            "security_score": rand_security_score,
            "vulnerabilities": [rand_vuln_name]
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": rand_token}):
            result = self.syncer.synchronize(metric_payload=metric_payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], rand_sync_id)
        self.assertEqual(result["health_data"]["health_score"], rand_health_score)
        self.assertEqual(result["health_data"]["token"], rand_token)
        self.assertEqual(result["security_data"]["security_score"], rand_security_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], [rand_vuln_name])

        expected_file_path = os.path.join(self.rand_target_dir, f"audit_{rand_sync_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))
        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
        self.assertEqual(file_data["correlation_id"], rand_sync_id)
        self.assertEqual(file_data["health_metrics"]["health_score"], rand_health_score)
        self.assertEqual(file_data["security_metrics"]["security_score"], rand_security_score)

    def test_synchronize_with_payload_token_mismatch(self):
        rand_sync_id = uuid.uuid4().hex
        env_token = uuid.uuid4().hex
        wrong_token = uuid.uuid4().hex
        
        metric_payload = {
            "sync_id": rand_sync_id,
            "token": wrong_token,
            "health_score": random.randint(1, 100)
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = self.syncer.synchronize(metric_payload=metric_payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], rand_sync_id)

    def test_synchronize_without_payload_success(self):
        rand_health_val = uuid.uuid4().hex
        rand_security_val = uuid.uuid4().hex
        
        mock_health_response = MagicMock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = {"status": rand_health_val}

        mock_security_response = MagicMock()
        mock_security_response.status_code = 200
        mock_security_response.json.return_value = {"status": rand_security_val}

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_response, mock_security_response]
            result = self.syncer.synchronize()

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"]["status"], rand_health_val)
        self.assertEqual(result["security_data"]["status"], rand_security_val)
        self.assertEqual(mock_get.call_count, 2)

    def test_synchronize_without_payload_health_error(self):
        rand_status_code = random.choice([400, 401, 403, 404, 500])
        rand_error_text = uuid.uuid4().hex

        mock_health_response = MagicMock()
        mock_health_response.status_code = rand_status_code
        mock_health_response.text = rand_error_text

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_health_response
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], rand_status_code)
        self.assertEqual(result["error"], rand_error_text)

    def test_synchronize_without_payload_security_error(self):
        rand_status_code = random.choice([502, 503, 504])
        rand_error_text = uuid.uuid4().hex

        mock_health_response = MagicMock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = {}

        mock_security_response = MagicMock()
        mock_security_response.status_code = rand_status_code
        mock_security_response.text = rand_error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_response, mock_security_response]
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], rand_status_code)
        self.assertEqual(result["error"], rand_error_text)

    def test_synchronize_exception_handling(self):
        rand_exception_msg = uuid.uuid4().hex

        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception(rand_exception_msg)
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertIn(rand_exception_msg, result["error"])

    def test_export_audit_stream_with_raw(self):
        rand_payload_bytes = uuid.uuid4().hex.encode('utf-8')
        expected_hash = hashlib.sha256(rand_payload_bytes).hexdigest()
        expected_len = len(rand_payload_bytes)

        mock_response = MagicMock()
        mock_response.raw = io.BytesIO(rand_payload_bytes)

        with patch("requests.get", return_value=mock_response) as mock_get:
            res = self.syncer.export_audit_stream()

        mock_get.assert_called_once_with(self.rand_health_url)
        self.assertEqual(res["stream_hash"], expected_hash)
        self.assertEqual(res["bytes_read"], expected_len)

    def test_export_audit_stream_without_raw(self):
        rand_payload_bytes = uuid.uuid4().hex.encode('utf-8')
        expected_hash = hashlib.sha256(rand_payload_bytes).hexdigest()
        expected_len = len(rand_payload_bytes)

        mock_response = MagicMock(spec=[])
        mock_response.raw = None
        mock_response.content = rand_payload_bytes

        with patch("requests.get", return_value=mock_response) as mock_get:
            res = self.syncer.export_audit_stream()

        mock_get.assert_called_once_with(self.rand_health_url)
        self.assertEqual(res["stream_hash"], expected_hash)
        self.assertEqual(res["bytes_read"], expected_len)

if __name__ == '__main__':
    unittest.main()