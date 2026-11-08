import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import hashlib
import random
import string
import io
import json

from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncer(unittest.TestCase):

    def setUp(self):
        self.repo_id = str(uuid.uuid4())
        self.health_url = f"http://{uuid.uuid4().hex}.local/health"
        self.security_url = f"http://{uuid.uuid4().hex}.local/security"
        self.target_directory = f"./test_audit_dir_{uuid.uuid4().hex}"
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

    def test_init_attributes(self):
        rand_repo = str(uuid.uuid4())
        rand_health = f"http://{uuid.uuid4().hex}.test/h"
        rand_sec = f"http://{uuid.uuid4().hex}.test/s"
        rand_dir = f"./{uuid.uuid4().hex}"

        syncer = RepoHealthSecuritySyncer(
            repo_id=rand_repo,
            health_url=rand_health,
            security_url=rand_sec,
            target_directory=rand_dir
        )

        self.assertEqual(syncer.repo_id, rand_repo)
        self.assertEqual(syncer.health_url, rand_health)
        self.assertEqual(syncer.security_url, rand_sec)
        self.assertEqual(syncer.target_directory, rand_dir)

    def test_synchronize_with_payload_success(self):
        sync_id = str(uuid.uuid4())
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

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertTrue(result["success"])
        self.assertEqual(result["synced_id"], sync_id)
        self.assertEqual(result["health_data"]["health_score"], health_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)
        self.assertEqual(result["security_data"]["token"], token)
        self.assertEqual(result["security_data"]["security_score"], security_score)

        expected_file = os.path.join(self.target_directory, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file))

        with open(expected_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["correlation_id"], sync_id)
            self.assertEqual(data["health_metrics"]["health_score"], health_score)
            self.assertEqual(data["security_metrics"]["vulnerabilities"], vulnerabilities)

    def test_synchronize_with_payload_invalid_token(self):
        sync_id = str(uuid.uuid4())
        token = uuid.uuid4().hex
        env_token = uuid.uuid4().hex

        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": random.randint(1, 100),
            "vulnerabilities": random.randint(0, 5),
            "security_score": random.randint(1, 100)
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = self.syncer.synchronize(metric_payload=payload)

        self.assertFalse(result["success"])
        self.assertEqual(result["synced_id"], sync_id)

    def test_synchronize_network_success(self):
        health_data = {"score": random.randint(50, 100), "status": uuid.uuid4().hex}
        security_data = {"vulns": random.randint(0, 5), "level": uuid.uuid4().hex}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_data

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = 200
        mock_sec_resp.json.return_value = security_data

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]
            result = self.syncer.synchronize()

        self.assertTrue(result["success"])
        self.assertEqual(result["health_data"], health_data)
        self.assertEqual(result["security_data"], security_data)

    def test_synchronize_health_fail(self):
        status_code = random.choice([400, 401, 403, 404, 500, 502])
        error_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = status_code
        mock_health_resp.text = error_text

        with patch("requests.get", return_value=mock_health_resp):
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], status_code)
        self.assertIn(error_text, result["error"])

    def test_synchronize_security_fail(self):
        health_data = {"score": random.randint(50, 100)}
        status_code = random.choice([400, 401, 403, 404, 500, 502])
        error_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_data

        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = status_code
        mock_sec_resp.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_sec_resp]
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], status_code)
        self.assertIn(error_text, result["error"])

    def test_synchronize_exception(self):
        exception_msg = uuid.uuid4().hex

        with patch("requests.get", side_effect=Exception(exception_msg)):
            result = self.syncer.synchronize()

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 500)
        self.assertEqual(result["error"], exception_msg)

    def test_export_audit_stream_with_raw(self):
        random_bytes = os.urandom(random.randint(16, 64))
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_raw = MagicMock()
        mock_raw.read.return_value = random_bytes

        mock_resp = MagicMock()
        mock_resp.raw = mock_raw

        with patch("requests.get", return_value=mock_resp):
            result = self.syncer.export_audit_stream()

        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], len(random_bytes))

    def test_export_audit_stream_with_content(self):
        random_bytes = os.urandom(random.randint(16, 64))
        expected_hash = hashlib.sha256(random_bytes).hexdigest()

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        with patch("requests.get", return_value=mock_resp):
            result = self.syncer.export_audit_stream()

        self.assertEqual(result["stream_hash"], expected_hash)
        self.assertEqual(result["bytes_read"], len(random_bytes))