import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.incident_predictive_risk_analyzer import start_new

class TestIncidentPredictiveRiskAnalyzer(unittest.TestCase):
    
    def test_start_new_success_flow(self):
        random_telemetry_id = uuid.uuid4().hex
        random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        random_value = round(random.uniform(1.0, 100.0), 2)
        
        mock_telemetry_data = f"{random_telemetry_id},{random_metric_name},{random_value}\n".encode('utf-8')
        mock_file_stream = io.BytesIO(mock_telemetry_data)
        
        with patch('skills.incident_predictive_risk_analyzer.system_health_telemetry_collector') as mock_collector, \
             with patch('skills.incident_predictive_risk_analyzer.incident_trend_analyzer') as mock_analyzer:
            
            mock_collector.return_value = mock_file_stream
            expected_risk_score = random.randint(0, 100)
            mock_analyzer.return_value = {"risk_score": expected_risk_score, "target_id": random_telemetry_id}
            
            result = start_new(random_telemetry_id)
            
            self.assertIsInstance(result, dict)
            self.assertIn("risk_score", result)
            self.assertEqual(result["risk_score"], expected_risk_score)
            self.assertEqual(result["target_id"], random_telemetry_id)

    def test_start_new_empty_telemetry_handling(self):
        random_error_id = uuid.uuid4().hex
        empty_stream = io.BytesIO(b"")
        
        with patch('skills.incident_predictive_risk_analyzer.system_health_telemetry_collector') as mock_collector:
            mock_collector.return_value = empty_stream
            
            result = start_new(random_error_id)
            
            self.assertIsInstance(result, dict)
            self.assertTrue(result.get("error") or result.get("risk_score") == 0)

    def test_start_new_anomaly_detection_trigger(self):
        random_stream_id = uuid.uuid4().hex
        random_anomaly_code = ''.join(random.choices(string.ascii_uppercase, k=6))
        
        mock_payload = f"ID:{random_stream_id}|ANOMALY:{random_anomaly_code}".encode('ascii')
        
        with patch('skills.incident_predictive_risk_analyzer.telemetry_streamer') as mock_streamer, \
             with patch('skills.incident_predictive_risk_analyzer.incident_sla_breach_predictor') as mock_predictor:
            
            mock_streamer.return_value = io.BytesIO(mock_payload)
            mock_predictor.return_value = {"critical": True, "code": random_anomaly_code}
            
            response = start_new(random_stream_id)
            
            self.assertIn("critical", response)
            self.assertTrue(response["critical"])
            self.assertEqual(response["code"], random_anomaly_code)

    def test_start_new_exception_propagation(self):
        random_fault_uuid = uuid.uuid4().hex
        random_error_message = ''.join(random.choices(string.ascii_letters, k=15))
        
        with patch('skills.incident_predictive_risk_analyzer.system_health_aggregator') as mock_aggregator:
            mock_aggregator.side_effect = RuntimeError(random_error_message)
            
            with self.assertRaises(RuntimeError) as context:
                start_new(random_fault_uuid)
                
            self.assertIn(random_error_message, str(context.exception))

if __name__ == '__main__':
    unittest.main()