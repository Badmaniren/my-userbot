import unittest
from unittest.mock import patch
import random
import uuid

from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer
)


class TestMarketPortfolioStressAuditVisualizer(unittest.TestCase):

    def test_visualizer_initialization_and_payload_handling(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        dependency_name = uuid.uuid4().hex
        
        visualizer = MarketPortfolioStressAuditVisualizer(**{dependency_name: rand_val})
        self.assertEqual(visualizer.dependencies[dependency_name], rand_val)

        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            rand_key: rand_val
        }

        result_obj = visualizer.visualize(payload)
        self.assertIn(portfolio_id, result_obj)
        
        direct_result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIn(portfolio_id, direct_result)

    def test_visualizer_graphical_format(self):
        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        payload = {
            "report_id": report_id,
            "format": "graphical"
        }

        result = market_portfolio_stress_audit_visualizer(payload)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), report_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")

    def test_visualizer_non_dict_payload(self):
        raw_string = uuid.uuid4().hex
        result = market_portfolio_stress_audit_visualizer(raw_string)
        self.assertEqual(result, raw_string)

    def test_visualizer_report_rendering_chaos(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id,
            "format": random.choice(["text_summary", "graphical"])
        }

        with patch("skills.market_portfolio_stress_audit_visualizer.requests.get") as mock_get:
            mock_resp = mock_get.return_value
            mock_resp.status_code = 200
            mock_resp.text = f"<html><body><div>{uuid.uuid4().hex}</div></body></html>"

            res = market_portfolio_stress_audit_visualizer(payload)
            self.assertIsNotNone(res)


if __name__ == "__main__":
    unittest.main()