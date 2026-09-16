import unittest
import uuid
import random
import os
from skills.incident_post_mortem_service import IncidentPostMortemService
from skills.incident_aggregator import IncidentAggregator
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.recovery_report_exporter import RecoveryReportExporter

class TestIncidentPostMortemServiceIntegration(unittest.TestCase):
    def setUp(self):
        self.post_mortem_service = IncidentPostMortemService()
        self.incident_aggregator = IncidentAggregator()
        self.error_recovery_hub = ErrorRecoveryHub()
        self.report_exporter = RecoveryReportExporter()

    def test_end_to_end_post_mortem_generation(self):
        unique_incident_id = str(uuid.uuid4())
        random_error_code = f"ERR_{random.randint(1000, 9999)}"
        random_recovery_duration = random.randint(15, 300)

        raw_incident_data = {
            "incident_id": unique_incident_id,
            "error_code": random_error_code,
            "severity": random.choice(["CRITICAL", "HIGH", "MEDIUM"]),
            "metrics": {
                "cpu_load_spike": random.uniform(85.0, 99.9),
                "memory_leak_mb": random.randint(512, 4096)
            }
        }

        aggregated_incident = self.incident_aggregator.aggregate(raw_incident_data)
        self.assertIsNotNone(aggregated_incident)

        recovery_logs = self.error_recovery_hub.execute_recovery_sequence(
            incident_id=unique_incident_id,
            error_code=random_error_code,
            duration=random_recovery_duration
        )
        self.assertTrue(recovery_logs.get("success", False))

        post_mortem_report = self.post_mortem_service.generate_report(
            incident=aggregated_incident,
            recovery_data=recovery_logs
        )

        self.assertIn("report_id", post_mortem_report)
        self.assertEqual(post_mortem_report["incident_id"], unique_incident_id)
        self.assertIn("timeline", post_mortem_report)
        self.assertIn("root_cause_analysis", post_mortem_report)

        export_path = f"/tmp/post_mortem_{unique_incident_id}.json"
        export_result = self.report_exporter.export(
            report=post_mortem_report,
            destination_path=export_path
        )

        self.assertTrue(export_result.get("success", False))
        self.assertTrue(os.path.exists(export_path))

        with open(export_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(unique_incident_id, file_content)
            self.assertIn(random_error_code, file_content)

        if os.path.exists(export_path):
            os.remove(export_path)

if __name__ == "__main__":
    unittest.main()