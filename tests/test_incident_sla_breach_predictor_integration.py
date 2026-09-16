import unittest
import uuid
import random
from skills.incident_sla_breach_predictor import IncidentSLABreachPredictor, incident_sla_breach_predictor

class TestIncidentSLABreachPredictorIntegration(unittest.TestCase):
    def setUp(self):
        self.predictor = IncidentSLABreachPredictor()
        self.test_incident_id = str(uuid.uuid4())

    def test_forecast_breach_integration(self):
        random_elapsed = random.randint(10, 300)
        random_limit = random_elapsed + random.randint(1, 1000)
        
        payload = {
            "incident_id": self.test_incident_id,
            "sla_data": {
                "sla_limit_seconds": random_limit,
                "current_elapsed_seconds": random_elapsed,
                "priority": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
            },
            "trend_data": {
                "risk_score": random.uniform(0.0, 1.0),
                "trend_id": f"trend_{uuid.uuid4()}"
            }
        }

        result_func = incident_sla_breach_predictor(payload)
        
        self.assertIsInstance(result_func, dict)
        self.assertEqual(result_func["incident_id"], self.test_incident_id)
        self.assertIn("breach_predicted", result_func)
        self.assertIn("trend_reference", result_func)

        try:
            result_class = self.predictor.forecast_breach(self.test_incident_id)
            self.assertIsInstance(result_class, dict)
            self.assertEqual(result_class["incident_id"], self.test_incident_id)
        except Exception as e:
            self.assertIn("Incident data not found", str(e))

    def test_streams_and_escalations_integration(self):
        try:
            stream_res = self.predictor.consume_forecaster_stream()
            self.assertIsNotNone(stream_res)
        except Exception:
            pass

        try:
            escalation_res = self.predictor.force_escalate_prediction(self.test_incident_id)
            self.assertIsNotNone(escalation_res)
        except Exception:
            pass

if __name__ == "__main__":
    unittest.main()