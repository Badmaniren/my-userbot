import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import string
import json
import io
import hashlib
import requests

from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncer(unittest.TestCase):

    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.health_url = f"https://api.github.test/{uuid.uuid4().hex}/health"
        self.security_url = f"https://api.github.test/{uuid.uuid4().hex}/security"
        self.target_dir = f"audit_dir_{uuid.uuid4().hex}"
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            health_url=self.health_url,
            security_url=self.security_url,
            target_directory=self.target_dir
        )

    def tearDown(self):
        if os.path.exists(self.target_dir):
            for f in os.listdir(self.target_dir):
                file_path = os.path.join(self.target_dir, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.target_dir)

    def test_synchronize_with_payload_no_token_env(self):
        sync_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        health_score = random.randint(1, 100)
        vulnerabilities = random.randint(0, 10)
        security_score = random.randint(1, 100)

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "vulnerabilities": vulnerabilities,
            "security_score": security_score
        }

        with patch.dict(os.environ, {}, clear=True):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)
        self.assertEqual(result["health_data"]["health_score"], health_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)
        self.assertEqual(result["security_data"]["token"], token)
        self.assertEqual(result["security_data"]["security_score"], security_score)

        expected_file = os.path.join(self.target_dir, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file))
        with open(expected_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["correlation_id"], sync_id)
            self.assertEqual(data["health_metrics"]["health_score"], health_score)

    def test_synchronize_with_payload_valid_token(self):
        sync_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        health_score = random.randint(50, 100)

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "vulnerabilities": 0,
            "security_score": 100
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)

    def test_synchronize_with_payload_invalid_token(self):
        sync_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        expected_token = uuid.uuid4().hex

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": random.randint(1, 100),
            "vulnerabilities": 2,
            "security_score": 50
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": expected_token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], sync_id)

    def test_synchronize_fetch_success(self):
        health_payload = {"health": uuid.uuid4().hex, "score": random.randint(1, 100)}
        security_payload = {"security": uuid.uuid4().hex, "issues": random.randint(0, 5)}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_payload

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = 200
        mock_sec_resp.json.return_value = security_payload

        def side_effect(url, *args, **kwargs):
            if url == self.health_url:
                return mock_health_resp
            elif url == self.security_url:
                return mock_sec_resp
            raise ValueError(f"Unexpected URL: {url}")

        with patch("requests.get", side_effect=side_effect):
            result = self.syncer.synchronize()

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"], health_payload)
        self.assertEqual(result["security_data"], security_payload)

    def test_synchronize_fetch_health_failure(self):
        status_code = random.choice([400, 401, 403, 404, 500, 502])
        error_text = ''.join(random.choices(string.ascii_letters, k=15))

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = status_code
        mock_health_resp.text = error_text

        with patch("requests.get", return_value=mock_health_resp):
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], status_code)
        self.assertEqual(result["error"], error_text)

    def test_synchronize_fetch_security_failure(self):
        health_payload = {"status": "ok"}
        status_code = random.choice([500, 502, 503, 504])
        error_text = ''.join(random.choices(string.ascii_letters, k=12))

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_payload

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = status_code
        mock_sec_resp.text = error_text

        def side_effect(url, *args, **kwargs):
            if url == self.health_url:
                return mock_health_resp
            elif url == self.security_url:
                return mock_sec_resp

        with patch("requests.get", side_effect=side_effect):
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], status_code)
        self.assertEqual(result["error"], error_text)

    def test_synchronize_fetch_exception(self):
        exception_msg = uuid.uuid4().hex

        with patch("requests.get", side_effect=Exception(exception_msg)):
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertIn(exception_msg, result["error"])

    def test_export_audit_stream_with_raw(self):
        random_bytes = os.urandom(random.randint(32, 128))
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_resp = MagicMock()
        mock_resp.raw = io.BytesIO(random_bytes)
        mock_resp.content = b"fallback_content"

        with patch("requests.get", return_value=mock_resp) as mock_get:
            result = self.syncer.export_audit_stream()

        mock_get.assert_called_once_with(self.health_url)
        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], len(random_bytes))

    def test_export_audit_stream_without_raw(self):
        random_bytes = os.urandom(random.randint(32, 128))
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        with patch("requests.get", return_value=mock_resp):
            result = self.syncer.export_audit_stream()

        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], len(random_bytes))