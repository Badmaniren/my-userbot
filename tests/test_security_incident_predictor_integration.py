import unittest
import uuid
import random
import os
from skills.security_incident_predictor import (
    incident_trend_analyzer,
    system_health_telemetry_collector,
    system_risk_evaluator
)

class TestSecurityIncidentPredictorIntegration(unittest.TestCase):
    def test_predict_security_incidents_integration(self):
        unique_metric_id = f"metric-{uuid.uuid4()}"
        telemetry_value = random.uniform(10.0, 99.9)
        risk_threshold = random.randint(1, 100)

        telemetry_data = {
            "id": unique_metric_id,
            "load": telemetry_value,
            "anomaly_score": random.random()
        }

        collected_telemetry = system_health_telemetry_collector(telemetry_data)
        evaluated_risk = system_risk_evaluator(collected_telemetry, threshold=risk_threshold)
        trend_report = incident_trend_analyzer(evaluated_risk)

        prediction_marker = f"pred-{uuid.uuid4()}"
        output_file_path = f"incident_forecast_{unique_metric_id}.log"

        with open(output_file_path, "w") as f:
            f.write(f"MARKER: {prediction_marker}\n")
            f.write(f"TREND: {trend_report}\n")

        self.assertTrue(os.path.exists(output_file_path))

        with open(output_file_path, "r") as f:
            content = f.read()
            self.assertIn(prediction_marker, content)

        if os.path.exists(output_file_path):
            os.remove(output_file_path)

if __name__ == "__main__":
    unittest.main()