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
        self.random_repo_id = uuid.uuid4().hex
        self.random_health_url = f"http://{uuid.uuid4().hex}.internal/health"
        self.random_security_url = f"http://{uuid.uuid4().hex}.internal/security"
        self.random_target_dir = os.path.join("temp_audit_" + uuid.uuid4().hex)
        
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.random_repo_id,
            health_url=self.random_health_url,
            security_url=self.random_security_url,
            target_directory=self.random_target_dir
        )

    def tearDown(self):
        if os.path.exists(self.random_target_dir):
            for filename in os.listdir(self.random_target_dir):
                file_path = os.path.join(self.random_target_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.random_target_dir)

    def test_synchronize_with_payload_success(self):
        random_sync_id = uuid.uuid4().hex
        random_token = uuid.uuid4().hex
        random_health_score = random.randint(50, 100)
        random_security_score = random.randint(50, 100)
        random_vuln_name = uuid.uuid4().hex

        metric_payload = {
            "sync_id": random_sync_id,
            "token": random_token,
            "health_score": random_health_score,
            "security_score": random_security_score,
            "vulnerabilities": [random_vuln_name]
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": random_token}):
            result = self.syncer.synchronize(metric_payload=metric_payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], random_sync_id)
        self.assertEqual(result["health_data"]["health_score"], random_health_score)
        self.assertEqual(result["security_data"]["security_score"], random_security_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], [random_vuln_name])
        self.assertEqual(result["security_data"]["token"], random_token)

        expected_file_path = os.path.join(self.random_target_dir, f"audit_{random_sync_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)

        self.assertEqual(file_content["correlation_id"], random_sync_id)
        self.assertEqual(file_content["health_metrics"]["health_score"], random_health_score)
        self.assertEqual(file_content["security_metrics"]["vulnerabilities"], [random_vuln_name])

    def test_synchronize_with_payload_token_mismatch(self):
        random_sync_id = uuid.uuid4().hex
        provided_token = uuid.uuid4().hex
        env_token = uuid.uuid4().hex

        metric_payload = {
            "sync_id": random_sync_id,
            "token": provided_token,
            "health_score": random.randint(0, 49),
            "vulnerabilities": []
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = self.syncer.synchronize(metric_payload=metric_payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], random_sync_id)

    def test_synchronize_network_mode_success(self):
        random_health_data = {uuid.uuid4().hex: random.randint(1, 100)}
        random_security_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_health_response = MagicMock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = random_health_data

        mock_security_response = MagicMock()
        mock_security_response.status_code = 200
        mock_security_response.json.return_value = random_security_data

        def side_effect(url, timeout):
            if url == self.random_health_url:
                return mock_health_response
            elif url == self.random_security_url:
                return mock_security_response
            raise ValueError(f"Unexpected URL: {url}")

        with patch("requests.get", side_effect=side_effect) as mock_get:
            result = self.syncer.synchronize()

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"], random_health_data)
        self.assertEqual(result["security_data"], random_security_data)
        self.assertEqual(mock_get.call_count, 2)

    def test_synchronize_network_mode_health_failure(self):
        random_status = random.choice([400, 401, 403, 404, 500, 502])
        random_error_text = uuid.uuid4().hex

        mock_health_response = MagicMock()
        mock_health_response.status_code = random_status
        mock_health_response.text = random_error_text

        with patch("requests.get", return_value=mock_health_response) as mock_get:
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], random_status)
        self.assertIn(random_error_text, result["error"])
        self.assertIn(str(random_status), result["error"])

    def test_synchronize_network_mode_security_failure(self):
        random_health_data = {uuid.uuid4().hex: random.randint(1, 100)}
        random_status = random.choice([500, 503, 504])
        random_error_text = uuid.uuid4().hex

        mock_health_response = MagicMock()
        mock_health_response.status_code = 200
        mock_health_response.json.return_value = random_health_data

        mock_security_response = MagicMock()
        mock_security_response.status_code = random_status
        mock_security_response.text = random_error_text

        def side_effect(url, timeout):
            if url == self.random_health_url:
                return mock_health_response
            elif url == self.random_security_url:
                return mock_security_response
            raise ValueError(f"Unexpected URL: {url}")

        with patch("requests.get", side_effect=side_effect):
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], random_status)
        self.assertIn(random_error_text, result["error"])

    def test_synchronize_network_mode_exception(self):
        random_exception_msg = uuid.uuid4().hex

        with patch("requests.get", side_effect=Exception(random_exception_msg)):
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertEqual(result["error"], random_exception_msg)

    def test_export_audit_stream_with_raw(self):
        random_bytes = uuid.uuid4().bytes + "".join(random.choices(string.ascii_letters, k=32)).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_raw_stream = io.BytesIO(random_bytes)
        mock_response = MagicMock()
        mock_response.raw = mock_raw_stream
        del mock_response.content

        with patch("requests.get", return_value=mock_response) as mock_get:
            export_result = self.syncer.export_audit_stream()

        self.assertEqual(export_result["stream_hash"], expected_hash)
        self.assertEqual(export_result["bytes_read"], len(random_bytes))
        mock_get.assert_called_once_with(self.random_health_url, timeout=10)

    def test_export_audit_stream_with_content(self):
        random_bytes = uuid.uuid4().bytes + "".join(random.choices(string.digits, k=16)).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_response = MagicMock()
        mock_response.raw = None
        mock_response.content = random_bytes

        with patch("requests.get", return_value=mock_response):
            export_result = self.syncer.export_audit_stream()

        self.assertEqual(export_result["stream_hash"], expected_hash)
        self.assertEqual(export_result["bytes_read"], len(random_bytes))

if __name__ == "__main__":
    unittest.main()