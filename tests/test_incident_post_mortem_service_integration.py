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
        self.incident_id = str(uuid.uuid4())
        self.random_timeout = random.randint(1, 100)
        self.random_memory = random.randint(128, 4096)
        self.error_code = f"ERR-{random.randint(1000, 9999)}"

    def test_generate_report_with_dictionary_input(self):
        incident_data = {
            "incident_id": self.incident_id,
            "error_code": self.error_code,
            "metrics": {
                "timeout_count": self.random_timeout,
                "memory_leak_mb": self.random_memory
            }
        }
        
        recovery_data = {
            "logs": f"System unstable. High memory usage detected: {self.random_memory}MB. Timeouts: {self.random_timeout}."
        }

        report = self.service.generate_report(incident_data, recovery_data)

        self.assertIsInstance(report, dict)
        self.assertEqual(report["incident_id"], self.incident_id)
        self.assertIn("report_id", report)
        self.assertIn(self.error_code, report["root_cause_analysis"])
        self.assertIn(str(self.random_timeout), report["root_cause_analysis"])
        self.assertIn(str(self.random_memory), report["root_cause_analysis"])
        self.assertEqual(report["metrics_snapshot"]["timeout_count"], self.random_timeout)
        self.assertEqual(report["metrics_snapshot"]["memory_leak_mb"], self.random_memory)
        self.assertTrue(len(report["timeline"]) > 0)

    def test_generate_report_with_string_identifier_integration(self):
        if hasattr(self.service.incident_aggregator, "aggregate"):
            self.service.incident_aggregator.aggregate = lambda i_id: {
                "incident_id": i_id,
                "timeout_count": self.random_timeout,
                "memory_leak_detected": True
            }
        
        if hasattr(self.service.error_recovery_hub, "get_logs"):
            self.service.error_recovery_hub.get_logs = lambda i_id: f"Critical failure for {i_id}. Memory leak detected."

        exported_reports = []
        if hasattr(self.service.report_exporter, "export"):
            self.service.report_exporter.export = lambda rep: exported_reports.append(rep)

        report = self.service.generate_report(self.incident_id)

        self.assertIsInstance(report, dict)
        self.assertEqual(report["incident_id"], self.incident_id)
        self.assertIn("Root cause identified", report["root_cause"])
        self.assertIn(str(self.random_timeout), report["root_cause"])
        self.assertEqual(report["metrics_snapshot"]["timeout_count"], self.random_timeout)
        self.assertTrue(report["metrics_snapshot"]["memory_leak_detected"])
        
        self.assertEqual(len(exported_reports), 1)
        self.assertEqual(exported_reports[0]["incident_id"], self.incident_id)


if __name__ == "__main__":
    unittest.main()