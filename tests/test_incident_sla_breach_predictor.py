import unittest
from unittest.mock import patch
import io
import os
import uuid
import random
from skills.incident_sla_breach_predictor import (
    IncidentSLABreachPredictor,
    incident_sla_breach_predictor
)

class TestIncidentSLABreachPredictor(unittest.TestCase):

    def setUp(self):
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.response_time = random.uniform(1.0, 50.0)
        self.predictor = IncidentSLABreachPredictor()
        self.random_id = uuid.uuid4().hex

    def tearDown(self):
        output_file_path = f"sla_prediction_{self.random_id}.json"
        if os.path.exists(output_file_path):
            os.remove(output_file_path)

    def test_predict_breach_valid(self):
        result = self.predictor.predict_breach(self.severity, self.response_time)
        self.assertIn("risk_score", result)
        self.assertIn("will_breach", result)
        self.assertIsInstance(result["risk_score"], float)
        self.assertIsInstance(result["will_breach"], bool)
        self.assertEqual(result["severity"], self.severity)
        self.assertEqual(result["response_time"], self.response_time)

    def test_predict_breach_empty_severity(self):
        with self.assertRaises(ValueError):
            self.predictor.predict_breach("", self.response_time)

    def test_evaluate_stream(self):
        stream_content = f"{self.severity},{self.response_time}\nLOW,invalid_rt\n".encode('utf-8')
        stream_io = io.BytesIO(stream_content)
        results = self.predictor.evaluate_stream(stream_io)
        self.assertGreaterEqual(len(results), 1)
        self.assertIn("risk_score", results[0])

    def test_functional_wrapper(self):
        payload = {
            "incident_id": self.random_id,
            "severity": self.severity,
            "response_time_minutes": self.response_time
        }
        result = incident_sla_breach_predictor(payload)
        self.assertEqual(result["incident_id"], self.random_id)
        self.assertIn("probability", result)
        self.assertIn("risk_score", result)
        self.assertIn("breach_predicted", result)

        output_file_path = f"sla_prediction_{self.random_id}.json"
        self.assertTrue(os.path.exists(output_file_path))

    def test_functional_wrapper_defaults(self):
        payload = {}
        result = incident_sla_breach_predictor(payload)
        self.assertIn("incident_id", result)
        self.assertEqual(result["risk_score"], 10.0 * (len("LOW") / 10.0))

        output_file_path = f"sla_prediction_{result['incident_id']}.json"
        if os.path.exists(output_file_path):
            os.remove(output_file_path)

if __name__ == "__main__":
    unittest.main()