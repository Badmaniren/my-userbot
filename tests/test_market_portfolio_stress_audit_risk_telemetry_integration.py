import unittest
import uuid
import random
from unittest.mock import patch
from skills.market_portfolio_stress_audit_risk_telemetry import (
    start_new,
    market_portfolio_stress_audit_risk_telemetry
)
try:
    from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
except (ImportError, AttributeError):
    market_portfolio_collector_agent = None

try:
    from skills.market_portfolio_stress_audit_exporter_v2 import market_portfolio_stress_audit_exporter_v2
except (ImportError, AttributeError):
    market_portfolio_stress_audit_exporter_v2 = None

class IntegrationTestMarketPortfolioStressAuditRiskTelemetry(unittest.TestCase):

    @patch('skills.market_portfolio_stress_audit_risk_telemetry.requests.post')
    def test_start_new_integration_flow(self, mock_requests_post):
        random_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        random_audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        random_metric_value = random.uniform(10500.5, 99999.9)

        telemetry_stream = {
            "portfolio_id": random_portfolio_id,
            "audit_id": random_audit_id,
            "metric_value": random_metric_value
        }

        dependencies = {
            "market_portfolio_collector_agent": market_portfolio_collector_agent,
            "market_portfolio_stress_audit_exporter_v2": market_portfolio_stress_audit_exporter_v2
        }

        result = start_new(dependencies, telemetry_stream=telemetry_stream)

        self.assertIsInstance(result, dict)
        self.assertIn("telemetry_id", result)
        self.assertEqual(result.get("portfolio_id"), random_portfolio_id)
        self.assertEqual(result.get("audit_id"), random_audit_id)
        self.assertTrue(mock_requests_post.called)

    def test_class_method_integration(self):
        random_portfolio_id = str(uuid.uuid4())
        random_audit_id = str(uuid.uuid4())

        input_data = {
            "portfolio_id": random_portfolio_id,
            "audit_id": random_audit_id,
            "entropy": random.randint(1, 100)
        }

        processed = market_portfolio_stress_audit_risk_telemetry.process_telemetry(input_data)

        self.assertEqual(processed["portfolio_id"], random_portfolio_id)
        self.assertEqual(processed["audit_id"], random_audit_id)
        self.assertEqual(processed["status"], "processed")
        self.assertIn("telemetry_id", processed)
        self.assertTrue(len(processed["telemetry_id"]) > 0)

if __name__ == '__main__':
    unittest.main()