import unittest
import os
import uuid
import random
from skills.incident_priority_resolver import IncidentPriorityResolver, resolve_incident_priority
from skills.incident_trend_analyzer import IncidentTrendAnalyzer
from skills.incident_trend_forecaster import IncidentTrendForecaster
from skills.system_health_monitoring_gateway import SystemHealthMonitoringGateway


class TestIncidentPriorityResolverIntegration(unittest.TestCase):

    def setUp(self):
        self.resolver = IncidentPriorityResolver()
        self.system_id = f"sys-{uuid.uuid4()}"
        self.incident_id = f"inc-{uuid.uuid4()}"
        self.report_file_path = f"report_{self.incident_id}.txt"

    def tearDown(self):
        if os.path.exists(self.report_file_path):
            try:
                os.remove(self.report_file_path)
            except OSError:
                pass

    def test_resolve_integration_flow(self):
        severity = round(random.uniform(10.0, 99.9), 2)
        anomaly = random.choice([True, False])

        trend_data = {
            "severity_score": severity,
            "anomaly_detected": anomaly,
            "metrics": {
                "cpu_load": random.randint(40, 100)
            }
        }

        priority = self.resolver.resolve(self.system_id, trend_data)
        self.assertIn(priority, ["CRITICAL", "HIGH", "MEDIUM", "LOW"])

    def test_evaluate_stream_integration(self):
        gateway = SystemHealthMonitoringGateway()
        result = self.resolver.evaluate_stream(gateway, self.system_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("system_id"), self.system_id)
        self.assertIn("priority", result)
        self.assertIn("error_code", result)

    def test_calculate_from_forecast_integration(self):
        priority = self.resolver.calculate_from_forecast(self.system_id)
        self.assertIn(priority, ["CRITICAL", "HIGH", "MEDIUM"])

    def test_resolve_incident_priority_file_generation(self):
        severity = round(random.uniform(0.0, 100.0), 2)
        anomaly = random.choice([True, False])

        trend_data = {
            "severity_score": severity,
            "anomaly_detected": anomaly
        }

        result = resolve_incident_priority(self.incident_id, trend_data)

        self.assertEqual(result.get("target_incident_id"), self.incident_id)
        self.assertIn(result.get("priority_level"), ["CRITICAL", "HIGH", "MEDIUM", "LOW"])

        generated_path = result.get("report_file_path")
        self.assertEqual(generated_path, self.report_file_path)
        self.assertTrue(os.path.exists(generated_path))

        with open(generated_path, "r") as f:
            content = f.read()
            self.assertIn(self.incident_id, content)
            self.assertIn(result.get("priority_level"), content)


if __name__ == "__main__":
    unittest.main()