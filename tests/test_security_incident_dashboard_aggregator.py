import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json

from skills.security_incident_dashboard_aggregator import SecurityIncidentDashboardAggregator


class TestSecurityIncidentDashboardAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = SecurityIncidentDashboardAggregator()
        self.random_namespace = uuid.uuid4().hex
        self.random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_metric_value = random.randint(100, 9999)
        self.random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

    def test_aggregate_metrics_success(self):
        mock_payload = {
            "namespace": self.random_namespace,
            "metric": self.random_metric_name,
            "value": self.random_metric_value,
            "severity": self.random_severity
        }
        json_data = json.dumps(mock_payload).encode('utf-8')

        with patch('skills.security_incident_dashboard_aggregator.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = json_data
            mock_response.json.return_value = mock_payload
            mock_get.return_value = mock_response

            random_url = f"https://{uuid.uuid4().hex}.internal/api/metrics"
            result = self.aggregator.aggregate_system_metrics(random_url)

            self.assertIn("namespace", result)
            self.assertEqual(result["namespace"], self.random_namespace)
            self.assertEqual(result["metric"], self.random_metric_name)
            self.assertEqual(result["value"], self.random_metric_value)
            self.assertEqual(result["severity"], self.random_severity)

    def test_dashboard_report_generation_with_stream(self):
        random_stream_data = f"INCIDENT_ID:{uuid.uuid4().hex}|SEV:{self.random_severity}|VAL:{self.random_metric_value}".encode('utf-8')
        mock_stream = io.BytesIO(random_stream_data)

        with patch('skills.security_incident_dashboard_aggregator.open', return_value=mock_stream, create=True):
            random_file_path = f"/var/log/security/{uuid.uuid4().hex}.log"
            report = self.aggregator.generate_consolidated_dashboard(random_file_path)

            self.assertIsInstance(report, dict)
            self.assertIn("metrics_count", report)
            self.assertGreaterEqual(report["metrics_count"], 0)
            self.assertIn("raw_stream_read", report)
            self.assertTrue(report["raw_stream_read"])

    def test_incident_severity_distribution(self):
        incidents_list = []
        for _ in range(random.randint(3, 8)):
            incidents_list.append({
                "id": uuid.uuid4().hex,
                "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
                "score": random.uniform(1.0, 10.0)
            })

        with patch('skills.security_incident_dashboard_aggregator.sys.modules') as mock_modules:
            distribution = self.aggregator.compute_severity_distribution(incidents_list)

            self.assertIsInstance(distribution, dict)
            total_counted = sum(distribution.values())
            self.assertEqual(total_counted, len(incidents_list))

    def test_dashboard_aggregator_error_handling(self):
        random_error_code = random.randint(500, 599)
        random_url = f"https://api.{uuid.uuid4().hex}.net/v1/telemetry"

        with patch('skills.security_incident_dashboard_aggregator.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = random_error_code
            mock_get.return_value = mock_response

            result = self.aggregator.aggregate_system_metrics(random_url)

            self.assertIn("error", result)
            self.assertEqual(result["status_code"], random_error_code)


if __name__ == '__main__':
    unittest.main()