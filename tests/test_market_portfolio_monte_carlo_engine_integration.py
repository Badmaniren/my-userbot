import unittest
import uuid
import random

from skills.market_portfolio_monte_carlo_engine import MonteCarloEngine, market_portfolio_monte_carlo_engine
from skills import db_storage
from skills import market_portfolio_visualizer_v2
from skills import market_portfolio_performance_analytics
from skills import market_portfolio_stress_scenario_pipeline


class TestMarketPortfolioMonteCarloEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.iterations = random.randint(100, 500)
        self.horizon_days = random.randint(10, 60)
        self.initial_capital = round(random.uniform(50000.0, 150000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.3), 4)

    def test_run_simulation_integration(self):
        engine = MonteCarloEngine()

        asset_symbol = f"AST_{uuid.uuid4().hex[:6]}"
        mean_return = round(random.uniform(0.04, 0.12), 4)

        input_data = {
            "portfolio_id": self.portfolio_id,
            "iterations": self.iterations,
            "horizon_days": self.horizon_days,
            "initial_capital": self.initial_capital,
            "assets": [
                {
                    "symbol": asset_symbol,
                    "weight": 1.0,
                    "mean_return": mean_return,
                    "volatility": self.volatility
                }
            ]
        }

        result = engine.run_simulation(input_data)

        self.assertIn("simulation_id", result)
        self.assertIsInstance(result["simulation_id"], str)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["iterations_executed"], self.iterations)
        self.assertEqual(result["horizon_days"], self.horizon_days)
        self.assertGreater(result["expected_final_value"], 0.0)
        self.assertGreater(result["percentile_95"], result["percentile_5"])

    def test_market_portfolio_monte_carlo_engine_wrapper(self):
        config = {
            "portfolio_id": self.portfolio_id,
            "simulations": self.iterations,
            "horizon_days": self.horizon_days,
            "volatility": self.volatility
        }

        wrapped_result = market_portfolio_monte_carlo_engine(config)

        self.assertEqual(wrapped_result["portfolio_id"], self.portfolio_id)
        self.assertIn("results", wrapped_result)

        res_details = wrapped_result["results"]
        self.assertIn("simulation_id", res_details)
        self.assertIsInstance(res_details["simulation_id"], str)
        self.assertGreater(res_details["expected_final_value"], 0.0)
        self.assertGreater(res_details["percentile_95"], res_details["percentile_5"])

    def test_calculate_value_at_risk_integration(self):
        engine = MonteCarloEngine()
        simulated_returns = [round(random.uniform(-0.05, 0.07), 5) for _ in range(50)]
        confidence_level = 0.95

        var_value = engine.calculate_value_at_risk(simulated_returns, confidence_level=confidence_level)
        self.assertIsInstance(var_value, (int, float))

    def test_apply_stress_test_integration(self):
        engine = MonteCarloEngine()
        stress_payload = {
            "portfolio_id": self.portfolio_id,
            "shock_percentage": round(random.uniform(-0.3, -0.1), 2)
        }

        stress_result = engine.apply_stress_test(stress_payload)
        self.assertIsInstance(stress_result, (dict, type(None)))


if __name__ == "__main__":
    unittest.main()