import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json
from skills.system_audit_log_exporter import SystemAuditLogExporter


class TestSystemAuditLogExporter(unittest.TestCase):

    def setUp(self):
        self.exporter = SystemAuditLogExporter()

    def test_export_audit_log_success(self):
        event_id = uuid.uuid4().hex
        source_system = "".join(random.choices(string.ascii_lowercase, k=10))
        severity = random.choice(["INFO", "WARNING", "CRITICAL", "FATAL"])
        payload_data = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        
        raw_log_entry = {
            "event_id": event_id,
            "source": source_system,
            "severity": severity,
            "payload": payload_data
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "accepted", "event_id": event_id}

        target_url = f"https://{uuid.uuid4().hex}.monitoring-system.internal/api/v1/logs"

        with patch("requests.post") as mock_post:
            mock_post.return_value = mock_response
            
            result = self.exporter.export_log(target_url, raw_log_entry)
            
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], target_url)
            
            sent_data = kwargs.get("json", {})
            self.assertEqual(sent_data.get("event_id"), event_id)
            self.assertEqual(sent_data.get("source"), source_system)
            self.assertEqual(sent_data.get("severity"), severity)
            self.assertEqual(sent_data.get("payload"), payload_data)
            
            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("event_id"), event_id)

    def test_export_audit_log_stream_failure(self):
        error_code = random.randint(500, 599)
        error_message = "".join(random.choices(string.ascii_letters, k=20))
        
        log_stream = io.BytesIO(json.dumps({
            "error_code": error_code,
            "message": error_message,
            "uuid": uuid.uuid4().hex
        }).encode("utf-8"))

        target_url = f"https://{uuid.uuid4().hex}.audit-receiver.net/ingest"

        mock_response = MagicMock()
        mock_response.status_code = error_code
        mock_response.text = error_message

        with patch("requests.post") as mock_post:
            mock_post.return_value = mock_response

            result = self.exporter.export_stream(target_url, log_stream)

            mock_post.assert_called_once()
            self.assertFalse(result.get("success"))
            self.assertEqual(result.get("status_code"), error_code)
            self.assertIn(error_message, result.get("error"))

    def test_format_compliance_check(self):
        random_signature = uuid.uuid4().hex
        audit_records = [
            {
                "timestamp": random.randint(1600000000, 1700000000),
                "signature": random_signature,
                "action": "".join(random.choices(string.ascii_uppercase, k=8))
            }
        ]

        formatted_output = self.exporter.format_standardized_logs(audit_records)

        self.assertIsInstance(formatted_output, str)
        parsed_output = json.loads(formatted_output)
        
        self.assertIn("records", parsed_output)
        self.assertEqual(len(parsed_output["records"]), 1)
        self.assertEqual(parsed_output["records"][0]["signature"], random_signature)


if __name__ == "__main__":
    unittest.main()