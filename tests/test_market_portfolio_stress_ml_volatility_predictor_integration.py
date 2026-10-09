import unittest
import uuid
import random
from skills.market_portfolio_stress_ml_volatility_predictor import market_portfolio_stress_ml_volatility_predictor
from skills.db_storage import db_storage

class TestMarketPortfolioStressMlVolatilityPredictorIntegration(unittest.TestCase):
    def test_market_portfolio_stress_ml_volatility_predictor_integration(self):
        unique_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        stress_mult = round(random.uniform(1.0, 3.0), 2)
        horizon_val = random.randint(10, 500)

        simulation_data = {
            "stress_multiplier": stress_mult
        }

        result = market_portfolio_stress_ml_volatility_predictor(
            portfolio_id=unique_portfolio_id,
            simulation_data=simulation_data,
            historical_horizon=horizon_val
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), unique_portfolio_id)
        self.assertEqual(result.get("horizon"), horizon_val)

        expected_volatility = float(0.05 * (stress_mult * (1.0 + horizon_val / 1000.0)))
        self.assertAlmostEqual(result.get("predicted_volatility"), expected_volatility)

        stored_data = db_storage(
            action="get_prediction",
            target_id=unique_portfolio_id
        )

        if stored_data:
            self.assertEqual(stored_data.get("portfolio_id"), unique_portfolio_id)
            self.assertAlmostEqual(stored_data.get("predicted_volatility"), expected_volatility)

if __name__ == "__main__":
    unittest.main()