import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer
from skills.market_portfolio_alert_dispatcher import market_portfolio_alert_dispatcher
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_stress_audit_visualizer_end_to_end_integration(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        adaptive_score = round(random.uniform(1.0, 99.9), 2)
        tail_risk_value = round(random.uniform(0.01, 0.5), 4)

        monte_carlo_payload = {
            "portfolio_id": portfolio_id,
            "simulations": random.randint(100, 1000),
            "confidence_level": 0.95
        }

        mc_result = market_portfolio_stress_monte_carlo_engine(monte_carlo_payload)

        visualizer_payload = {
            "portfolio_id": portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": adaptive_score,
            "tail_risk_metrics": {
                "var_95": tail_risk_value,
                "monte_carlo_data": mc_result
            },
            "stream_payload": True
        }

        visualizer = MarketPortfolioStressAuditVisualizer()
        visualization_output = visualizer.visualize(visualizer_payload)

        self.assertIsInstance(visualization_output, dict)
        self.assertEqual(visualization_output.get("portfolio_id"), portfolio_id)
        self.assertEqual(visualization_output.get("status"), "success")
        self.assertEqual(visualization_output.get("adaptive_risk_score"), adaptive_score)
        self.assertIn("tail_risk_metrics", visualization_output)

        alert_payload = {
            "alert_id": str(uuid.uuid4()),
            "portfolio_id": portfolio_id,
            "severity": "HIGH",
            "dashboard_metrics": visualization_output
        }

        dispatch_result = market_portfolio_alert_dispatcher(alert_payload)

        if isinstance(dispatch_result, dict):
            self.assertIn("status", dispatch_result)
        else:
            self.assertIsInstance(dispatch_result, (str, bool))

if __name__ == "__main__":
    unittest.main()