import unittest
import uuid
import random
from skills.market_portfolio_stress_ml_var_estimator_v2 import (
    MarketPortfolioStressMLVaREstimatorV2,
    evaluate_portfolio_stress_ml_var
)
from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import forecast_volatility
from skills.market_portfolio_stress_monte_carlo_engine import run_monte_carlo_simulation
from skills.market_portfolio_valuation import calculate_portfolio_valuation

class RealMarketPortfolioStressMLVaREstimatorV2IntegrationTest(unittest.TestCase):
    def test_end_to_end_var_estimation(self):
        dynamic_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        dynamic_confidence = round(random.uniform(0.90, 0.99), 2)
        dynamic_horizon = random.randint(10, 30)

        estimator = MarketPortfolioStressMLVaREstimatorV2(
            db_storage=None,
            market_portfolio_stress_ml_volatility_forecaster_v2=type('DummyForecaster', (), {'predict': lambda self, portfolio_id, horizon_days: random.uniform(0.01, 0.05)})(),
            market_portfolio_stress_monte_carlo_engine=type('DummyMC', (), {'simulate': lambda self, portfolio_id, confidence_level, horizon_days: {"var": random.uniform(1000.0, 50000.0)}})()
        )

        result = estimator.estimate_var(
            portfolio_id=dynamic_portfolio_id,
            confidence_level=dynamic_confidence,
            horizon_days=dynamic_horizon
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], dynamic_portfolio_id)
        self.assertEqual(result["confidence_level"], dynamic_confidence)
        self.assertEqual(result["horizon_days"], dynamic_horizon)
        self.assertIn("var_value", result)
        self.assertIsInstance(result["var_value"], float)

        eval_data = {
            "portfolio_id": dynamic_portfolio_id,
            "volatility_forecast": random.uniform(0.02, 0.08),
            "monte_carlo_results": {"var": result["var_value"]},
            "valuation": random.uniform(100000.0, 500000.0)
        }

        eval_result = evaluate_portfolio_stress_ml_var(eval_data)
        self.assertIsInstance(eval_result, dict)
        self.assertEqual(eval_result["portfolio_id"], dynamic_portfolio_id)
        self.assertIn("estimation_id", eval_result)
        self.assertTrue(eval_result["estimation_id"].startswith("est_"))
        self.assertEqual(eval_result["var_value"], eval_data["monte_carlo_results"]["var"])

if __name__ == "__main__":
    unittest.main()