import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import os

from skills.repo_health_security_syncer import RepoHealthSecuritySyncer


class TestRepoHealthSecuritySyncer(unittest.TestCase):

    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.health_endpoint = f"https://{uuid.uuid4().hex}.internal/health"
        self.security_endpoint = f"https://{uuid.uuid4().hex}.internal/security"
        self.syncer = RepoHealthSecuritySyncer(
            repo_id=self.repo_id,
            health_url=self.health_endpoint,
            security_url=self.security_endpoint
        )

    def test_initialization_parameters(self):
        rand_repo = uuid.uuid4().hex
        rand_health = f"https://{uuid.uuid4().hex}.org/api/v1/health"
        rand_sec = f"https://{uuid.uuid4().hex}.org/api/v1/security"
        
        syncer = RepoHealthSecuritySyncer(
            repo_id=rand_repo,
            health_url=rand_health,
            security_url=rand_sec
        )
        
        self.assertEqual(syncer.repo_id, rand_repo)
        self.assertEqual(syncer.health_url, rand_health)
        self.assertEqual(syncer.security_url, rand_sec)

    def test_sync_metrics_success_flow(self):
        health_score = round(random.uniform(50.0, 100.0), 2)
        security_score = round(random.uniform(50.0, 100.0), 2)
        sync_token = uuid.uuid4().hex

        health_response_payload = {
            "repo_id": self.repo_id,
            "health_score": health_score,
            "status": "stable"
        }
        security_response_payload = {
            "repo_id": self.repo_id,
            "security_score": security_score,
            "token": sync_token,
            "vulnerabilities": []
        }

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_response_payload

        mock_security_resp = MagicMock()
        mock_security_resp.status_code = 200
        mock_security_resp.json.return_value = security_response_payload

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
            
            result = self.syncer.synchronize()

            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("health_data")["health_score"], health_score)
            self.assertEqual(result.get("security_data")["security_score"], security_score)
            self.assertEqual(result.get("security_data")["token"], sync_token)
            
            self.assertEqual(mock_get.call_count, 2)
            mock_get.assert_any_call(self.health_endpoint, timeout=unittest.mock.ANY)
            mock_get.assert_any_call(self.security_endpoint, timeout=unittest.mock.ANY)

    def test_sync_metrics_health_failure(self):
        error_code = random.choice([400, 401, 403, 404, 500, 503])
        error_msg = ''.join(random.choices(string.ascii_letters, k=15))

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = error_code
        mock_health_resp.text = error_msg

        with patch("requests.get") as mock_get:
            mock_get.return_value = mock_health_resp
            
            result = self.syncer.synchronize()

            self.assertFalse(result.get("success"))
            self.assertIn("health", result.get("error").lower())
            self.assertEqual(result.get("status_code"), error_code)

    def test_sync_metrics_security_failure(self):
        health_score = round(random.uniform(0.0, 100.0), 2)
        health_response_payload = {
            "repo_id": self.repo_id,
            "health_score": health_score
        }

        mock_health_resp = MagicMock()
        mock_health_resp.status_code = 200
        mock_health_resp.json.return_value = health_response_payload

        error_code = random.choice([500, 502, 504])
        mock_security_resp = MagicMock()
        mock_security_resp.status_code = error_code
        mock_security_resp.text = uuid.uuid4().hex

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]
            
            result = self.syncer.synchronize()

            self.assertFalse(result.get("success"))
            self.assertIn("security", result.get("error").lower())
            self.assertEqual(result.get("status_code"), error_code)

    def test_payload_export_stream(self):
        random_bytes = uuid.uuid4().bytes + ''.join(random.choices(string.printable, k=50)).encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.raw = mock_stream
            mock_get.return_value = mock_resp

            exported_data = self.syncer.export_audit_stream()
            
            self.assertIn("stream_hash", exported_data)
            self.assertTrue(exported_data["bytes_read"] > 0)


if __name__ == "__main__":
    unittest.main()