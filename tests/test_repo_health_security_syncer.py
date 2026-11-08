import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import string
import json
import io
import hashlib
from skills.repo_health_security_syncer import RepoHealthSecuritySyncer

class TestRepoHealthSecuritySyncer(unittest.TestCase):
    def setUp(self):
        self.repo_id = str(uuid.uuid4())
        self.health_url = f"http://{uuid.uuid4().hex[:8]}.local/health"
        self.security_url = f"http://{uuid.uuid4().hex[:8]}.local/security"
        self.target_directory = f"./audit_dir_{uuid.uuid4().hex[:6]}"
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
        assert self.syncer.repo_id == self.repo_id
        assert self.syncer.health_url == self.health_url
        assert self.syncer.security_url == self.security_url
        assert self.syncer.target_directory == self.target_directory

    def test_synchronize_with_payload_success_token(self):
        sync_id = str(uuid.uuid4())
        token = uuid.uuid4().hex
        health_score = random.randint(50, 100)
        security_score = random.randint(50, 100)
        vulnerabilities = [uuid.uuid4().hex for _ in range(random.randint(1, 3))]

        metric_payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            result = self.syncer.synchronize(metric_payload=metric_payload)

        assert result["success"] is True
        assert result["synced_id"] == sync_id
        assert result["health_data"]["health_score"] == health_score
        assert result["security_data"]["security_score"] == security_score
        assert result["security_data"]["vulnerabilities"] == vulnerabilities
        assert result["security_data"]["token"] == token

        expected_file_path = os.path.join(self.target_directory, f"audit_{sync_id}.json")
        assert os.path.exists(expected_file_path)
        with open(expected_file_path, "r", encoding="utf-8") as f:
            audit_data = json.load(f)
        assert audit_data["correlation_id"] == sync_id
        assert audit_data["health_metrics"]["health_score"] == health_score
        assert audit_data["security_metrics"]["vulnerabilities"] == vulnerabilities

    def test_synchronize_with_payload_invalid_token(self):
        sync_id = str(uuid.uuid4())
        token = uuid.uuid4().hex
        env_token = uuid.uuid4().hex
        health_score = random.randint(0, 49)

        metric_payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = self.syncer.synchronize(metric_payload=metric_payload)

        assert result["success"] is False
        assert result["synced_id"] == sync_id

    def test_synchronize_network_success(self):
        health_data_mock = {"health_score": random.randint(1, 100), "status": uuid.uuid4().hex}
        security_data_mock = {"security_score": random.randint(1, 100), "issues": []}

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_data_mock

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = 200
        mock_security_resp.json.return_value = security_data_mock

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
            result = self.syncer.synchronize()

        assert result["success"] is True
        assert result["health_data"] == health_data_mock
        assert result["security_data"] == security_data_mock
        assert mock_get.call_count == 2

    def test_synchronize_health_fail(self):
        status_code = random.choice([400, 401, 403, 404, 500, 502])
        error_text = uuid.uuid4().hex

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = status_code
        mock_health_resp.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_health_resp
            result = self.syncer.synchronize()

        assert result["success"] is False
        assert result["status_code"] == status_code
        assert error_text in result["error"]
        assert mock_get.call_count == 1

    def test_synchronize_security_fail(self):
        health_data_mock = {"health_score": random.randint(1, 100)}
        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_data_mock

        status_code = random.choice([400, 404, 500, 503])
        error_text = uuid.uuid4().hex

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = status_code
        mock_security_resp.text = error_text

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
            result = self.syncer.synchronize()

        assert result["success"] is False
        assert result["status_code"] == status_code
        assert error_text in result["error"]
        assert mock_get.call_count == 2

    def test_synchronize_exception(self):
        exception_message = uuid.uuid4().hex

        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception(exception_message)
            result = self.syncer.synchronize()

        assert result["success"] is False
        assert result["status_code"] == 500
        assert exception_message in result["error"]

    def test_export_audit_stream_with_raw(self):
        random_bytes = uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=32)).encode('utf-8')
        mock_raw = io.BytesIO(random_bytes)

        mock_resp = MagicMock()
        mock_resp.raw = mock_raw
        mock_resp.content = b"fallback"

        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_len = len(random_bytes)

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_resp
            res = self.syncer.export_audit_stream()

        assert res["stream_hash"] == expected_hash
        assert res["bytes_read"] == expected_len

    def test_export_audit_stream_with_content(self):
        random_bytes = uuid.uuid4().bytes + ''.join(random.choices(string.digits, k=32)).encode('utf-8')

        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes

        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        expected_len = len(random_bytes)

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_resp
            res = self.syncer.export_audit_stream()

        assert res["stream_hash"] == expected_hash
        assert res["bytes_read"] == expected_len