import unittest
from unittest.mock import patch, mock_open
import os
import uuid
import random
import string
import io
import json
import requests
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncer(unittest.TestCase):
    def setUp(self):
        self.repo_id = str(uuid.uuid4())
        self.health_url = f"https://{uuid.uuid4().hex}.internal/health"
        self.security_url = f"https://{uuid.uuid4().hex}.internal/security"
        self.target_dir = f"audit_dir_{uuid.uuid4().hex[:8]}"
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            health_url=self.health_url,
            security_url=self.security_url,
            target_directory=self.target_dir
        )

    def test_synchronize_with_payload_no_env_token(self):
        sync_id = uuid.uuid4().hex
        health_score = random.randint(1, 100)
        security_score = random.randint(1, 100)
        vulnerabilities = [uuid.uuid4().hex, uuid.uuid4().hex]
        
        payload = {
            "sync_id": sync_id,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }

        with patch.dict(os.environ, {}, clear=True), \
             patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open()) as mock_file:
            
            result = self.syncer.synchronize(metric_payload=payload)

            self.assertTrue(result["success"])
            self.assertEqual(result["synced_id"], sync_id)
            self.assertEqual(result["health_data"]["health_score"], health_score)
            self.assertEqual(result["security_data"]["security_score"], security_score)
            self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)
            mock_file.assert_called_once()

    def test_synchronize_with_payload_matching_env_token(self):
        sync_id = uuid.uuid4().hex
        env_token = uuid.uuid4().hex
        token = env_token
        health_score = random.randint(50, 100)
        security_score = random.randint(50, 100)
        vulnerabilities = [uuid.uuid4().hex]

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}), \
             patch("os.path.exists", return_value=False), \
             patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_open()) as mock_file:
            
            result = self.syncer.synchronize(metric_payload=payload)

            self.assertTrue(result["success"])
            self.assertEqual(result["synced_id"], sync_id)
            self.assertEqual(result["health_data"]["token"], token)
            self.assertEqual(result["security_data"]["token"], token)
            mock_makedirs.assert_called_once_with(self.target_dir, exist_ok=True)
            mock_file.assert_called_once()

    def test_synchronize_with_payload_mismatch_env_token(self):
        sync_id = uuid.uuid4().hex
        env_token = uuid.uuid4().hex
        wrong_token = uuid.uuid4().hex

        payload = {
            "sync_id": sync_id,
            "token": wrong_token,
            "health_score": random.randint(1, 50),
            "security_score": random.randint(1, 50),
            "vulnerabilities": []
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = self.syncer.synchronize(metric_payload=payload)

            self.assertFalse(result["success"])
            self.assertEqual(result["synced_id"], sync_id)

    def test_synchronize_fetch_success(self):
        health_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        security_payload = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_health_resp = requests.Response()
        mock_health_resp.status_code = 200
        mock_health_resp.json = lambda: health_payload

        mock_security_resp = requests.Response()
        mock_security_resp.status_code = 200
        mock_security_resp.json = lambda: security_payload

        def side_effect(url):
            if url == self.health_url:
                return mock_health_resp
            elif url == self.security_url:
                return mock_security_resp
            raise requests.exceptions.RequestException("Unknown URL")

        with patch("requests.get", side_effect=side_effect):
            result = self.syncer.synchronize()

            self.assertTrue(result["success"])
            self.assertEqual(result["health_data"], health_payload)
            self.assertEqual(result["security_data"], security_payload)

    def test_synchronize_health_fail(self):
        err_code = random.choice([400, 401, 403, 404, 500, 502])
        err_text = uuid.uuid4().hex

        mock_health_resp = requests.Response()
        mock_health_resp.status_code = err_code
        mock_health_resp._content = err_text.encode('utf-8')

        with patch("requests.get", return_value=mock_health_resp):
            result = self.syncer.synchronize()

            self.assertFalse(result["success"])
            self.assertEqual(result["status_code"], err_code)
            self.assertIn(err_text, result["error"])

    def test_synchronize_security_fail(self):
        health_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_health_resp = requests.Response()
        mock_health_resp.status_code = 200
        mock_health_resp.json = lambda: health_payload

        err_code = random.choice([400, 403, 404, 500, 503])
        err_text = uuid.uuid4().hex

        mock_security_resp = requests.Response()
        mock_security_resp.status_code = err_code
        mock_security_resp._content = err_text.encode('utf-8')

        def side_effect(url):
            if url == self.health_url:
                return mock_health_resp
            elif url == self.security_url:
                return mock_security_resp
            raise requests.exceptions.RequestException()

        with patch("requests.get", side_effect=side_effect):
            result = self.syncer.synchronize()

            self.assertFalse(result["success"])
            self.assertEqual(result["status_code"], err_code)
            self.assertIn(err_text, result["error"])

    def test_synchronize_exception_handling(self):
        err_msg = uuid.uuid4().hex

        with patch("requests.get", side_effect=Exception(err_msg)):
            result = self.syncer.synchronize()

            self.assertFalse(result["success"])
            self.assertEqual(result["status_code"], 500)
            self.assertIn(err_msg, result["error"])

    def test_export_audit_stream_with_raw(self):
        random_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_raw = io.BytesIO(random_bytes)
        mock_resp = requests.Response()
        mock_resp.raw = mock_raw

        with patch("requests.get", return_value=mock_resp):
            result = self.syncer.export_audit_stream()

            self.assertEqual(result["stream_hash"], expected_hash)
            self.assertEqual(result["bytes_read"], len(random_bytes))

    def test_export_audit_stream_fallback_content(self):
        random_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_resp = requests.Response()
        mock_resp.raw = None
        mock_resp._content = random_bytes

        with patch("requests.get", return_value=mock_resp):
            result = self.syncer.export_audit_stream()

            self.assertEqual(result["stream_hash"], expected_hash)
            self.assertEqual(result["bytes_read"], len(random_bytes))