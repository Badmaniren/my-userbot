import unittest
from unittest.mock import patch
import os
import uuid
import random
import json
import io
import requests

from skills.repo_health_security_syncer import RepoHealthSecuritySyncer


class TestRepoHealthSecuritySyncer(unittest.TestCase):

    def test_synchronize_with_metric_payload_success(self):
        repo_id = uuid.uuid4().hex
        health_url = f"http://{uuid.uuid4().hex}.local/health"
        security_url = f"http://{uuid.uuid4().hex}.local/security"
        target_dir = f"temp_audit_{uuid.uuid4().hex}"

        syncer = RepoHealthSecuritySyncer(
            repo_id=repo_id,
            health_url=health_url,
            security_url=security_url,
            target_directory=target_dir
        )

        sync_id = uuid.uuid4().hex
        health_score = random.randint(1, 100)
        security_score = random.randint(1, 100)
        vulnerabilities = random.randint(0, 10)

        payload = {
            "sync_id": sync_id,
            "health_score": health_score,
            "security_score": security_score,
            "vulnerabilities": vulnerabilities
        }

        try:
            result = syncer.synchronize(metric_payload=payload)

            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("synced_id"), sync_id)
            self.assertEqual(result.get("health_data", {}).get("health_score"), health_score)
            self.assertEqual(result.get("security_data", {}).get("security_score"), security_score)
            self.assertEqual(result.get("security_data", {}).get("vulnerabilities"), vulnerabilities)

            expected_file = os.path.join(target_dir, f"audit_{sync_id}.json")
            self.assertTrue(os.path.exists(expected_file))

            with open(expected_file, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                self.assertEqual(saved_data.get("correlation_id"), sync_id)
                self.assertEqual(saved_data.get("health_metrics", {}).get("health_score"), health_score)
                self.assertEqual(saved_data.get("security_metrics", {}).get("security_score"), security_score)
                self.assertEqual(saved_data.get("security_metrics", {}).get("vulnerabilities"), vulnerabilities)
        finally:
            if os.path.exists(target_dir):
                for file in os.listdir(target_dir):
                    file_path = os.path.join(target_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                os.rmdir(target_dir)

    def test_synchronize_with_token_mismatch(self):
        repo_id = uuid.uuid4().hex
        syncer = RepoHealthSecuritySyncer(repo_id=repo_id)

        env_token = uuid.uuid4().hex
        wrong_token = uuid.uuid4().hex
        sync_id = uuid.uuid4().hex

        payload = {
            "sync_id": sync_id,
            "token": wrong_token,
            "health_score": random.randint(1, 100)
        }

        with patch.dict(os.environ, {"REPO_SYNC_TOKEN": env_token}):
            result = syncer.synchronize(metric_payload=payload)

            self.assertFalse(result.get("success"))
            self.assertEqual(result.get("synced_id"), sync_id)

    def test_synchronize_remote_fetch_success(self):
        repo_id = uuid.uuid4().hex
        health_url = f"http://{uuid.uuid4().hex}.local/health"
        security_url = f"http://{uuid.uuid4().hex}.local/security"

        syncer = RepoHealthSecuritySyncer(
            repo_id=repo_id,
            health_url=health_url,
            security_url=security_url
        )

        health_score = random.randint(1, 100)
        security_score = random.randint(1, 100)
        health_json = {"health_score": health_score}
        security_json = {"security_score": security_score}

        mock_health_resp = requests.Response()
        mock_health_resp.status_code = 200
        mock_health_resp.json = lambda: health_json

        mock_security_resp = requests.Response()
        mock_security_resp.status_code = 200
        mock_security_resp.json = lambda: security_json

        with patch("requests.get") as mock_get:
            mock_get.side_effect = [mock_health_resp, mock_security_resp]

            result = syncer.synchronize(metric_payload=None)

            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("health_data"), health_json)
            self.assertEqual(result.get("security_data"), security_json)

    def test_synchronize_remote_fetch_health_error(self):
        repo_id = uuid.uuid4().hex
        health_url = f"http://{uuid.uuid4().hex}.local/health"
        security_url = f"http://{uuid.uuid4().hex}.local/security"

        syncer = RepoHealthSecuritySyncer(
            repo_id=repo_id,
            health_url=health_url,
            security_url=security_url
        )

        error_status = random.choice([400, 401, 403, 404, 500, 503])
        error_text = uuid.uuid4().hex

        mock_health_resp = requests.Response()
        mock_health_resp.status_code = error_status
        mock_health_resp._content = error_text.encode('utf-8')

        with patch("requests.get", return_value=mock_health_resp) as mock_get:
            result = syncer.synchronize(metric_payload=None)

            self.assertFalse(result.get("success"))
            self.assertEqual(result.get("status_code"), error_status)
            self.assertIn(error_text, result.get("error", ""))

    def test_export_audit_stream(self):
        repo_id = uuid.uuid4().hex
        health_url = f"http://{uuid.uuid4().hex}.local/health"
        syncer = RepoHealthSecuritySyncer(repo_id=repo_id, health_url=health_url)

        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes

        mock_resp = requests.Response()
        mock_resp.status_code = 200
        mock_resp.raw = io.BytesIO(random_bytes)

        with patch("requests.get", return_value=mock_resp):
            export_result = syncer.export_audit_stream()

            self.assertIn("stream_hash", export_result)
            self.assertIn("bytes_read", export_result)
            self.assertEqual(export_result["bytes_read"], len(random_bytes))


if __name__ == "__main__":
    unittest.main()