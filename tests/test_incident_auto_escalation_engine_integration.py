import unittest
import uuid
import random
import os
import tempfile
import json
from skills.incident_auto_escalation_engine import IncidentAutoEscalator, incident_auto_escalation_engine

class TestIncidentAutoEscalationEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.escalator = IncidentAutoEscalator()
        self.test_incident_id = str(uuid.uuid4())
        self.test_error_code = f"ERR_{random.randint(1000, 9999)}"
        self.test_package_name = f"pkg-{uuid.uuid4().hex[:6]}"
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_evaluate_and_escalate_integration(self):
        result = self.escalator.evaluate_and_escalate(self.test_incident_id)
        self.assertIn(self.test_incident_id, result)
        self.assertTrue(len(result) > 0)

    def test_incident_auto_escalation_engine_file_export(self):
        payload = {
            "incident_id": self.test_incident_id,
            "export_path": self.temp_dir.name,
            "random_flag": random.choice([True, False]),
            "metric_value": random.uniform(1.0, 100.0)
        }

        result = incident_auto_escalation_engine(payload)

        self.assertEqual(result["escalated_incident_id"], self.test_incident_id)
        self.assertTrue(result["is_escalated"])

        expected_file_name = f"escalation_{self.test_incident_id}.json"
        expected_file_path = os.path.join(self.temp_dir.name, expected_file_name)

        self.assertTrue(os.path.exists(expected_file_path), "Файл эскалации должен быть создан на диске")

        with open(expected_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["escalated_incident_id"], self.test_incident_id)
            self.assertEqual(data["details"]["metric_value"], payload["metric_value"])

    def test_recover_system_integration(self):
        recovery_result = self.escalator.recover_system(self.test_incident_id, self.test_error_code)
        self.assertIsNotNone(recovery_result)

    def test_audit_dependencies_integration(self):
        audit_result = self.escalator.audit_dependencies(self.test_package_name)
        self.assertIsNotNone(audit_result)

    def test_forecast_trend_integration(self):
        horizon = random.randint(1, 48)
        forecast = self.escalator.forecast_trend(self.test_incident_id, horizon)
        self.assertIsNotNone(forecast)

    def test_get_system_health_integration(self):
        system_id = f"sys-{random.randint(100, 999)}"
        health_score = self.escalator.get_system_health(system_id)
        self.assertIsNotNone(health_score)

if __name__ == "__main__":
    unittest.main()