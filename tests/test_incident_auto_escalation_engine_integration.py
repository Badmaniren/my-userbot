import unittest
import os
import shutil
import uuid
import random
from skills import incident_auto_escalation_engine
from skills import incident_aggregator
from skills import incident_severity_evaluator
from skills import notification_channel_dispatcher
from skills import incident_notification_broadcaster
from skills import system_health_telemetry_collector
from skills import incident_trend_analyzer
from skills import vulnerability_scanner
from skills import auto_patch_pipeline

class TestIncidentAutoEscalationEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.workspace_dir = f"./test_workspace_{uuid.uuid4().hex}"
        self.engine = incident_auto_escalation_engine.IncidentAutoEscalationEngine()

    def tearDown(self):
        if os.path.exists(self.workspace_dir):
            shutil.rmtree(self.workspace_dir)

    def test_process_escalation_integration(self):
        random_incident_id = f"INC-{uuid.uuid4().hex[:8]}"
        
        result = self.engine.process_escalation(random_incident_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("incident_id"), random_incident_id)
        self.assertIn("severity", result)
        self.assertIn("escalated_to", result)
        self.assertIn("channel", result)
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
        random_incident_id = f"INC-FILE-{uuid.uuid4().hex[:8]}"
        random_severity = random.randint(1, 10)

        result = incident_auto_escalation_engine.auto_escalate_incident(
            incident_id=random_incident_id,
            severity=random_severity,
            workspace_dir=self.workspace_dir
        )

        self.assertEqual(result.get("escalated_incident_id"), random_incident_id)
        self.assertEqual(result.get("severity"), random_severity)
        self.assertEqual(result.get("status"), "SUCCESS")

        expected_file = os.path.join(self.workspace_dir, f"escalated_{random_incident_id}.json")
        self.assertTrue(os.path.exists(expected_file), "Файл эскалации не был создан на диске.")

        with open(expected_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            self.assertEqual(file_data.get("escalated_incident_id"), random_incident_id)
            self.assertEqual(file_data.get("severity"), random_severity)

if __name__ == "__main__":
    unittest.main()