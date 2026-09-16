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
        self.rand_uuid = str(uuid.uuid4())
        self.timeout_val = random.randint(1, 10)
        self.memory_mb = random.randint(100, 2048)

    def test_generate_report_with_dict_and_real_dependencies(self):
        incident_data = {
            "incident_id": self.rand_uuid,
            "metrics": {
                "memory_leak_mb": self.memory_mb,
                "timeout_count": self.timeout_val
            },
            "error_code": f"ERR_{random.randint(500, 599)}"
        }
        recovery_payload = {
            "logs": f"CRITICAL: Out of memory at step {random.randint(1, 5)}\nINFO: Recovery initiated."
        }

        report = self.service.generate_report(incident_data, recovery_payload)

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("incident_id"), self.rand_uuid)
        self.assertIn("report_id", report)
        self.assertIn(str(self.memory_mb), str(report.get("metrics_snapshot")))
        self.assertIn(str(self.timeout_val), report.get("root_cause_analysis"))
        self.assertIn("Error code:", report.get("root_cause_analysis"))

    def test_generate_report_with_string_id_real_flow(self):
        incident_id = f"inc-{uuid.uuid4()}"
        
        report = self.service.generate_report(incident_id)

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("incident_id"), incident_id)
        self.assertIn("metrics_snapshot", report)
        self.assertIn("recovery_logs_summary", report)
        self.assertIn("root_cause", report)

if __name__ == "__main__":
    unittest.main()