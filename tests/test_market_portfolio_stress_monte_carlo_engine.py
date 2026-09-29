import unittest
from skills.market_portfolio_stress_monte_carlo_engine import (
    run_monte_carlo_stress_simulation,
    MarketPortfolioStressMonteCarloEngine
)

class TestMarketPortfolioStressMonteCarloEngine(unittest.TestCase):

    def test_run_monte_carlo_stress_simulation_success(self):
        portfolio_id = "test_port_123"
        composition = {"BTC": 0.6, "ETH": 0.4}
        result = run_monte_carlo_stress_simulation(
            portfolio_id=portfolio_id,
            composition=composition,
            simulations=100,
            horizon_days=10
        )
        self.assertIn("simulation_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["composition"], composition)
        self.assertEqual(result["simulations"], 100)
        self.assertEqual(result["horizon_days"], 10)
        self.assertIn("stress_var_95", result)
        self.assertIn("max_drawdown_expected", result)
        self.assertEqual(result["status"], "completed")

    def test_run_simulation_class_wrapper(self):
        engine = MarketPortfolioStressMonteCarloEngine()
        portfolio_id = "test_port_456"
        composition = {"AAPL": 0.5, "GOOGL": 0.5}
        result = engine.run_simulation(
            portfolio_id=portfolio_id,
            composition=composition,
            simulations=50,
            horizon_days=5
        )
        self.assertIn("simulation_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)

    def test_invalid_parameters_raise_value_error(self):
        with self.assertRaises(ValueError):
            run_monte_carlo_stress_simulation("", {"BTC": 1.0})

        with self.assertRaises(ValueError):
            run_monte_carlo_stress_simulation("port_1", {})

        with self.assertRaises(ValueError):
            run_monte_carlo_stress_simulation("port_1", {"BTC": 1.0}, simulations=0)

        with self.assertRaises(ValueError):
            run_monte_carlo_stress_simulation("port_1", {"BTC": 1.0}, horizon_days=-5)

if __name__ == "__main__":
    unittest.main()
