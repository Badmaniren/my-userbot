import unittest
import uuid
import random
from skills.incident_post_mortem_service import IncidentPostMortemService
from skills.incident_aggregator import IncidentAggregator
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.recovery_report_exporter import RecoveryReportExporter


class TestIncidentPostMortemServiceIntegration(unittest.TestCase):
    def setUp(self):
        self.service = IncidentPostMortemService()
        self.random_incident_id = f"inc-{uuid.uuid4()}"
        self.random_error_code = f"ERR-{random.randint(1000, 9999)}"
        self.random_timeout = random.randint(1, 10)
        self.random_log_message = f"Recovery sequence initiated for anomaly {uuid.uuid4()}"

    def test_generate_report_with_dictionary_payload_integration(self):
        payload = {
            "incident_id": self.random_incident_id,
            "error_code": self.random_error_code,
            "metrics": {
                "memory_leak_detected": True,
                "timeout_count": self.random_timeout
            }
        }
        
        recovery_payload = {
            "logs": self.random_log_message.encode('utf-8')
        }

        report = self.service.generate_report(incident=payload, recovery_data=recovery_payload)

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("incident_id"), self.random_incident_id)
        self.assertIn("report_id", report)
        self.assertIn(self.random_error_code, report.get("root_cause_analysis", ""))
        self.assertIn(str(self.random_timeout), report.get("root_cause_analysis", ""))
        self.assertIn(self.random_log_message, report.get("recovery_logs_summary", ""))
        self.assertEqual(report.get("metrics_snapshot"), payload["metrics"])

    def test_generate_report_with_string_id_integration(self):
        report = self.service.generate_report(incident=self.random_incident_id)

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("incident_id"), self.random_incident_id)
        self.assertIn("root_cause", report)
        self.assertIn("metrics_snapshot", report)
        self.assertIn("recovery_logs_summary", report)
        self.assertIsInstance(report.get("metrics_snapshot"), dict)


if __name__ == "__main__":
    unittest.main()