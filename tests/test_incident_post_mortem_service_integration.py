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
        self.random_error_code = f"ERR_{random.randint(1000, 9999)}"
        self.random_timeout = random.randint(1, 100)
        self.random_log_message = f"Recovery sequence initiated for error {self.random_error_code}"

    def test_full_integration_pipeline_with_real_dependencies(self):
        incident_payload = {
            "incident_id": self.random_incident_id,
            "error_code": self.random_error_code,
            "metrics": {
                "timeout_count": self.random_timeout,
                "memory_leak_detected": True
            }
        }
        
        recovery_payload = {
            "logs": f"[INFO] {self.random_log_message}\n[WARN] High memory consumption observed."
        }

        report = self.service.generate_report(incident_payload, recovery_payload)

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("incident_id"), self.random_incident_id)
        self.assertIn("report_id", report)
        
        root_cause = report.get("root_cause_analysis", "")
        self.assertIn(self.random_error_code, root_cause)
        self.assertIn(str(self.random_timeout), root_cause)
        self.assertIn("Memory leak detected", root_cause)
        self.assertIn(self.random_log_message, root_cause)

        metrics_snapshot = report.get("metrics_snapshot", {})
        self.assertEqual(metrics_snapshot.get("timeout_count"), self.random_timeout)
        self.assertTrue(metrics_snapshot.get("memory_leak_detected"))

    def test_batch_import_and_summary_analytics_integration(self):
        batch_size = random.randint(2, 5)
        data_batch = []
        
        generated_ids = set()
        for _ in range(batch_size):
            inc_id = str(uuid.uuid4())
            generated_ids.add(inc_id)
            data_batch.append({
                "incident_id": inc_id,
                "error_code": f"CODE_{random.randint(100, 999)}",
                "metrics": {
                    "timeout_count": random.randint(0, 5)
                }
            })

        imported_reports = self.service.import_historical_data(data_batch)
        self.assertEqual(len(imported_reports), batch_size)
        
        for rep in imported_reports:
            self.assertIn(rep.get("incident_id"), generated_ids)
            self.assertIn("root_cause_analysis", rep)

        summary = self.service.export_summary_analytics(data_batch)
        self.assertEqual(summary.get("total_incidents"), batch_size)
        self.assertEqual(len(summary.get("reports_summary")), batch_size)


if __name__ == "__main__":
    unittest.main()