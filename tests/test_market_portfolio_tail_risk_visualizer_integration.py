import unittest
import uuid
import random
import os
from skills.market_portfolio_tail_risk_visualizer import market_portfolio_tail_risk_visualizer

class TestMarketPortfolioTailRiskVisualizerIntegration(unittest.TestCase):
    def test_tail_risk_visualizer_integration(self):
        rand_portfolio_id = f"port_{uuid.uuid4()}"
        rand_simulation_id = f"sim_{uuid.uuid4()}"

        payload = {
            "portfolio_id": rand_portfolio_id,
            "simulation_id": rand_simulation_id
        }

        result = market_portfolio_tail_risk_visualizer(payload)

        self.assertIsInstance(result, dict)
        self.assertIn("chart_artifact_id", result)
        self.assertIn("tail_var", result)

        artifact_id = result["chart_artifact_id"]
        self.assertTrue(len(artifact_id) > 0)

        # Проверяем, что ID генерируется динамически, а не захардкожен
        payload_second = {
            "portfolio_id": f"port_{uuid.uuid4()}",
            "simulation_id": f"sim_{uuid.uuid4()}"
        }
        result_second = market_portfolio_tail_risk_visualizer(payload_second)
        self.assertNotEqual(result["chart_artifact_id"], result_second["chart_artifact_id"])

if __name__ == "__main__":
    unittest.main()