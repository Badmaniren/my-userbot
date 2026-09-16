import unittest
import os
import uuid
import random
import tempfile
from skills.incident_post_mortem_generator import (
    IncidentPostMortemGenerator,
    generate_incident_post_mortem
)
from skills.incident_aggregator import aggregate_incidents
from skills.error_recovery_hub import process_error_recovery
from skills.incident_severity_evaluator import evaluate_incident_severity


class TestIncidentPostMortemGeneratorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.incident_id = str(uuid.uuid4())
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        self.log_file = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8")
        self.log_file.write(f"ERROR: Test failure log entry for incident {self.incident_id}")
        self.log_file.close()

    def tearDown(self):
        self.test_dir.cleanup()
        if os.path.exists(self.log_file.name):
            os.unlink(self.log_file.name)

    def test_integration_post_mortem_workflow(self):
        aggregated_data = aggregate_incidents([self.incident_id])
        recovery_result = process_error_recovery({"error_code": random.randint(500, 599)})
        severity_result = evaluate_incident_severity({"metric": random.random()})

        post_mortem_input = {
            "incident": {
                "id": self.incident_id,
                "data": aggregated_data
            },
            "severity": {
                "severity": self.severity_level,
                "eval": severity_result
            },
            "recovery": {
                "status": "FAILED",
                "timestamp_start": random.randint(1000, 2000),
                "timestamp_end": random.randint(2001, 3000),
                "details": recovery_result
            },
            "output_dir": self.test_dir.name
        }

        report_data = generate_incident_post_mortem(post_mortem_input)

        self.assertEqual(report_data["incident_id"], self.incident_id)
        self.assertEqual(report_data["severity"], self.severity_level)
        self.assertIn("report_id", report_data)
        self.assertIn("summary", report_data)

        generator = IncidentPostMortemGenerator()
        escalations = [{"step": random.randint(1, 5)}]
        recoveries = [{"status": "FAILED", "timestamp_start": 100, "timestamp_end": 200}]

        summary = generator.generate_post_mortem_summary(
            incident_id=self.incident_id,
            severity=self.severity_level,
            escalations=escalations,
            recoveries=recoveries,
            log_file_path=self.log_file.name
        )

        self.assertEqual(summary["incident_id"], self.incident_id)
        self.assertEqual(summary["escalation_steps_count"], len(escalations))
        self.assertEqual(summary["recovery_actions_count"], len(recoveries))
        self.assertEqual(summary["root_cause_analysis"], "ANALYZED_OK")

        target_export_path = os.path.join(self.test_dir.name, f"export_{uuid.uuid4().hex}.json")
        export_result = generator.export_report(summary, target_export_path, format="json")

        self.assertTrue(export_result)
        self.assertTrue(os.path.exists(target_export_path))

        timeline = generator._analyze_recovery_timeline(recoveries)
        self.assertEqual(timeline["events_analyzed"], 1)
        self.assertEqual(timeline["total_duration"], 100)
        self.assertEqual(timeline["failure_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()