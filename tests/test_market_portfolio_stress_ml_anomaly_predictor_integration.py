import unittest
import uuid
import random
from skills.market_portfolio_stress_ml_anomaly_predictor import market_portfolio_stress_ml_anomaly_predictor

class TestMarketPortfolioStressMlAnomalyPredictorIntegration(unittest.TestCase):

    def test_market_portfolio_stress_ml_anomaly_predictor_integration(self):
        test_portfolio_id = str(uuid.uuid4())
        test_ml_threshold = round(random.uniform(0.5, 0.9), 2)
        test_simulation_ref = f"sim_ref_{uuid.uuid4().hex[:8]}"

        payload = {
            "portfolio_id": test_portfolio_id,
            "ml_threshold": test_ml_threshold,
            "simulation_ref": test_simulation_ref
        }

        result = market_portfolio_stress_ml_anomaly_predictor(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), test_portfolio_id)
        self.assertEqual(result.get("simulation_ref"), test_simulation_ref)
        self.assertIn("anomaly_predicted", result)
        self.assertIn("risk_score", result)
        self.assertIsInstance(result.get("risk_score"), (int, float))

if __name__ == "__main__":
    unittest.main()