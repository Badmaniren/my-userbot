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
        self.random_timeout = random.randint(1, 100)
        self.random_log_message = f"error occurred at {uuid.uuid4()}"

    def test_integration_flow_with_real_dependencies(self):
        self.assertIsInstance(self.service.incident_aggregator, IncidentAggregator)
        self.assertIsInstance(self.service.error_recovery_hub, ErrorRecoveryHub)
        self.assertIsInstance(self.service.report_exporter, RecoveryReportExporter)

        incident_payload = {
            "incident_id": self.random_incident_id,
            "metrics": {
                "timeout_count": self.random_timeout,
                "memory_leak_detected": True
            },
            "error_code": f"ERR_{random.randint(1000, 9999)}"
        }

        recovery_payload = {
            "logs": self.random_log_message.encode('utf-8')
        }

        report = self.service.generate_report(incident_payload, recovery_payload)

        self.assertIn("report_id", report)
        self.assertEqual(report["incident_id"], self.random_incident_id)
        self.assertIn("Memory leak detected", report["root_cause_analysis"])
        self.assertIn(str(self.random_timeout), report["root_cause_analysis"])
        self.assertIn(self.random_log_message, report["recovery_logs_summary"])
        self.assertEqual(report["metrics_snapshot"]["timeout_count"], self.random_timeout)

    def test_integration_with_string_incident_id(self):
        report = self.service.generate_report(self.random_incident_id)
        
        self.assertEqual(report["incident_id"], self.random_incident_id)
        self.assertIn("metrics_snapshot", report)
        self.assertIn("root_cause", report)

if __name__ == "__main__":
    unittest.main()