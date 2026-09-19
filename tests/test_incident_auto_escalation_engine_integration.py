import unittest
import os
import shutil
import uuid
import random
from skills.incident_auto_escalation_engine import (
    IncidentAutoEscalationEngine,
    auto_escalate_incident
)

class TestIncidentAutoEscalationEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.workspace_dir = os.path.join(os.getcwd(), f"test_workspace_{uuid.uuid4().hex}")
        self.engine = IncidentAutoEscalationEngine()

    def tearDown(self):
        if os.path.exists(self.workspace_dir):
            shutil.rmtree(self.workspace_dir, ignore_errors=True)

    def test_process_escalation_integration(self):
        random_incident_id = f"INC-{uuid.uuid4().hex[:8]}"
        result = self.engine.process_escalation(random_incident_id)

        self.assertIsInstance(result, dict)
        self.assertIn("incident_id", result)
        self.assertEqual(result["incident_id"], random_incident_id)
        self.assertIn("severity", result)
        self.assertIn("escalated_to", result)
        self.assertIn("broadcast_success", result)

    def test_evaluate_system_telemetry_risks_integration(self):
        report = self.engine.evaluate_system_telemetry_risks()
        self.assertIsInstance(report, dict)
        self.assertIn("risk_metric", report)

    def test_check_and_trigger_patching_integration(self):
        patch_result = self.engine.check_and_trigger_patching()
        self.assertIsInstance(patch_result, bool)

    def test_consume_stream_data_integration(self):
        stream_data = self.engine.consume_stream_data()
        self.assertIsInstance(stream_data, bytes)

    def test_auto_escalate_incident_file_creation(self):
        random_incident_id = str(uuid.uuid4())
        random_severity = random.randint(1, 10)

        escalation_result = auto_escalate_incident(
            incident_id=random_incident_id,
            severity=random_severity,
            workspace_dir=self.workspace_dir
        )

        self.assertIsInstance(escalation_result, dict)
        self.assertEqual(escalation_result["escalated_incident_id"], random_incident_id)
        self.assertEqual(escalation_result["severity"], random_severity)
        self.assertEqual(escalation_result["status"], "SUCCESS")

        expected_file_path = os.path.join(self.workspace_dir, f"escalated_{random_incident_id}.json")
        self.assertTrue(os.path.exists(expected_file_path))

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(random_incident_id, file_content)

if __name__ == "__main__":
    unittest.main()