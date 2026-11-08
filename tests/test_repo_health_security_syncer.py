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

    def setUp(self):
        self.repo_id = str(uuid.uuid4())
        self.health_url = f"https://api.random-{uuid.uuid4().hex[:6]}.io/health"
        self.security_url = f"https://api.random-{uuid.uuid4().hex[:6]}.io/security"
        self.target_directory = f"./audit_dir_{uuid.uuid4().hex[:8]}"
        
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            health_url=self.health_url,
            security_url=self.security_url,
            target_directory=self.target_directory
        )

    def tearDown(self):
        if os.path.exists(self.target_directory):
            for file_name in os.listdir(self.target_directory):
                file_path = os.path.join(self.target_directory, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.target_directory)

    def test_synchronize_with_payload_success_no_token(self):
        sync_id = str(uuid.uuid4())
        health_score = random.randint(1, 100)
        security_score = random.randint(1, 100)
        vulnerabilities_count = random.randint(0, 5)
        vulnerabilities = [uuid.uuid4().hex for _ in range(vulnerabilities_count)]

        payload = {
            "sync_id": sync_id,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }

        result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)
        self.assertEqual(result["health_data"]["health_score"], health_score)
        self.assertEqual(result["security_data"]["security_score"], security_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)

        expected_file_path = os.path.join(self.target_directory, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            self.assertEqual(file_data["correlation_id"], sync_id)
            self.assertEqual(file_data["health_metrics"]["health_score"], health_score)
            self.assertEqual(file_data["security_metrics"]["vulnerabilities"], vulnerabilities)

    def test_synchronize_with_payload_token_validation(self):
        sync_id = str(uuid.uuid4())
        valid_token = uuid.uuid4().hex
        invalid_token = uuid.uuid4().hex

        payload_valid = {
            "sync_id": sync_id,
            "token": valid_token,
            "health_score": random.randint(50, 100)
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": valid_token}):
            result_valid = self.syncer.synchronize(metric_payload=payload_valid)
            self.assertTrue(result_valid["success"])

        payload_invalid = {
            "sync_id": sync_id,
            "token": invalid_token,
            "health_score": random.randint(50, 100)
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": valid_token}):
            result_invalid = self.syncer.synchronize(metric_payload=payload_invalid)
            self.assertFalse(result_invalid["success"])

    def test_synchronize_remote_fetch_success(self):
        health_data = {"score": random.randint(1, 100), "status": uuid.uuid4().hex}
        security_data = {"issues": random.randint(0, 10), "risk": uuid.uuid4().hex}

        mock_health_response = MagicMock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = health_data

        mock_security_response = MagicMock()
        mock_security_response.status_code = 200
        mock_security_response.json.return_value = security_data

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_response, mock_security_response]
            
            result = self.syncer.synchronize(metric_payload=None)

            self.assertTrue(result["success"])
            self.assertEqual(result["health_data"], health_data)
            self.assertEqual(result["security_data"], security_data)
            self.assertEqual(mock_get.call_count, 2)

    def test_synchronize_remote_fetch_health_failure(self):
        error_status = 503
        error_text = uuid.uuid4().hex

        mock_health_response = MagicMock()
        mock_health_response.status_code = error_status
        mock_health_response.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_health_response
            
            result = self.syncer.synchronize(metric_payload=None)

            self.assertFalse(result["success"])
            self.assertEqual(result["status_code"], error_status)
            self.assertIn(error_text, result["error"])

    def test_synchronize_remote_fetch_security_failure(self):
        health_data = {"score": random.randint(1, 100)}
        error_status = 404
        error_text = uuid.uuid4().hex

        mock_health_response = MagicMock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = health_data

        mock_security_response = MagicMock()
        mock_security_response.status_code = error_status
        mock_security_response.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_response, mock_security_response]
            
            result = self.syncer.synchronize(metric_payload=None)

            self.assertFalse(result["success"])
            self.assertEqual(result["status_code"], error_status)
            self.assertIn(error_text, result["error"])

    def test_synchronize_exception_handling(self):
        exception_message = uuid.uuid4().hex

        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception(exception_message)
            
            result = self.syncer.synchronize(metric_payload=None)

            self.assertFalse(result["success"])
            self.assertEqual(result["status_code"], 500)
            self.assertIn(exception_message, result["error"])

    def test_export_audit_stream_with_raw(self):
        random_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_len = len(random_bytes)

        mock_raw = io.BytesIO(random_bytes)
        mock_response = MagicMock()
        mock_response.raw = mock_raw

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = self.syncer.export_audit_stream()

            self.assertEqual(result["stream_hash"], expected_hash)
            self.assertEqual(result["bytes_read"], expected_len)
            mock_get.assert_called_once_with(self.health_url, timeout=10)

    def test_export_audit_stream_with_content(self):
        random_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_len = len(random_bytes)

        mock_response = MagicMock()
        mock_response.raw = None
        mock_response.content = random_bytes

        with patch("requests.get", return_value=mock_response):
            result = self.syncer.export_audit_stream()

            self.assertEqual(result["stream_hash"], expected_hash)
            self.assertEqual(result["bytes_read"], expected_len)

if __name__ == "__main__":
    unittest.main()