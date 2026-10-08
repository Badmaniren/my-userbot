import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
import sys

try:
    import requests
except ImportError:
    requests = MagicMock()
    requests.exceptions.RequestException = Exception
    requests.exceptions.ConnectionError = Exception
    sys.modules["requests"] = requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = MagicMock()
    sys.modules["bs4"] = BeautifulSoup

from skills.market_portfolio_stress_audit_health_monitor import (
    StressAuditHealthMonitor,
    HealthMonitorError,
    TelemetryValidationError
)


class TestStressAuditHealthMonitor(unittest.TestCase):

    def setUp(self):
        self.db_url = f"postgresql://user_{uuid.uuid4().hex[:6]}:pass_{uuid.uuid4().hex[:6]}@localhost:{random.randint(1024, 65535)}/{uuid.uuid4().hex[:8]}"
        self.monitor = StressAuditHealthMonitor(db_storage=self.db_url)

    def test_storage_availability_success(self):
        random_status_code = random.choice([200, 201, 204])
        random_response_text = uuid.uuid4().hex

        with patch('skills.market_portfolio_stress_audit_health_monitor.requests') as mock_requests:
            if mock_requests is None:
                self.skipTest("requests module not available")
            mock_response = MagicMock()
            mock_response.status_code = random_status_code
            mock_response.text = random_response_text
            mock_requests.get.return_value = mock_response

            is_available = self.monitor.check_storage_availability()
            self.assertTrue(is_available)
            mock_requests.get.assert_called_once()

    def test_storage_availability_failure(self):
        random_status_code = random.choice([500, 502, 503, 404, 401])

        with patch('skills.market_portfolio_stress_audit_health_monitor.requests') as mock_requests:
            if mock_requests is None:
                self.skipTest("requests module not available")
            mock_response = MagicMock()
            mock_response.status_code = random_status_code
            mock_requests.get.return_value = mock_response

            is_available = self.monitor.check_storage_availability()
            self.assertFalse(is_available)

    def test_storage_availability_connection_error(self):
        with patch('skills.market_portfolio_stress_audit_health_monitor.requests') as mock_requests:
            if mock_requests is None:
                self.skipTest("requests module not available")
            conn_err = getattr(mock_requests.exceptions, "ConnectionError", Exception)
            mock_requests.get.side_effect = conn_err("Network unreachable")

            is_available = self.monitor.check_storage_availability()
            self.assertFalse(is_available)

    def test_telemetry_validation_success(self):
        random_telemetry_id = str(uuid.uuid4())
        random_risk_score = round(random.uniform(0.01, 99.99), 4)
        random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))

        valid_payload = {
            "telemetry_id": random_telemetry_id,
            "risk_score": random_risk_score,
            "metric": random_metric_name,
            "status": "HEALTHY"
        }

        result = self.monitor.validate_telemetry(valid_payload)
        self.assertTrue(result)

    def test_telemetry_validation_missing_fields(self):
        random_telemetry_id = str(uuid.uuid4())
        invalid_payload = {
            "telemetry_id": random_telemetry_id
        }

        with self.assertRaises(TelemetryValidationError):
            self.monitor.validate_telemetry(invalid_payload)

    def test_telemetry_validation_out_of_bounds(self):
        random_telemetry_id = str(uuid.uuid4())
        invalid_risk_score = random.choice([-500.0, 105.5, -0.1])
        random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))

        invalid_payload = {
            "telemetry_id": random_telemetry_id,
            "risk_score": invalid_risk_score,
            "metric": random_metric_name,
            "status": "CRITICAL"
        }

        with self.assertRaises(TelemetryValidationError):
            self.monitor.validate_telemetry(invalid_payload)

    def test_parse_audit_report_stream(self):
        random_heading = ''.join(random.choices(string.ascii_uppercase, k=12))
        random_metric_val = str(random.randint(1000, 99999))
        html_content = f"<html><body><h1>{random_heading}</h1><span id='audit-metric'>{random_metric_val}</span></body></html>"

        byte_stream = io.BytesIO(html_content.encode('utf-8'))

        parsed_data = self.monitor.parse_audit_report_stream(byte_stream)

        if sys.modules.get("bs4") and hasattr(sys.modules["bs4"], "BeautifulSoup") and not isinstance(sys.modules["bs4"].BeautifulSoup, MagicMock):
            self.assertEqual(parsed_data.get("heading"), random_heading)
            self.assertEqual(parsed_data.get("metric"), random_metric_val)
        else:
            self.assertIn("heading", parsed_data)
            self.assertIn("metric", parsed_data)

    def test_health_monitor_full_diagnostic_cycle(self):
        random_id = uuid.uuid4().hex
        random_score = round(random.uniform(1.0, 50.0), 2)

        diagnostic_data = {
            "telemetry_id": random_id,
            "risk_score": random_score,
            "metric": "var_liquidity_core",
            "status": "NOMINAL"
        }

        with patch('skills.market_portfolio_stress_audit_health_monitor.requests') as mock_requests:
            if mock_requests is not None:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_requests.get.return_value = mock_response

            report = self.monitor.run_full_diagnostic(diagnostic_data)

            self.assertEqual(report["storage_status"], "ONLINE")
            self.assertEqual(report["telemetry_status"], "VALIDATED")
            self.assertEqual(report["processed_id"], random_id)


if __name__ == '__main__':
    unittest.main()
