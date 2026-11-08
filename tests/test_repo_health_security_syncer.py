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
        rand_sec_url = f"https://{uuid.uuid4().hex}.com/security"
        rand_dir = f"temp_audit_{uuid.uuid4().hex}"
        
        syncer = RepoHealthSecuritySyncer(
            repo_id=rand_repo_id,
            health_url=rand_health_url,
            security_url=rand_sec_url,
            target_directory=rand_dir
        )

        sync_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        health_score = random.randint(1, 100)
        vulnerabilities = random.randint(0, 5)
        security_score = random.randint(1, 100)

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "vulnerabilities": vulnerabilities,
            "security_score": security_score
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            result = syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)
        self.assertEqual(result["health_data"]["health_score"], health_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)
        self.assertEqual(result["security_data"]["token"], token)
        self.assertEqual(result["security_data"]["security_score"], security_score)

        expected_file_path = os.path.join(rand_dir, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
        self.assertEqual(file_data["correlation_id"], sync_id)
        self.assertEqual(file_data["health_metrics"]["health_score"], health_score)
        self.assertEqual(file_data["security_metrics"]["vulnerabilities"], vulnerabilities)

        if os.path.exists(expected_file_path):
            os.remove(expected_file_path)
        if os.path.exists(rand_dir):
            os.rmdir(rand_dir)

    def test_synchronize_with_payload_token_mismatch(self):
        syncer = RepoHealthSecuritySyncer(
            repo_id=uuid.uuid4().hex,
            health_url=f"https://{uuid.uuid4().hex}.com/health",
            security_url=f"https://{uuid.uuid4().hex}.com/sec",
            target_directory=None
        )

        payload = {
            "sync_id": uuid.uuid4().hex,
            "token": uuid.uuid4().hex,
            "health_score": random.randint(10, 50),
            "vulnerabilities": random.randint(1, 10),
            "security_score": random.randint(10, 50)
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": uuid.uuid4().hex}):
            result = syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])

    def test_synchronize_requests_success(self):
        rand_health_url = f"https://{uuid.uuid4().hex}.com/health"
        rand_sec_url = f"https://{uuid.uuid4().hex}.com/sec"
        syncer = RepoHealthSecuritySyncer(
            repo_id=uuid.uuid4().hex,
            health_url=rand_health_url,
            security_url=rand_sec_url,
            target_directory=None
        )

        health_data_mock = {"health_status": uuid.uuid4().hex, "score": random.randint(50, 100)}
        security_data_mock = {"status": uuid.uuid4().hex, "issues": random.randint(0, 3)}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_data_mock

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = 200
        mock_sec_resp.json.return_value = security_data_mock

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]
            result = syncer.synchronize(metric_payload=None)

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"], health_data_mock)
        self.assertEqual(result["security_data"], security_data_mock)

    def test_synchronize_health_request_failure(self):
        rand_health_url = f"https://{uuid.uuid4().hex}.com/health"
        rand_sec_url = f"https://{uuid.uuid4().hex}.com/sec"
        syncer = RepoHealthSecuritySyncer(
            repo_id=uuid.uuid4().hex,
            health_url=rand_health_url,
            security_url=rand_sec_url,
            target_directory=None
        )

        status_code = random.choice([400, 401, 403, 404, 500, 503])
        error_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = status_code
        mock_health_resp.text = error_text

        with patch("requests.get", return_value=mock_health_resp):
            result = syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], status_code)
        self.assertIn(error_text, result["error"])

    def test_synchronize_security_request_failure(self):
        rand_health_url = f"https://{uuid.uuid4().hex}.com/health"
        rand_sec_url = f"https://{uuid.uuid4().hex}.com/sec"
        syncer = RepoHealthSecuritySyncer(
            repo_id=uuid.uuid4().hex,
            health_url=rand_health_url,
            security_url=rand_sec_url,
            target_directory=None
        )

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = {"ok": True}

        status_code = random.choice([400, 401, 403, 404, 500, 503])
        error_text = uuid.uuid4().hex

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = status_code
        mock_sec_resp.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]
            result = syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], status_code)
        self.assertIn(error_text, result["error"])

    def test_synchronize_request_exception(self):
        syncer = RepoHealthSecuritySyncer(
            repo_id=uuid.uuid4().hex,
            health_url=f"https://{uuid.uuid4().hex}.com/health",
            security_url=f"https://{uuid.uuid4().hex}.com/sec",
            target_directory=None
        )

        exception_message = uuid.uuid4().hex

        with patch("requests.get", side_effect=Exception(exception_message)):
            result = syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertIn(exception_message, result["error"])

    def test_export_audit_stream(self):
        syncer = RepoHealthSecuritySyncer(
            repo_id=uuid.uuid4().hex,
            health_url=f"https://{uuid.uuid4().hex}.com/stream",
            security_url=f"https://{uuid.uuid4().hex}.com/sec",
            target_directory=None
        )

        random_bytes = uuid.uuid4().hex.encode("utf-8") + os.urandom(32)
        mock_resp = MagicMock()
        mock_resp.raw = io.BytesIO(random_bytes)

        with patch("requests.get", return_value=mock_resp):
            result = syncer.export_audit_stream()

        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], len(random_bytes))

    def test_export_audit_stream_fallback_content(self):
        syncer = RepoHealthSecuritySyncer(
            repo_id=uuid.uuid4().hex,
            health_url=f"https://{uuid.uuid4().hex}.com/stream",
            security_url=f"https://{uuid.uuid4().hex}.com/sec",
            target_directory=None
        )

        random_bytes = uuid.uuid4().hex.encode("utf-8") + os.urandom(16)
        mock_resp = MagicMock()
        del mock_resp.raw
        mock_resp.content = random_bytes

        with patch("requests.get", return_value=mock_resp):
            result = syncer.export_audit_stream()

        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], len(random_bytes))