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
    
    def _random_string(self, length=10):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def test_synchronize_with_payload_success(self):
        repo_id = uuid.uuid4().hex
        health_url = f"https://{self._random_string()}.org/{self._random_string()}"
        security_url = f"https://{self._random_string()}.org/{self._random_string()}"
        target_dir = os.path.join("temp_test_dir_" + uuid.uuid4().hex)
        
        syncer = RepoHealthSecuritySyncer(repo_id=repo_id, health_url=health_url, security_url=security_url, target_directory=target_dir)
        
        sync_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        health_score = random.randint(1, 100)
        security_score = random.randint(1, 100)
        vulnerabilities = random.randint(0, 10)
        
        payload = {
            "sync_id": sync_id,
            "token": token,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }
        
        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": token}):
            result = syncer.synchronize(metric_payload=payload)
            
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)
        self.assertIn("health_data", result)
        self.assertIn("security_data", result)
        self.assertEqual(result["health_data"]["health_score"], health_score)
        self.assertEqual(result["health_data"]["token"], token)
        self.assertEqual(result["security_data"]["security_score"], security_score)
        self.assertEqual(result["security_data"]["vulnerabilities"], vulnerabilities)
        self.assertEqual(result["security_data"]["token"], token)
        
        expected_file = os.path.join(target_dir, f"audit_{sync_id}.json")
        self.assertTrue(os.path.exists(expected_file))
        
        with open(expected_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            self.assertEqual(file_data["correlation_id"], sync_id)
            self.assertEqual(file_data["health_metrics"]["health_score"], health_score)
            self.assertEqual(file_data["security_metrics"]["security_score"], security_score)
            self.assertEqual(file_data["security_metrics"]["vulnerabilities"], vulnerabilities)
            
        if os.path.exists(expected_file):
            os.remove(expected_file)
        if os.path.exists(target_dir):
            os.rmdir(target_dir)

    def test_synchronize_with_payload_token_mismatch(self):
        repo_id = uuid.uuid4().hex
        syncer = RepoHealthSecuritySyncer(repo_id=repo_id)
        
        sync_id = uuid.uuid4().hex
        payload = {
            "sync_id": sync_id,
            "token": uuid.uuid4().hex
        }
        env_token = uuid.uuid4().hex
        
        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = syncer.synchronize(metric_payload=payload)
            
        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("synced_id"), sync_id)

    def test_synchronize_remote_health_fail(self):
        health_url = f"https://{self._random_string()}.net/{self._random_string()}"
        security_url = f"https://{self._random_string()}.net/{self._random_string()}"
        syncer = RepoHealthSecuritySyncer(health_url=health_url, security_url=security_url)
        
        err_code = random.choice([400, 401, 403, 404, 500, 502])
        err_text = self._random_string(15)
        
        mock_response = MagicMock()
        mock_response.status_code = err_code
        mock_response.text = err_text
        
        with patch("requests.get", return_value=mock_response) as mock_get:
            result = syncer.synchronize(metric_payload=None)
            mock_get.assert_called_once_with(health_url)
            
        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), err_code)
        self.assertEqual(result.get("error"), err_text)

    def test_synchronize_remote_security_fail(self):
        health_url = f"https://{self._random_string()}.com/{self._random_string()}"
        security_url = f"https://{self._random_string()}.com/{self._random_string()}"
        syncer = RepoHealthSecuritySyncer(health_url=health_url, security_url=security_url)
        
        health_data = {self._random_string(): random.randint(1, 100)}
        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_data
        
        err_code = random.choice([400, 403, 404, 500, 503])
        err_text = self._random_string(12)
        
        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = err_code
        mock_sec_resp.text = err_text
        
        with patch("requests.get", side_effect=[mock_health_resp, mock_sec_resp]) as mock_get:
            result = syncer.synchronize(metric_payload=None)
            self.assertEqual(mock_get.call_count, 2)
            
        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), err_code)
        self.assertEqual(result.get("error"), err_text)

    def test_synchronize_remote_success(self):
        health_url = f"https://{self._random_string()}.io/{self._random_string()}"
        security_url = f"https://{self._random_string()}.io/{self._random_string()}"
        syncer = RepoHealthSecuritySyncer(health_url=health_url, security_url=security_url)
        
        health_data = {self._random_string(): self._random_string()}
        security_data = {self._random_string(): random.randint(1, 50)}
        
        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_data
        
        mock_sec_resp = MagicMock()
        mock_sec_resp.status_code = 200
        mock_sec_resp.json.return_value = security_data
        
        with patch("requests.get", side_effect=[mock_health_resp, mock_sec_resp]) as mock_get:
            result = syncer.synchronize(metric_payload=None)
            
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("health_data"), health_data)
        self.assertEqual(result.get("security_data"), security_data)

    def test_synchronize_exception_handling(self):
        health_url = f"https://{self._random_string()}.xyz/{self._random_string()}"
        syncer = RepoHealthSecuritySyncer(health_url=health_url)
        
        err_message = self._random_string(20)
        
        with patch("requests.get", side_effect=Exception(err_message)) as mock_get:
            result = syncer.synchronize(metric_payload=None)
            
        self.assertFalse(result.get("success"))
        self.assertEqual(result.get("status_code"), 500)
        self.assertIn(err_message, result.get("error"))

    def test_export_audit_stream_with_raw(self):
        health_url = f"https://{self._random_string()}.edu/{self._random_string()}"
        syncer = RepoHealthSecuritySyncer(health_url=health_url)
        
        random_bytes = self._random_string(50).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        
        mock_raw = io.BytesIO(random_bytes)
        mock_resp = MagicMock()
        mock_resp.raw = mock_raw
        
        with patch("requests.get", return_value=mock_resp) as mock_get:
            res = syncer.export_audit_stream()
            mock_get.assert_called_once_with(health_url)
            
        self.assertEqual(res.get("stream_hash"), expected_hash)
        self.assertEqual(res.get("bytes_read"), len(random_bytes))

    def test_export_audit_stream_with_content(self):
        health_url = f"https://{self._random_string()}.gov/{self._random_string()}"
        syncer = RepoHealthSecuritySyncer(health_url=health_url)
        
        random_bytes = self._random_string(30).encode('utf-8')
        expected_hash = hashlib.sha256(random_bytes).hexdigest()
        
        mock_resp = MagicMock()
        mock_resp.raw = None
        mock_resp.content = random_bytes
        
        with patch("requests.get", return_value=mock_resp) as mock_get:
            res = syncer.export_audit_stream()
            mock_get.assert_called_once_with(health_url)
            
        self.assertEqual(res.get("stream_hash"), expected_hash)
        self.assertEqual(res.get("bytes_read"), len(random_bytes))