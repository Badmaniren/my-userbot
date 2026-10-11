import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_regulatory_compliance_validator import start_new

class TestMarketPortfolioRegulatoryComplianceValidator(unittest.TestCase):

    def setUp(self):
        self.rand_portfolio_id = uuid.uuid4().hex
        self.rand_limit_type = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.rand_metric_value = random.uniform(100.0, 100000.0)
        self.rand_audit_log_id = uuid.uuid4().hex

    def test_start_new_compliance_success(self):
        mock_db = MagicMock()
        mock_db.fetch_portfolio_limits.return_value = {
            "limit_type": self.rand_limit_type,
            "max_threshold": self.rand_metric_value * 2.0
        }
        mock_db.fetch_stress_indicators.return_value = {
            "current_exposure": self.rand_metric_value
        }

        mock_audit_exporter = MagicMock()
        mock_audit_exporter.export_audit_log.return_value = self.rand_audit_log_id

        dependencies = {
            "db_storage": mock_db,
            "market_portfolio_audit_log_exporter": mock_audit_exporter,
            "market_portfolio_monitor": MagicMock(),
            "market_portfolio_stress_reporter": MagicMock()
        }

        with patch('skills.market_portfolio_regulatory_compliance_validator.uuid.uuid4', return_value=uuid.UUID(self.rand_portfolio_id)):
            result = start_new(self.rand_portfolio_id, dependencies)

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "COMPLIANT")
        self.assertEqual(result["portfolio_id"], self.rand_portfolio_id)
        mock_db.fetch_portfolio_limits.assert_called_once_with(self.rand_portfolio_id)
        mock_audit_exporter.export_audit_log.assert_called_once()

    def test_start_new_compliance_violation(self):
        mock_db = MagicMock()
        mock_db.fetch_portfolio_limits.return_value = {
            "limit_type": self.rand_limit_type,
            "max_threshold": self.rand_metric_value * 0.5
        }
        mock_db.fetch_stress_indicators.return_value = {
            "current_exposure": self.rand_metric_value
        }

        mock_alert_dispatcher = MagicMock()
        mock_alert_dispatcher.dispatch_alert.return_value = True

        dependencies = {
            "db_storage": mock_db,
            "market_portfolio_alert_dispatcher": mock_alert_dispatcher,
            "market_portfolio_audit_log_exporter": MagicMock(),
            "market_portfolio_monitor": MagicMock()
        }

        stream_data = io.BytesIO(f"VIOLATION_{self.rand_portfolio_id}".encode('utf-8'))

        with patch('skills.market_portfolio_regulatory_compliance_validator.uuid.uuid4', return_value=uuid.UUID(self.rand_portfolio_id)):
            with patch('skills.market_portfolio_regulatory_compliance_validator.requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.raw = stream_data
                mock_response.status_code = 200
                mock_get.return_value = mock_response

                result = start_new(self.rand_portfolio_id, dependencies)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "VIOLATION_DETECTED")
        self.assertEqual(result["violation_metric"], self.rand_metric_value)
        mock_alert_dispatcher.dispatch_alert.assert_called_once()

    def test_start_new_missing_dependencies_raises_error(self):
        broken_dependencies = {
            "db_storage": None
        }

        with self.assertRaises((KeyError, ValueError, TypeError)):
            start_new(self.rand_portfolio_id, broken_dependencies)

    def test_start_new_stream_audit_log_handling(self):
        mock_db = MagicMock()
        mock_db.fetch_portfolio_limits.return_value = {
            "limit_type": self.rand_limit_type,
            "max_threshold": self.rand_metric_value * 1.5
        }
        mock_db.fetch_stress_indicators.return_value = {
            "current_exposure": self.rand_metric_value
        }

        mock_audit_hub = MagicMock()
        mock_audit_hub.verify_log_stream.return_value = True

        dependencies = {
            "db_storage": mock_db,
            "market_portfolio_audit_compliance_hub": mock_audit_hub,
            "market_portfolio_audit_log_exporter": MagicMock(),
            "market_portfolio_monitor": MagicMock()
        }

        result = start_new(self.rand_portfolio_id, dependencies)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("audit_verified"))
        mock_audit_hub.verify_log_stream.assert_called_once()

if __name__ == '__main__':
    unittest.main()