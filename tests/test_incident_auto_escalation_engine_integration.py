import unittest
import os
import json
import uuid
import random
import tempfile

from skills.incident_auto_escalation_engine import (
    IncidentAutoEscalationEngine,
    auto_escalate_incident
)
from skills import incident_aggregator

class TestIncidentAutoEscalationEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.engine = IncidentAutoEscalationEngine()
        self.test_dir = tempfile.TemporaryDirectory()
        self.random_incident_id = f"INC-{uuid.uuid4()}"
        self.random_severity = random.randint(1, 100)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_process_escalation_end_to_end(self):
        result = self.engine.process_escalation(self.random_incident_id)
        
        self.assertIsInstance(result, dict)
        self.assertIn("incident_id", result)
        self.assertEqual(result["incident_id"], self.random_incident_id)
        self.assertIn("severity", result)
        self.assertIn("escalated_to", result)
        self.assertIn("broadcast_success", result)

    def test_evaluate_system_telemetry_risks_flow(self):
        report = self.engine.evaluate_system_telemetry_risks()
        
        self.assertIsInstance(report, dict)
        self.assertIn("risk_metric", report)

    def test_check_and_trigger_patching_execution(self):
        patch_result = self.engine.check_and_trigger_patching()
        self.assertIsInstance(patch_result, bool)

    def test_consume_stream_data_pipeline(self):
        stream_data = self.engine.consume_stream_data()
        self.assertIsInstance(stream_data, bytes)

    def test_auto_escalate_incident_file_creation(self):
        result = auto_escalate_incident(
            incident_id=self.random_incident_id,
            severity=self.random_severity,
            workspace_dir=self.test_dir.name
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["escalated_incident_id"], self.random_incident_id)
        self.assertEqual(result["severity"], self.random_severity)
        self.assertEqual(result["status"], "SUCCESS")

        expected_filename = f"escalated_{self.random_incident_id}.json"
        expected_filepath = os.path.join(self.test_dir.name, expected_filename)
        
        self.assertTrue(os.path.exists(expected_filepath), f"File {expected_filepath} was not created.")

        with open(expected_filepath, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data["escalated_incident_id"], self.random_incident_id)
        self.assertEqual(file_data["severity"], self.random_severity)
        self.assertEqual(file_data["status"], "SUCCESS")

if __name__ == "__main__":
    unittest.main()