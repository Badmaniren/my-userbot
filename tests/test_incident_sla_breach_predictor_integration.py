import unittest
import uuid
import random
from skills.incident_sla_breach_predictor import incident_sla_breach_predictor
from skills.incident_sla_tracker import incident_sla_tracker
from skills.incident_trend_analyzer import incident_trend_analyzer

class TestIncidentSlaBreachPredictorIntegration(unittest.TestCase):
    def test_sla_breach_prediction_integration(self):
        incident_id = f"INC-{uuid.uuid4()}"
        metric_value = random.randint(50, 500)
        
        tracker_input = {
            "incident_id": incident_id,
            "sla_limit_seconds": metric_value,
            "current_elapsed_seconds": random.randint(10, 40)
        }
        
        sla_tracking_data = incident_sla_tracker(tracker_input)
        
        trend_input = {
            "incident_id": incident_id,
            "trend_factor": random.random() * 2.0
        }
        trend_data = incident_trend_analyzer(trend_input)
        
        predictor_payload = {
            "incident_id": incident_id,
            "sla_data": sla_tracking_data,
            "trend_data": trend_data
        }
        
        result = incident_sla_breach_predictor(predictor_payload)
        
        self.assertIsInstance(result, dict)
        self.assertIn("breach_predicted", result)
        self.assertIn("incident_id", result)
        self.assertEqual(result["incident_id"], incident_id)
        self.assertIsInstance(result["breach_predicted"], bool)

if __name__ == "__main__":
    unittest.main()