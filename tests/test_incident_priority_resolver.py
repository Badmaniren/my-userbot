import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.incident_priority_resolver import IncidentPriorityResolver


class TestIncidentPriorityResolver(unittest.TestCase):

    def setUp(self):
        self.resolver = IncidentPriorityResolver()
        self.random_prefix = uuid.uuid4().hex[:8]
        self.error_code = f"ERR-{random.randint(100, 999)}"
        self.metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        self.system_id = f"sys-{random.randint(1000, 9999)}"

    def test_resolve_priority_critical_trend(self):
        dynamic_metric = f"{self.metric_name}_{random.choice(string.ascii_lowercase)}"
        dynamic_value = random.uniform(85.0, 99.9)
        
        mock_trend_data = {
            "metric": dynamic_metric,
            "anomaly_detected": True,
            "severity_score": dynamic_value,
            "error_signature": self.error_code
        }

        with patch("skills.incident_priority_resolver.IncidentTrendAnalyzer") as mock_analyzer_cls:
            mock_analyzer_instance = mock_analyzer_cls.return_value
            mock_analyzer_instance.analyze.return_value = mock_trend_data

            priority = self.resolver.resolve(self.system_id, mock_trend_data)

            self.assertEqual(priority, "CRITICAL")
            mock_analyzer_instance.analyze.assert_called_once()

    def test_resolve_priority_low_trend(self):
        dynamic_metric = f"{self.metric_name}_{random.choice(string.ascii_lowercase)}"
        dynamic_value = random.uniform(1.0, 30.0)
        
        mock_trend_data = {
            "metric": dynamic_metric,
            "anomaly_detected": False,
            "severity_score": dynamic_value,
            "error_signature": self.error_code
        }

        with patch("skills.incident_priority_resolver.IncidentTrendAnalyzer") as mock_analyzer_cls:
            mock_analyzer_instance = mock_analyzer_cls.return_value
            mock_analyzer_instance.analyze.return_value = mock_trend_data

            priority = self.resolver.resolve(self.system_id, mock_trend_data)

            self.assertEqual(priority, "LOW")

    def test_evaluate_from_monitoring_stream(self):
        stream_data = io.BytesIO(f"SYSTEM_ID:{self.system_id}|STATUS:FAIL|CODE:{self.error_code}".encode('utf-8'))

        with patch("skills.incident_priority_resolver.SystemHealthMonitoringGateway") as mock_gateway_cls:
            mock_gateway = mock_gateway_cls.return_value
            mock_gateway.stream_logs.return_value = stream_data

            result = self.resolver.evaluate_stream(mock_gateway, self.system_id)

            self.assertIsInstance(result, dict)
            self.assertIn("priority", result)
            self.assertEqual(result.get("system_id"), self.system_id)
            self.assertEqual(result.get("error_code"), self.error_code)

    def test_calculate_priority_score_edge_cases(self):
        score = random.randint(50, 84)
        dynamic_system = f"host-{uuid.uuid4().hex[:5]}"
        
        with patch("skills.incident_priority_resolver.IncidentTrendForecaster") as mock_forecaster_cls:
            mock_forecaster = mock_forecaster_cls.return_value
            mock_forecaster.predict_next_spike.return_value = {
                "system": dynamic_system,
                "predicted_load": score,
                "confidence": 0.95
            }

            computed_priority = self.resolver.calculate_from_forecast(dynamic_system)
            
            self.assertIn(computed_priority, ["MEDIUM", "HIGH", "CRITICAL"])


if __name__ == "__main__":
    unittest.main()