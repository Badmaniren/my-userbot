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
        self.rand_repo_id = uuid.uuid4().hex
        self.rand_health_url = f"https://{uuid.uuid4().hex}.com/health"
        self.rand_security_url = f"https://{uuid.uuid4().hex}.com/security"
        self.rand_dir = f"./test_dir_{uuid.uuid4().hex}"
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.rand_repo_id,
            health_url=self.rand_health_url,
            security_url=self.rand_security_url,
            target_directory=self.rand_dir
        )

    def tearDown(self):
        if os.path.exists(self.rand_dir):
            for f in os.listdir(self.rand_dir):
                file_path = os.path.join(self.rand_dir, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.rand_dir)

    def test_synchronize_with_payload_no_env_token(self):
        rand_sync_id = uuid.uuid4().hex
        rand_token = uuid.uuid4().hex
        rand_health_score = random.randint(0, 100)
        rand_sec_score = random.randint(0, 100)
        rand_vuln = [uuid.uuid4().hex for _ in range(random.randint(1, 3))]

        payload = {
            "sync_id": rand_sync_id,
            "token": rand_token,
            "health_score": rand_health_score,
            "security_score": rand_sec_score,
            "vulnerabilities": rand_vuln
        }

        with patch.dict(os.environ, {}, clear=True):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], rand_sync_id)
        self.assertEqual(result["health_data"]["health_score"], rand_health_score)
        self.assertEqual(result["health_data"]["token"], rand_token)
        self.assertEqual(result["security_data"]["security_score"], rand_sec_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], rand_vuln)
        self.assertEqual(result["security_data"]["token"], rand_token)

        expected_file = os.path.join(self.rand_dir, f"audit_{rand_sync_id}.json")
        self.assertTrue(os.path.exists(expected_file))
        with open(expected_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["correlation_id"], rand_sync_id)
            self.assertEqual(data["health_metrics"]["health_score"], rand_health_score)
            self.assertEqual(data["security_metrics"]["security_score"], rand_sec_score)
            self.assertEqual(data["security_metrics"]["vulnerabilities"], rand_vuln)

    def test_synchronize_with_payload_env_token_match(self):
        rand_sync_id = uuid.uuid4().hex
        rand_token = uuid.uuid4().hex
        rand_health_score = random.randint(50, 100)

        payload = {
            "sync_id": rand_sync_id,
            "token": rand_token,
            "health_score": rand_health_score
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": rand_token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], rand_sync_id)
        self.assertEqual(result["health_data"]["token"], rand_token)

    def test_synchronize_with_payload_env_token_mismatch(self):
        rand_sync_id = uuid.uuid4().hex
        rand_env_token = uuid.uuid4().hex
        rand_bad_token = uuid.uuid4().hex

        payload = {
            "sync_id": rand_sync_id,
            "token": rand_bad_token
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": rand_env_token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], rand_sync_id)

    def test_synchronize_network_success(self):
        rand_health_dict = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(2)}
        rand_sec_dict = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(2)}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = rand_health_dict

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = 200
        mock_sec_resp.json.return_value = rand_sec_dict

        def mock_get(url, *args, **kwargs):
            if url == self.rand_health_url:
                return mock_health_resp
            elif url == self.rand_security_url:
                return mock_sec_resp
            return MagicMock(status_code=404)

        with patch("requests.get", side_effect=mock_get):
            result = self.syncer.synchronize(metric_payload=None)

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"], rand_health_dict)
        self.assertEqual(result["security_data"], rand_sec_dict)

    def test_synchronize_network_health_fail(self):
        rand_status = random.choice([400, 401, 403, 500, 502])
        rand_err_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = rand_status
        mock_health_resp.text = rand_err_text

        with patch("requests.get", return_value=mock_health_resp):
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], rand_status)
        self.assertEqual(result["error"], rand_err_text)

    def test_synchronize_network_security_fail(self):
        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = {uuid.uuid4().hex: uuid.uuid4().hex}

        rand_status = random.choice([404, 500, 503])
        rand_err_text = uuid.uuid4().hex

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = rand_status
        mock_sec_resp.text = rand_err_text

        def mock_get(url, *args, **kwargs):
            if url == self.rand_health_url:
                return mock_health_resp
            elif url == self.rand_security_url:
                return mock_sec_resp
            return MagicMock(status_code=404)

        with patch("requests.get", side_effect=mock_get):
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], rand_status)
        self.assertEqual(result["error"], rand_err_text)

    def test_synchronize_exception_handling(self):
        rand_exception_msg = uuid.uuid4().hex

        with patch("requests.get", side_effect=Exception(rand_exception_msg)):
            result = self.syncer.synchronize(metric_payload=None)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertIn(rand_exception_msg, result["error"])

    def test_export_audit_stream_raw_available(self):
        rand_bytes = uuid.uuid4().hex.encode("utf-8")
        expected_hash = hashlib.sha256(rand_bytes).hexdigest()
        expected_len = len(rand_bytes)

        mock_resp = MagicMock()
        mock_resp.raw = io.BytesIO(rand_bytes)

        with patch("requests.get", return_value=mock_resp):
            res = self.syncer.export_audit_stream()

        self.assertEqual(res["stream_hash"], expected_hash)
        self.assertEqual(res["bytes_read"], expected_len)

    def test_export_audit_stream_content_fallback(self):
        rand_bytes = uuid.uuid4().hex.encode("utf-8")
        expected_hash = hashlib.sha256(rand_bytes).hexdigest()
        expected_len = len(rand_bytes)

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = rand_bytes

        with patch("requests.get", return_value=mock_resp):
            res = self.syncer.export_audit_stream()

        self.assertEqual(res["stream_hash"], expected_hash)
        self.assertEqual(res["bytes_read"], expected_len)