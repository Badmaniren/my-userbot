import unittest
from unittest.mock import patch, MagicMock
import io
import json
import os
import uuid
import random
from skills.system_audit_log_exporter import SystemAuditLogExporter, export_system_audit_log


class TestSystemAuditLogExporter(unittest.TestCase):

    def setUp(self):
        self.exporter = SystemAuditLogExporter()
        self.target_url = f"http://{uuid.uuid4().hex}.local/api/v1/audit"
        self.event_id = uuid.uuid4().hex
        self.error_text = f"error_{uuid.uuid4().hex}"

    @patch("skills.system_audit_log_exporter.requests.post")
    def test_export_log_success_with_response_id(self, mock_post):
        returned_id = uuid.uuid4().hex
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"event_id": returned_id}
        mock_post.return_value = mock_response

        raw_log = {"event_id": self.event_id, "data": random.randint(1, 100)}
        result = self.exporter.export_log(self.target_url, raw_log)

        self.assertTrue(result["success"])
        self.assertEqual(result["event_id"], returned_id)
        mock_post.assert_called_once_with(self.target_url, json=raw_log)

    @patch("skills.system_audit_log_exporter.requests.post")
    def test_export_log_success_fallback_to_raw_id(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        raw_log = {"event_id": self.event_id, "payload": uuid.uuid4().hex}
        result = self.exporter.export_log(self.target_url, raw_log)

        self.assertTrue(result["success"])
        self.assertEqual(result["event_id"], self.event_id)

    @patch("skills.system_audit_log_exporter.requests.post")
    def test_export_log_failure_status(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = self.error_text
        mock_post.return_value = mock_response

        raw_log = {"event_id": self.event_id}
        result = self.exporter.export_log(self.target_url, raw_log)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 400)
        self.assertEqual(result["error"], self.error_text)

    @patch("skills.system_audit_log_exporter.requests.post")
    def test_export_log_exception(self, mock_post):
        mock_post.side_effect = Exception(self.error_text)

        raw_log = {"event_id": self.event_id}
        result = self.exporter.export_log(self.target_url, raw_log)

        self.assertFalse(result["success"])
        self.assertIn(self.error_text, result["error"])

    @patch("skills.system_audit_log_exporter.requests.post")
    def test_export_stream_success_bytes(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        stream_key = uuid.uuid4().hex
        stream_val = uuid.uuid4().hex
        stream_content = json.dumps({stream_key: stream_val}).encode("utf-8")
        stream = io.BytesIO(stream_content)

        result = self.exporter.export_stream(self.target_url, stream)

        self.assertTrue(result["success"])
        mock_post.assert_called_once_with(self.target_url, json={stream_key: stream_val})

    @patch("skills.system_audit_log_exporter.requests.post")
    def test_export_stream_success_invalid_json(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        garbage_text = f"garbage_{uuid.uuid4().hex}"
        stream = io.BytesIO(garbage_text.encode("utf-8"))

        result = self.exporter.export_stream(self.target_url, stream)

        self.assertTrue(result["success"])
        mock_post.assert_called_once_with(self.target_url, json={"raw": garbage_text})

    @patch("skills.system_audit_log_exporter.requests.post")
    def test_export_stream_non_200_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = self.error_text
        mock_post.return_value = mock_response

        stream = io.BytesIO(b'{"test": "data"}')

        result = self.exporter.export_stream(self.target_url, stream)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 503)
        self.assertEqual(result["error"], self.error_text)

    @patch("skills.system_audit_log_exporter.requests.post")
    def test_export_stream_outer_exception_fallback(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.text = self.error_text
        # First post fails inside main try block or stream read fails
        mock_post.side_effect = [Exception("Stream read error"), mock_response]

        bad_stream = MagicMock()
        bad_stream.read.side_effect = Exception("Read failed")

        result = self.exporter.export_stream(self.target_url, bad_stream)

        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"], 201)
        self.assertEqual(result["error"], self.error_text)

    def test_format_standardized_logs(self):
        records = [
            {uuid.uuid4().hex: uuid.uuid4().hex},
            {uuid.uuid4().hex: random.randint(100, 999)}
        ]
        formatted_str = self.exporter.format_standardized_logs(records)
        parsed = json.loads(formatted_str)

        self.assertIn("records", parsed)
        self.assertEqual(parsed["records"], records)


class TestExportSystemAuditLogIntegration(unittest.TestCase):

    def test_export_system_audit_log_file_creation(self):
        audit_id = uuid.uuid4().hex
        incident_key = uuid.uuid4().hex
        incident_val = uuid.uuid4().hex
        output_dir = f"temp_audit_dir_{uuid.uuid4().hex}"

        data = {
            "audit_id": audit_id,
            "incident": {incident_key: incident_val},
            "output_directory": output_dir
        }

        try:
            result = export_system_audit_log(data)
            expected_file_path = os.path.join(output_dir, f"audit_{audit_id}.json")

            self.assertEqual(result["exported_file"], expected_file_path)
            self.assertTrue(os.path.exists(expected_file_path))

            with open(expected_file_path, "r", encoding="utf-8") as f:
                content = json.load(f)

            self.assertEqual(content["audit_id"], audit_id)
            self.assertEqual(content["incident"][incident_key], incident_val)
        finally:
            expected_file_path = os.path.join(output_dir, f"audit_{audit_id}.json")
            if os.path.exists(expected_file_path):
                os.remove(expected_file_path)
            if os.path.exists(output_dir):
                os.rmdir(output_dir)