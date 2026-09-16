import unittest
from unittest.mock import patch
import uuid
import os
import io
import random
from skills.incident_post_mortem_generator import (
    IncidentPostMortemGenerator,
    generate_incident_post_mortem
)


class TestIncidentPostMortemGenerator(unittest.TestCase):

    def setUp(self):
        self.generator = IncidentPostMortemGenerator()
        self.random_incident_id = uuid.uuid4().hex
        self.random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.random_log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.random_target_path = f"/tmp/{uuid.uuid4().hex}.json"

    def tearDown(self):
        for path in [self.random_log_path, self.random_target_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_fetch_external_telemetry(self):
        telemetry = self.generator._fetch_external_telemetry(self.random_incident_id)
        self.assertIsInstance(telemetry, dict)
        self.assertIn("cpu_spike", telemetry)
        self.assertIsInstance(telemetry["cpu_spike"], float)

    def test_analyze_recovery_timeline_empty(self):
        result = self.generator._analyze_recovery_timeline([])
        self.assertEqual(result["total_duration"], 0)
        self.assertEqual(result["failure_rate"], 0.0)
        self.assertEqual(result["events_analyzed"], 0)

    def test_analyze_recovery_timeline_populated(self):
        events = [
            {"timestamp_start": 100, "timestamp_end": 150, "status": "SUCCESS"},
            {"timestamp_start": 200, "timestamp_end": 280, "status": "FAILED"},
            {"timestamp_start": 300, "timestamp_end": 320, "status": "SUCCESS"}
        ]
        result = self.generator._analyze_recovery_timeline(events)
        self.assertEqual(result["total_duration"], (150 - 100) + (280 - 200) + (320 - 300))
        self.assertAlmostEqual(result["failure_rate"], 1.0 / 3.0)
        self.assertEqual(result["events_analyzed"], 3)

    def test_generate_post_mortem_summary_empty_log(self):
        with open(self.random_log_path, "w", encoding="utf-8") as f:
            f.write("   \n  ")

        summary = self.generator.generate_post_mortem_summary(
            incident_id=self.random_incident_id,
            severity=self.random_severity,
            escalations=[{"id": uuid.uuid4().hex}],
            recoveries=[{"id": uuid.uuid4().hex}],
            log_file_path=self.random_log_path
        )

        self.assertEqual(summary["incident_id"], self.random_incident_id)
        self.assertEqual(summary["severity"], self.random_severity)
        self.assertEqual(summary["escalation_steps_count"], 1)
        self.assertEqual(summary["recovery_actions_count"], 1)
        self.assertEqual(summary["root_cause_analysis"], "INSUFFICIENT_LOG_DATA")
        self.assertIn("summary_id", summary)

    def test_generate_post_mortem_summary_valid_log(self):
        random_log_data = f"ERROR {uuid.uuid4().hex} critical failure detected"
        with open(self.random_log_path, "w", encoding="utf-8") as f:
            f.write(random_log_data)

        summary = self.generator.generate_post_mortem_summary(
            incident_id=self.random_incident_id,
            severity=self.random_severity,
            escalations=[],
            recoveries=[],
            log_file_path=self.random_log_path
        )

        self.assertEqual(summary["incident_id"], self.random_incident_id)
        self.assertEqual(summary["severity"], self.random_severity)
        self.assertEqual(summary["escalation_steps_count"], 0)
        self.assertEqual(summary["recovery_actions_count"], 0)
        self.assertEqual(summary["root_cause_analysis"], "ANALYZED_OK")

    def test_export_report_success(self):
        report_data = {
            "id": uuid.uuid4().hex,
            "metric": random.randint(1, 100)
        }
        res = self.generator.export_report(report_data, self.random_target_path, format="json")
        self.assertTrue(res)
        self.assertTrue(os.path.exists(self.random_target_path))

    def test_export_report_invalid_format(self):
        report_data = {"id": uuid.uuid4().hex}
        invalid_format = uuid.uuid4().hex
        with self.assertRaises(ValueError):
            self.generator.export_report(report_data, self.random_target_path, format=invalid_format)

    def test_generate_incident_post_mortem_wrapper(self):
        random_dir = f"/tmp/{uuid.uuid4().hex}"
        post_mortem_input = {
            "incident": {"id": self.random_incident_id, "details": uuid.uuid4().hex},
            "severity": {"severity": self.random_severity},
            "recovery": {"status": "SUCCESS", "action": uuid.uuid4().hex},
            "output_dir": random_dir
        }

        try:
            result = generate_incident_post_mortem(post_mortem_input)
            self.assertIsInstance(result, dict)
            self.assertEqual(result["incident_id"], self.random_incident_id)
            self.assertEqual(result["severity"], self.random_severity)
            self.assertIn("summary", result)
            self.assertIn("report_id", result)

            expected_file = os.path.join(random_dir, f"post_mortem_{self.random_incident_id}.json")
            self.assertTrue(os.path.exists(expected_file))
        finally:
            if os.path.exists(random_dir):
                for f in os.listdir(random_dir):
                    try:
                        os.remove(os.path.join(random_dir, f))
                    except OSError:
                        pass
                try:
                    os.rmdir(random_dir)
                except OSError:
                    pass


if __name__ == "__main__":
    unittest.main()