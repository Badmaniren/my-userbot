import unittest
from unittest.mock import patch
import random
import uuid

from skills.market_portfolio_var_simulation_engine import (
    MarketPortfolioVaRSimulationEngine,
    simulate_portfolio_var
)


class TestMarketPortfolioVaRSimulationEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.returns_series = [random.uniform(-0.05, 0.05) for _ in range(20)]
        self.engine = MarketPortfolioVaRSimulationEngine()

    def test_calculate_historical_var_success(self):
        confidence = 0.95
        result = self.engine.calculate_historical_var(self.portfolio_id, self.returns_series, confidence)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("var_historical", result)
        self.assertEqual(result["confidence"], confidence)

    def test_calculate_historical_var_empty_raises_error(self):
        with self.assertRaises(ValueError):
            self.engine.calculate_historical_var(self.portfolio_id, [], 0.95)

    def test_calculate_parametric_var_success(self):
        mean = random.uniform(-0.001, 0.001)
        std_dev = random.uniform(0.01, 0.03)
        confidence = 0.99

        result = self.engine.calculate_parametric_var(self.portfolio_id, mean, std_dev, confidence)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("var_parametric", result)
        self.assertEqual(result["confidence"], confidence)

    def test_simulate_portfolio_var_execution(self):
        total_val = random.uniform(50000.0, 500000.0)
        sim_id = f"sim_{uuid.uuid4().hex[:6]}"
        valuation_data = {
            "total_value": total_val,
            "returns_series": self.returns_series,
            "simulation_id": sim_id
        }

        horizon = random.randint(1, 10)
        conf = 0.95

        result = simulate_portfolio_var(self.portfolio_id, valuation_data, confidence_level=conf, horizon_days=horizon)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["simulation_id"], sim_id)
        self.assertEqual(result["confidence_level"], conf)
        self.assertEqual(result["horizon_days"], horizon)
        self.assertIn("var_historical", result)
        self.assertIn("var_parametric", result)


if __name__ == '__main__':
    unittest.main()