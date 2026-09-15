import unittest
from unittest.mock import patch
import io
import uuid
import random
from skills.system_health_aggregator import SystemHealthAggregator


class TestSystemHealthAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.random_epic_id = str(uuid.uuid4())
        self.random_module = f"module_{uuid.uuid4().hex[:6]}"
        self.random_format = random.choice(["json", "html", "pdf", "txt"])
        self.random_exception = random.choice(["KeyError", "ValueError", "TypeError", "AttributeError"])
        self.random_incident_id = f"inc_{uuid.uuid4().hex[:8]}"
        self.random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

    def test_aggregate_system_health(self):
        expected_result = {
            "status": "success",
            "health_score": random.randint(50, 100),
            "token": uuid.uuid4().hex
        }

        with patch("skills.recovery_dashboard_generator.RecoveryDashboardGenerator.aggregate_system_health", return_value=expected_result) as mock_agg:
            result = self.aggregator.aggregate_system_health()
            mock_agg.assert_called_once()
            self.assertEqual(result, expected_result)

    def test_process_stream(self):
        random_bytes = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        stream_io = io.BytesIO(random_bytes)
        expected_parsed = {
            "parsed": True,
            "stream_hash": uuid.uuid4().hex,
            "size": len(random_bytes)
        }

        with patch("skills.recovery_dashboard_generator.RecoveryDashboardGenerator.parse_stream_data", return_value=expected_parsed) as mock_parse:
            result = self.aggregator.process_stream(stream_io)
            mock_parse.assert_called_once_with(stream_io)
            self.assertEqual(result, expected_parsed)

    def test_generate_report(self):
        expected_export_path = f"/var/reports/{self.random_epic_id}.{self.random_format}"

        with patch("skills.recovery_report_exporter.RecoveryReportExporter.finalize_and_export_summary", return_value=expected_export_path) as mock_export:
            result = self.aggregator.generate_report(self.random_epic_id, self.random_module, self.random_format)
            mock_export.assert_called_once_with(self.random_epic_id, self.random_module, self.random_format)
            self.assertEqual(result, expected_export_path)

    def test_trigger_recovery(self):
        expected_recovery_result = {
            "recovered": True,
            "incident_id": self.random_incident_id,
            "module": self.random_module,
            "patch_applied": uuid.uuid4().hex
        }

        with patch("skills.error_recovery_hub.ErrorRecoveryHub.analyze_and_recover", return_value=expected_recovery_result) as mock_recover:
            result = self.aggregator.trigger_recovery(self.random_module, self.random_exception, self.random_incident_id)
            mock_recover.assert_called_once_with(self.random_module, self.random_exception, self.random_incident_id)
            self.assertEqual(result, expected_recovery_result)

    def test_notify_incident(self):
        expected_dispatch_status = True

        with patch("skills.notification_channel_dispatcher.NotificationChannelDispatcher.dispatch", return_value=expected_dispatch_status) as mock_dispatch:
            result = self.aggregator.notify_incident(self.random_severity, self.random_incident_id)
            expected_payload = {"incident_id": self.random_incident_id, "severity": self.random_severity}
            mock_dispatch.assert_called_once_with(self.random_severity, expected_payload)
            self.assertEqual(result, expected_dispatch_status)


if __name__ == "__main__":
    unittest.main()