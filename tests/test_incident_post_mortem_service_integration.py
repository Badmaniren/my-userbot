import unittest
import uuid
import random
import io
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
        self.random_log_message = f"Error recovery initiated at {uuid.uuid4()} with status failed"

    def test_generate_report_with_dict_input_integration(self):
        incident_data = {
            "incident_id": self.random_incident_id,
            "error_code": self.random_error_code,
            "metrics": {
                "timeout_count": self.random_timeout,
                "memory_leak_detected": True
            }
        }
        
        recovery_payload = {
            "logs": f"{self.random_log_message}\nRecovery action applied successfully."
        }

        report = self.service.generate_report(incident=incident_data, recovery_data=recovery_payload)

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("incident_id"), self.random_incident_id)
        self.assertIn("report_id", report)
        self.assertIn(self.random_error_code, report.get("root_cause_analysis", ""))
        self.assertIn(self.random_log_message, report.get("recovery_logs_summary", ""))
        self.assertEqual(report["metrics_snapshot"]["timeout_count"], self.random_timeout)

    def test_generate_report_with_string_id_integration(self):
        report = self.service.generate_report(incident=self.random_incident_id)

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("incident_id"), self.random_incident_id)
        self.assertIn("root_cause", report)
        self.assertIn("metrics_snapshot", report)
        self.assertIn("recovery_logs_summary", report)

    def subtest_real_collaborators_wiring(self):
        self.assertIsInstance(self.service.incident_aggregator, IncidentAggregator)
        self.assertIsInstance(self.service.error_recovery_hub, ErrorRecoveryHub)
        self.assertIsInstance(self.service.report_exporter, RecoveryReportExporter)

if __name__ == "__main__":
    unittest.main()