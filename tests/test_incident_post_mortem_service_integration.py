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
        self.random_incident_id = str(uuid.uuid4())
        self.random_error_code = f"ERR-{random.randint(1000, 9999)}"
        self.random_timeout = random.randint(1, 100)
        self.random_memory_mb = random.randint(256, 4096)
        self.random_log_message = f"Critical failure node {random.randint(1, 500)} failed to respond."

    def test_generate_report_with_dictionary_input_integration(self):
        incident_payload = {
            "incident_id": self.random_incident_id,
            "error_code": self.random_error_code,
            "metrics": {
                "memory_leak_detected": True,
                "memory_leak_mb": self.random_memory_mb,
                "timeout_count": self.random_timeout
            }
        }
        
        recovery_payload = {
            "logs": f"{self.random_log_message}\nRecovery routine executed successfully."
        }

        report = self.service.generate_report(incident=incident_payload, recovery_data=recovery_payload)

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("incident_id"), self.random_incident_id)
        self.assertIn("report_id", report)
        self.assertIn(self.random_error_code, report.get("root_cause_analysis", ""))
        self.assertIn(self.random_log_message, report.get("recovery_logs_summary", ""))
        self.assertEqual(report.get("metrics_snapshot", {}).get("memory_leak_mb"), self.random_memory_mb)

    def service_integration_with_real_components(self):
        incident_id = str(uuid.uuid4())
        
        if hasattr(self.service.incident_aggregator, "aggregate"):
            self.service.incident_aggregator.aggregate = lambda i_id: {
                "incident_id": i_id,
                "timeout_count": random.randint(5, 15)
            }
            
        if hasattr(self.service.error_recovery_hub, "get_logs"):
            self.service.error_recovery_hub.get_logs = lambda i_id: f"Error trace for {i_id}\nConnection reset by peer".encode('utf-8')

        report = self.service.generate_report(incident=incident_id)

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("incident_id"), incident_id)
        self.assertIn("Connection reset", report.get("recovery_logs_summary", ""))

    def test_import_historical_data_and_export_summary(self):
        batch_size = random.randint(2, 5)
        batch_data = []
        
        for _ in range(batch_size):
            batch_data.append({
                "incident_id": str(uuid.uuid4()),
                "error_code": f"CODE-{random.randint(100, 999)}",
                "metrics": {
                    "timeout_count": random.randint(0, 5)
                }
            })

        imported_reports = self.service.import_historical_data(batch_data)
        self.assertEqual(len(imported_reports), batch_size)

        summary = self.service.export_summary_analytics(batch_data)
        self.assertEqual(summary.get("total_incidents"), batch_size)
        self.assertEqual(len(summary.get("reports_summary")), batch_size)


if __name__ == "__main__":
    unittest.main()