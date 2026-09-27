import unittest
import uuid
import random
from skills.market_portfolio_monte_carlo import (
    MonteCarloConfig,
    MarketPortfolioMonteCarlo,
    market_portfolio_monte_carlo
)
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_slippage_model import market_portfolio_slippage_model
from skills.db_storage import db_storage

class RealScenarioSimulatorAdapter:
    def generate_scenarios(self):
        sim_id = str(uuid.uuid4())
        raw = market_portfolio_scenario_simulator({"simulation_id": sim_id, "iterations": 5})
        scenarios = []
        if isinstance(raw, dict) and "scenarios" in raw:
            for sc in raw["scenarios"]:
                scenarios.append({"asset_returns": sc.get("asset_returns", {"AAPL": random.uniform(-0.05, 0.05)})})
        else:
            scenarios.append({"asset_returns": {"AAPL": 0.02, "GOOGL": 0.03}})
        return scenarios

class RealSlippageModelAdapter:
    def estimate_slippage(self, portfolio):
        res = market_portfolio_slippage_model({"portfolio": portfolio, "amount": portfolio.get("total_value", 1000)})
        if isinstance(res, dict):
            return res.get("slippage", 0.001)
        return 0.001

class TestMarketPortfolioMonteCarloIntegration(unittest.TestCase):
    def test_full_monte_carlo_pipeline_integration(self):
        rand_suffix = uuid.uuid4().hex[:8]
        portfolio_id = f"port_{rand_suffix}"

        portfolio = {
            "portfolio_id": portfolio_id,
            "total_value": 150000.0,
            "assets": [
                {"ticker": "AAPL", "weight": 0.6, "expected_return": 0.08},
                {"ticker": "GOOGL", "weight": 0.4, "expected_return": 0.10}
            ]
        }

        config = MonteCarloConfig(
            num_simulations=10,
            time_horizon=5,
            confidence_level=0.95,
            random_seed=42,
            enable_slippage=True
        )

        scenario_sim = RealScenarioSimulatorAdapter()
        slippage_mod = RealSlippageModelAdapter()

        mpmc = MarketPortfolioMonteCarlo(
            scenario_simulator=scenario_sim,
            slippage_model=slippage_mod,
            config=config
        )

        result = mpmc.run_simulation(portfolio)

        self.assertIsNotNone(result)
        self.assertTrue(result.simulation_id.startswith("sim_"))
        self.assertGreater(len(result.returns), 0)
        self.assertIsInstance(result.mean_return, float)
        self.assertIsInstance(result.var, float)
        self.assertIsInstance(result.cvar, float)
        self.assertIsInstance(result.max_drawdown, float)

        stress_res = mpmc.run_stress_scenario(portfolio, market_shock=-0.25)
        self.assertEqual(stress_res["shock_factor"], -0.25)
        self.assertEqual(stress_res["portfolio_id"], portfolio_id)

        input_payload = {
            "portfolio_id": portfolio_id,
            "iterations": 15,
            "scenarios": [
                {"portfolio_return": 0.01},
                {"portfolio_return": -0.02},
                {"portfolio_return": 0.04}
            ]
        }

        func_result = market_portfolio_monte_carlo(input_payload)
        self.assertIn("simulation_id", func_result)
        self.assertEqual(func_result["portfolio_id"], portfolio_id)
        self.assertIn("VaR_95", func_result)

        db_check = db_storage("get", {"table": "monte_carlo_results", "id": func_result["simulation_id"]})
        self.assertIsNotNone(db_check)

if __name__ == "__main__":
    unittest.main()