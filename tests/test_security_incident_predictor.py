import unittest
from unittest.mock import patch
import io
import random
import uuid
import string

from skills.security_incident_predictor import SecurityIncidentPredictor

class TestSecurityIncidentPredictor(unittest.TestCase):
    def setUp(self):
        self.predictor = SecurityIncidentPredictor()

    def test_predict_incident_probability_valid_metrics(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        metric_value = random.uniform(1.0, 100.0)
        telemetry_id = uuid.uuid4().hex
        
        metrics = {metric_name: metric_value}
        telemetry = {"id": telemetry_id, "load": random.randint(10, 999)}

        result = self.predictor.predict(metrics, telemetry)
        
        self.assertIsInstance(result, dict)
        self.assertIn("incident_probability", result)
        self.assertIn("risk_score", result)
        self.assertIn(metric_name, result["analyzed_metrics"])
        self.assertEqual(result["telemetry_reference"], telemetry_id)
        self.assertGreaterEqual(result["incident_probability"], 0.0)
        self.assertLessEqual(result["incident_probability"], 1.0)

    def test_predict_incident_with_stream_telemetry(self):
        random_bytes = uuid.uuid4().bytes + uuid.uuid4().bytes
        stream_data = io.BytesIO(random_bytes)
        
        vulnerability_score = random.randint(1, 10)
        
        with patch('skills.security_incident_predictor.SecurityIncidentPredictor._read_telemetry_stream') as mock_read:
            mock_read.return_value = stream_data
            
            result = self.predictor.evaluate_stream_risk(stream_data, vulnerability_score)
            
            self.assertIsInstance(result, dict)
            self.assertTrue(result["processed"])
            self.assertEqual(result["vulnerability_score"], vulnerability_score)
            self.assertIsInstance(result["stream_hash"], str)
            self.assertTrue(len(result["stream_hash"]) > 0)

    def test_anomaly_threshold_breach_detection(self):
        threshold = random.uniform(50.0, 90.0)
        metric_key = uuid.uuid4().hex
        spike_value = threshold + random.uniform(1.1, 50.0)
        
        metrics = {metric_key: spike_value}
        
        with patch('skills.security_incident_predictor.SecurityIncidentPredictor._fetch_dynamic_threshold') as mock_thresh:
            mock_thresh.return_value = threshold
            
            assessment = self.predictor.assess_anomaly(metrics, metric_key)
            
            self.assertTrue(assessment["breach_detected"])
            self.assertEqual(assessment["metric_key"], metric_key)
            self.assertEqual(assessment["threshold"], threshold)
            self.assertEqual(assessment["actual_value"], spike_value)

    def test_empty_metrics_handling(self):
        empty_metrics = {}
        telemetry = {"status": uuid.uuid4().hex}
        
        result = self.predictor.predict(empty_metrics, telemetry)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["incident_probability"], 0.0)
        self.assertEqual(result["risk_score"], 0.0)
        self.assertEqual(result["analyzed_metrics"], [])

if __name__ == '__main__':
    unittest.main()