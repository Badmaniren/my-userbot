import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json

from skills.incident_severity_evaluator import IncidentSeverityEvaluator

class TestIncidentSeverityEvaluator(unittest.TestCase):

    def setUp(self):
        self.evaluator = IncidentSeverityEvaluator()
        self.random_telemetry_key = uuid.uuid4().hex
        self.random_vuln_id = f"CVE-{random.randint(1999, 2024)}-{random.randint(1000, 9999)}"
        self.random_score = round(random.uniform(1.0, 10.0), 1)

    def test_evaluate_severity_critical(self):
        dynamic_telemetry = {
            self.random_telemetry_key: random.choice([True, False]),
            "active_exploits": True,
            "cvss_score": 9.5
        }
        dynamic_vulnerabilities = [
            {"id": self.random_vuln_id, "severity": "CRITICAL", "exploit_available": True}
        ]

        result = self.evaluator.evaluate(dynamic_telemetry, dynamic_vulnerabilities)

        self.assertIn("severity_level", result)
        self.assertEqual(result["severity_level"], "CRITICAL")
        self.assertIn(self.random_vuln_id, str(result))

    def test_evaluate_severity_low_with_io_stream(self):
        random_bytes = uuid.uuid4().bytes + string.ascii_letters.encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        dynamic_telemetry = {
            "stream_data": mock_stream.read(),
            "metric_value": random.randint(1, 100)
        }
        dynamic_vulnerabilities = []

        with patch('skills.incident_severity_evaluator.IncidentSeverityEvaluator._external_check', return_value=False) as mock_ext:
            result = self.evaluator.evaluate(dynamic_telemetry, dynamic_vulnerabilities)
            mock_ext.assert_called_once()

        self.assertEqual(result.get("severity_level"), "LOW")
        self.assertIsInstance(result.get("score"), (int, float))

    def test_calculate_risk_factor_randomized(self):
        telemetry_payload = {
            "error_rate": random.uniform(0.0, 1.0),
            "unauthorized_access_attempts": random.randint(0, 500),
            "token": uuid.uuid4().hex
        }
        
        calculated_risk = self.evaluator.calculate_risk_factor(telemetry_payload)
        
        self.assertGreaterEqual(calculated_risk, 0.0)
        self.assertLessEqual(calculated_risk, 100.0)

    def test_evaluator_with_mocked_network_failure(self):
        random_url = f"https://{uuid.uuid4().hex}.internal-sec-audit.net/api"
        dynamic_payload = {
            "endpoint": random_url,
            "retry_count": random.randint(1, 5)
        }

        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception(uuid.uuid4().hex)
            
            evaluation = self.evaluator.evaluate_with_remote_telemetry(dynamic_payload)
            
            self.assertFalse(evaluation.get("remote_verified", True))
            self.assertIn("error", evaluation)

if __name__ == '__main__':
    unittest.main()