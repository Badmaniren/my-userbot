import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import os
from skills.incident_audit_trail_collector import start_new, collect_incident_audit_trail

class TestIncidentAuditTrailCollector(unittest.TestCase):

    def test_start_new_basic_success(self):
        rand_token = uuid.uuid4().hex
        rand_status = random.choice([200, 201, 400, 500])
        res = start_new(audit_token=rand_token, status_code=rand_status)
        self.assertEqual(res, {"status": "SUCCESS"})

    @patch("skills.incident_audit_trail_collector.requests.get")
    def test_start_new_target_url(self, mock_get):
        rand_url = f"http://{uuid.uuid4().hex}.local/api"
        res = start_new(target_url=rand_url)
        mock_get.assert_called_once_with(rand_url)
        self.assertEqual(res, {"status": "SUCCESS"})

    @patch("skills.incident_audit_trail_collector.requests.post")
    def test_start_new_endpoint(self, mock_post):
        rand_endpoint = f"http://{uuid.uuid4().hex}.local/hook"
        rand_token = uuid.uuid4().hex
        rand_status = random.randint(100, 999)
        res = start_new(endpoint=rand_endpoint, audit_token=rand_token, status_code=rand_status)
        mock_post.assert_called_once_with(rand_endpoint, json={"token": rand_token, "status": rand_status})
        self.assertEqual(res, {"status": "SUCCESS"})

    def test_start_new_data_stream(self):
        rand_bytes = bytes(uuid.uuid4().hex, "utf-8")
        mock_stream = io.BytesIO(rand_bytes)
        res = start_new(data_stream=mock_stream)
        self.assertEqual(res, {"status": "SUCCESS"})

    def test_start_new_aggregator(self):
        rand_tokens = [uuid.uuid4().hex for _ in range(3)]
        mock_aggregator = MagicMock()
        res = start_new(aggregator=mock_aggregator, tokens=rand_tokens)
        mock_aggregator.aggregate.assert_called_once_with(rand_tokens)
        self.assertEqual(res, {"status": "SUCCESS"})

    def test_start_new_stream(self):
        mock_stream = io.BytesIO(b"chaos_stream_data")
        res = start_new(stream=mock_stream)
        self.assertEqual(res, {"status": "SUCCESS"})

    def test_collect_incident_audit_trail_success(self):
        rand_incident_id = uuid.uuid4().hex
        rand_severity = random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"])
        rand_telemetry_key = uuid.uuid4().hex
        rand_telemetry_val = uuid.uuid4().hex
        rand_file_path = f"/tmp/{uuid.uuid4().hex}/audit.log"

        incident_data = {
            "incident_id": rand_incident_id,
            "severity": rand_severity,
            "source_telemetry": {rand_telemetry_key: rand_telemetry_val}
        }

        try:
            result = collect_incident_audit_trail(incident_data, rand_file_path, include_raw_telemetry=True)
            self.assertEqual(result["status"], "SUCCESS")
            self.assertEqual(result["logged_incident_id"], rand_incident_id)

            self.assertTrue(os.path.exists(rand_file_path))
            with open(rand_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn(rand_incident_id, content)
            self.assertIn(rand_severity, content)
            self.assertIn(rand_telemetry_key, content)
            self.assertIn(rand_telemetry_val, content)
        finally:
            if os.path.exists(rand_file_path):
                os.remove(rand_file_path)
                try:
                    os.rmdir(os.path.dirname(rand_file_path))
                except OSError:
                    pass

    def test_collect_incident_audit_trail_without_telemetry(self):
        rand_incident_id = uuid.uuid4().hex
        rand_severity = random.choice(["CRITICAL", "WARNING"])
        rand_file_path = f"/tmp/{uuid.uuid4().hex}/sub/audit.log"

        incident_data = {
            "incident_id": rand_incident_id,
            "severity": rand_severity,
            "source_telemetry": {"hidden_data": uuid.uuid4().hex}
        }

        try:
            result = collect_incident_audit_trail(incident_data, rand_file_path, include_raw_telemetry=False)
            self.assertEqual(result["status"], "SUCCESS")
            self.assertEqual(result["logged_incident_id"], rand_incident_id)

            self.assertTrue(os.path.exists(rand_file_path))
            with open(rand_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn(rand_incident_id, content)
            self.assertIn(rand_severity, content)
            self.assertNotIn("hidden_data", content)
        finally:
            if os.path.exists(rand_file_path):
                os.remove(rand_file_path)
                try:
                    os.rmdir(os.path.dirname(rand_file_path))
                except OSError:
                    pass

if __name__ == "__main__":
    unittest.main()