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
        self.health_url = f"https://{uuid.uuid4().hex}.local/health"
        self.security_url = f"https://{uuid.uuid4().hex}.local/security"
        self.target_dir = f"/tmp/{uuid.uuid4().hex}"
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

    def test_synchronize_with_payload_success(self):
        sync_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        health_score = random.randint(50, 100)
        security_score = random.randint(50, 100)
        vulnerabilities = [uuid.uuid4().hex for _ in range(random.randint(1, 3))]

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)
        self.assertEqual(result["health_data"]["health_score"], health_score)
        self.assertEqual(result["health_data"]["token"], token)
        self.assertEqual(result["security_data"]["security_score"], security_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)

        expected_audit_file = os.path.join(self.target_dir, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_audit_file))
        with open(expected_audit_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("correlation_id"), sync_id)
        self.assertEqual(data["health_metrics"]["health_score"], health_score)
        self.assertEqual(data["security_metrics"]["security_score"], security_score)

    def test_synchronize_with_payload_token_mismatch(self):
        sync_id = uuid.uuid4().hex
        env_token = uuid.uuid4().hex
        bad_token = uuid.uuid4().hex

        payload = {
            "sync_id": sync_id,
            "token": bad_token
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)

    def test_synchronize_network_get_success(self):
        health_payload = {uuid.uuid4().hex: random.randint(1, 100)}
        security_payload = {uuid.uuid4().hex: random.randint(1, 100)}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_payload

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = 200
        mock_sec_resp.json.return_value = security_payload

        syncer_no_dir = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            health_url=self.health_url,
            security_url=self.security_url
        )

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]
            result = syncer_no_dir.synchronize()

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("health_data"), health_payload)
        self.assertEqual(result.get("security_data"), security_payload)

    def test_synchronize_network_health_error(self):
        err_code = random.choice([400, 401, 403, 404, 500])
        err_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = err_code
        mock_health_resp.text = err_text

        with patch("requests.get", return_value=mock_health_resp) as mock_get:
            result = self.syncer.synchronize()

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), err_code)
        self.assertEqual(result.get("error"), err_text)

    def test_synchronize_network_security_error(self):
        health_payload = {uuid.uuid4().hex: random.randint(1, 100)}
        err_code = random.choice([400, 502, 503])
        err_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_payload

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = err_code
        mock_sec_resp.text = err_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]
            result = self.syncer.synchronize()

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), err_code)
        self.assertEqual(result.get("error"), err_text)

    def test_synchronize_network_exception(self):
        exception_msg = uuid.uuid4().hex

        with patch("requests.get", side_effect=Exception(exception_msg)) as mock_get:
            result = self.syncer.synchronize()

        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), 500)
        self.assertIn(exception_msg, result.get("error"))

    def test_export_audit_stream_raw(self):
        random_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=128)).encode("utf-8")
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_resp = MagicMock()
        mock_resp.raw = io.BytesIO(random_bytes)
        mock_resp.content = b""

        with patch("requests.get", return_value=mock_resp) as mock_get:
            result = self.syncer.export_audit_stream()

        self.assertEqual(result.get("stream_hash"), expected_hash)
        self.assertEqual(result.get("bytes_read"), len(random_bytes))

    def test_export_audit_stream_content(self):
        random_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=64)).encode("utf-8")
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        with patch("requests.get", return_value=mock_resp) as mock_get:
            result = self.syncer.export_audit_stream()

        self.assertEqual(result.get("stream_hash"), expected_hash)
        self.assertEqual(result.get("bytes_read"), len(random_bytes))

if __name__ == "__main__":
    unittest.main()