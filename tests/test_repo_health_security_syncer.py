import unittest
from unittest.mock import patch, MagicMock
import os
import io
import uuid
import random
import string
import json
import hashlib
import requests
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncer(unittest.TestCase):

    def setUp(self):
        self.repo_id = str(uuid.uuid4())
        self.health_url = f"http://{uuid.uuid4().hex}.local/health"
        self.security_url = f"http://{uuid.uuid4().hex}.local/security"
        self.target_directory = f"./temp_audit_{uuid.uuid4().hex}"
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            health_url=self.health_url,
            security_url=self.security_url,
            target_directory=self.target_directory
        )

    def tearDown(self):
        if os.path.exists(self.target_directory):
            for file in os.listdir(self.target_directory):
                file_path = os.path.join(self.target_directory, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.target_directory)

    def test_synchronize_with_payload_no_token_env(self):
        sync_id = str(uuid.uuid4())
        token = uuid.uuid4().hex
        health_score = random.randint(0, 100)
        security_score = random.randint(0, 100)
        vulnerabilities = [uuid.uuid4().hex for _ in range(random.randint(1, 3))]

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }

        with patch.dict(os.environ, {}, clear=True):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)
        self.assertEqual(result["health_data"]["health_score"], health_score)
        self.assertEqual(result["security_data"]["security_score"], security_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)

        expected_file = os.path.join(self.target_directory, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file))
        with open(expected_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["correlation_id"], sync_id)
        self.assertEqual(data["health_metrics"]["health_score"], health_score)

    def test_synchronize_with_payload_token_mismatch(self):
        sync_id = str(uuid.uuid4())
        token = uuid.uuid4().hex
        expected_token = uuid.uuid4().hex

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": random.randint(0, 100),
            "security_score": random.randint(0, 100),
            "vulnerabilities": []
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": expected_token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], sync_id)
        expected_file = os.path.join(self.target_directory, f"audit_{sync_id}.json")
        self.assertFalse(os.path.exists(expected_file))

    def test_synchronize_with_payload_token_match(self):
        sync_id = str(uuid.uuid4())
        token = uuid.uuid4().hex

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": random.randint(0, 100),
            "security_score": random.randint(0, 100),
            "vulnerabilities": []
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)

    def test_synchronize_remote_success(self):
        health_data_mock = {uuid.uuid4().hex: random.randint(1, 100)}
        security_data_mock = {uuid.uuid4().hex: random.choice([True, False])}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_data_mock

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = 200
        mock_sec_resp.json.return_value = security_data_mock

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]
            result = self.syncer.synchronize(metric_payload=None)

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"], health_data_mock)
        self.assertEqual(result["security_data"], security_data_mock)

    def test_synchronize_remote_health_failure(self):
        error_code = random.choice([400, 401, 403, 404, 500])
        error_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = error_code
        mock_health_resp.text = error_text

        with patch("requests.get", return_value=mock_health_resp) as mock_get:
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], error_code)
        self.assertEqual(result["error"], error_text)

    def test_synchronize_remote_security_failure(self):
        health_data_mock = {uuid.uuid4().hex: random.randint(1, 100)}
        error_code = random.choice([400, 403, 502, 503])
        error_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_data_mock

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = error_code
        mock_sec_resp.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], error_code)
        self.assertEqual(result["error"], error_text)

    def test_synchronize_remote_exception(self):
        exception_msg = uuid.uuid4().hex

        with patch("requests.get", side_effect=Exception(exception_msg)) as mock_get:
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertEqual(result["error"], exception_msg)

    def test_export_audit_stream_with_raw(self):
        random_bytes = os.urandom(random.randint(16, 64))
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_resp = MagicMock()
        mock_resp.raw = io.BytesIO(random_bytes)
        mock_resp.content = b""

        with patch("requests.get", return_value=mock_resp) as mock_get:
            res = self.syncer.export_audit_stream()

        self.assertEqual(res["stream_hash"], expected_hash)
        self.assertEqual(res["bytes_read"], len(random_bytes))

    def test_export_audit_stream_without_raw(self):
        random_bytes = os.urandom(random.randint(16, 64))
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        with patch("requests.get", return_value=mock_resp) as mock_get:
            res = self.syncer.export_audit_stream()

        self.assertEqual(res["stream_hash"], expected_hash)
        self.assertEqual(res["bytes_read"], len(random_bytes))