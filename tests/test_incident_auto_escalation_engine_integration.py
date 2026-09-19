import unittest
import os
import json
import uuid
import random
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine, auto_escalate_incident

class TestIncidentAutoEscalationEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.engine = IncidentAutoEscalationEngine()
        self.random_incident_id = f"inc-{uuid.uuid4()}"
        self.workspace_dir = f"./test_workspace_{uuid.uuid4()}"

    def tearDown(self):
        if os.path.exists(self.workspace_dir):
            for file_name in os.listdir(self.workspace_dir):
                file_path = os.path.join(self.workspace_dir, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.workspace_dir)

    def test_process_escalation_integration(self):
        result = self.engine.process_escalation(self.random_incident_id)
        
        self.assertIsInstance(result, dict)
        self.assertIn("incident_id", result)
        self.assertEqual(result["incident_id"], self.random_incident_id)
        self.assertIn("severity", result)
        self.assertIn("escalated_to", result)
        self.assertIn("channel", result)
        self.assertIn("broadcast_success", result)

    def test_evaluate_system_telemetry_risks_integration(self):
        telemetry_report = self.engine.evaluate_system_telemetry_risks()
        
        self.assertIsInstance(telemetry_report, dict)
        self.assertIn("risk_metric", telemetry_report)
        self.assertIsInstance(telemetry_report["risk_metric"], (int, float))

    def test_check_and_trigger_patching_integration(self):
        patch_result = self.engine.check_and_trigger_patching()
        self.assertIsInstance(patch_result, bool)

    def test_consume_stream_data_integration(self):
        stream_data = self.engine.consume_stream_data()
        self.assertIsInstance(stream_data, bytes)

    def test_auto_escalate_incident_file_creation(self):
        severity = random.randint(1, 10)
        escalation_result = auto_escalate_incident(self.random_incident_id, severity, self.workspace_dir)
        
        self.assertEqual(escalation_result["escalated_incident_id"], self.random_incident_id)
        self.assertEqual(escalation_result["severity"], severity)
        self.assertEqual(escalation_result["status"], "SUCCESS")

        expected_file_path = os.path.join(self.workspace_dir, f"escalated_{self.random_incident_id}.json")
        self.assertTrue(os.path.exists(expected_file_path), "Файл эскалации инцидента не был создан на диске.")

        with open(expected_file_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)
            
        self.assertEqual(file_content["escalated_incident_id"], self.random_incident_id)
        self.assertEqual(file_content["severity"], severity)
        self.assertEqual(file_content["status"], "SUCCESS")

if __name__ == "__main__":
    unittest.main()