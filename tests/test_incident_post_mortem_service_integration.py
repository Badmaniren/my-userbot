import unittest
import uuid
import random
from skills.incident_post_mortem_service import IncidentPostMortemService


class TestIncidentPostMortemServiceIntegration(unittest.TestCase):

    def setUp(self):
        self.service = IncidentPostMortemService()
        self.random_incident_id = f"inc-{uuid.uuid4()}"
        self.random_error_code = f"ERR-{random.randint(1000, 9999)}"
        self.random_timeout = random.randint(1, 50)

    def test_generate_report_integration_with_real_dependencies(self):
        incident_payload = {
            "incident_id": self.random_incident_id,
            "error_code": self.random_error_code,
            "metrics": {
                "timeout_count": self.random_timeout,
                "memory_leak_detected": True
            }
        }
        
        recovery_payload = {
            "logs": f"CRITICAL: Service degraded\nTimeout reached at limit {self.random_timeout}\nMemory usage spike"
        }

        report = self.service.generate_report(incident_payload, recovery_payload)

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("incident_id"), self.random_incident_id)
        self.assertIn("root_cause_analysis", report)
        
        root_cause = report["root_cause_analysis"]
        self.assertIn(self.random_error_code, root_cause)
        self.assertIn(str(self.random_timeout), root_cause)
        self.assertIn("Memory leak detected", root_cause)
        
        self.assertIn("metrics_snapshot", report)
        self.assertEqual(report["metrics_snapshot"]["timeout_count"], self.random_timeout)
        self.assertIn("recovery_logs_summary", report)

    def test_import_historical_data_integration(self):
        batch_size = random.randint(2, 4)
        data_batch = []
        
        generated_ids = set()
        for _ in range(batch_size):
            inc_id = f"hist-{uuid.uuid4()}"
            generated_ids.add(inc_id)
            data_batch.append({
                "incident_id": inc_id,
                "metrics": {"memory_leak_mb": random.randint(100, 1024)}
            })

        imported_reports = self.service.import_historical_data(data_batch)

        self.assertIsInstance(imported_reports, list)
        self.assertEqual(len(imported_reports), batch_size)
        
        for report in imported_reports:
            self.assertIn("incident_id", report)
            self.assertIn(report["incident_id"], generated_ids)
            self.assertIn("Memory leak detected", report.get("root_cause", report.get("root_cause_analysis", "")))

    def test_export_summary_analytics_integration(self):
        incidents_list = [
            f"string-inc-{uuid.uuid4()}",
            {
                "incident_id": f"dict-inc-{uuid.uuid4()}",
                "metrics": {"timeout_count": random.randint(1, 10)}
            }
        ]

        summary = self.service.export_summary_analytics(incidents_list)

        self.assertIsInstance(summary, dict)
        self.assertEqual(summary.get("total_incidents"), len(incidents_list))
        self.assertIn("reports_summary", summary)
        self.assertEqual(len(summary["reports_summary"]), len(incidents_list))


if __name__ == "__main__":
    unittest.main()