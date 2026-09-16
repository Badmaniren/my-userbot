import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.incident_impact_analyzer import IncidentImpactAnalyzer


class TestIncidentImpactAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = IncidentImpactAnalyzer()

    def test_analyze_financial_impact_success(self):
        incident_id = str(uuid.uuid4())
        downtime_minutes = random.randint(10, 500)
        cost_per_minute = round(random.uniform(10.0, 500.0), 2)
        
        mock_metrics_data = {
            "downtime_minutes": downtime_minutes,
            "cost_per_minute": cost_per_minute
        }
        mock_stream = io.BytesIO(json.dumps(mock_metrics_data).encode('utf-8'))

        with patch('skills.incident_impact_analyzer.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raw = mock_stream
            mock_response.json.return_value = mock_metrics_data
            mock_get.return_value = mock_response

            result = self.analyzer.analyze_financial_impact(incident_id)

            self.assertIn("total_loss", result)
            expected_loss = downtime_minutes * cost_per_minute
            self.assertEqual(result["total_loss"], expected_loss)
            self.assertEqual(result["incident_id"], incident_id)

    def test_analyze_operational_impact_degradation(self):
        incident_uuid = str(uuid.uuid4())
        random_log_prefix = ''.join(random.choices(string.ascii_letters, k=10))
        error_count = random.randint(100, 9999)
        log_content = f"{random_log_prefix} ERROR failures count: {error_count}\n"
        
        mock_log_stream = io.BytesIO(log_content.encode('utf-8'))

        with patch('skills.incident_impact_analyzer.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = mock_log_stream

            operational_score = self.analyzer.analyze_operational_impact(incident_uuid)

            self.assertIsInstance(operational_score, float)
            self.assertGreaterEqual(operational_score, 0.0)
            self.assertLessEqual(operational_score, 100.0)

    def test_aggregate_recovery_metrics_randomized(self):
        metric_key = str(uuid.uuid4())
        metric_value = random.randint(1000, 99999)
        recovery_logs = [
            f"RECOVERY_START id={str(uuid.uuid4())}",
            f"METRIC {metric_key}={metric_value}",
            "RECOVERY_END status=SUCCESS"
        ]
        
        mock_stream = io.BytesIO("\n".join(recovery_logs).encode('utf-8'))

        with patch('skills.incident_impact_analyzer.sys.stdin', mock_stream):
            aggregated = self.analyzer.aggregate_recovery_metrics()
            
            self.assertIsInstance(aggregated, dict)
            self.assertIn(metric_key, aggregated)
            self.assertEqual(aggregated[metric_key], metric_value)

    def test_calculate_total_incident_severity_index(self):
        financial_loss = round(random.uniform(500.0, 50000.0), 2)
        operational_degradation = round(random.uniform(1.0, 10.0), 2)
        
        with patch.object(self.analyzer, 'analyze_financial_impact', return_value={"total_loss": financial_loss}), \
             patch.object(self.analyzer, 'analyze_operational_impact', return_value=operational_degradation):
            
            incident_token = str(uuid.uuid4())
            severity_index = self.analyzer.calculate_severity_index(incident_token)
            
            expected_index = financial_loss * operational_degradation
            self.assertEqual(severity_index, expected_index)


if __name__ == '__main__':
    unittest.main()