import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_monte_carlo_engine import run_monte_carlo_stress_simulation
from skills.db_storage import save_simulation_results, get_simulation_results
from skills.market_portfolio_valuation import calculate_portfolio_value
from skills.market_parser import fetch_asset_historical_data

class TestMarketPortfolioStressMonteCarloEngineIntegration(unittest.TestCase):

    def test_monte_carlo_stress_pipeline_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        asset_count = random.randint(2, 5)
        assets = [f"ASSET_{uuid.uuid4().hex[:4].upper()}" for _ in range(asset_count)]

        weights = [random.uniform(0.1, 0.8) for _ in range(asset_count)]
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        portfolio_composition = dict(zip(assets, normalized_weights))

        simulations_count = random.choice([500, 1000, 2000])
        time_horizon_days = random.randint(30, 90)

        for asset in assets:
            raw_market_data = fetch_asset_historical_data(asset)
            self.assertIsNotNone(raw_market_data)

        initial_valuation = calculate_portfolio_value(portfolio_id, portfolio_composition)
        self.assertGreater(initial_valuation, 0.0)

        simulation_output = run_monte_carlo_stress_simulation(
            portfolio_id=portfolio_id,
            composition=portfolio_composition,
            simulations=simulations_count,
            horizon_days=time_horizon_days
        )

        self.assertIn("simulation_id", simulation_output)
        generated_sim_id = simulation_output["simulation_id"]
        self.assertTrue(isinstance(generated_sim_id, str))
        self.assertTrue(len(generated_sim_id) > 0)

        self.assertIn("stress_var_95", simulation_output)
        self.assertIn("max_drawdown_expected", simulation_output)
        self.assertGreaterEqual(simulation_output["stress_var_95"], 0.0)

        save_simulation_results(generated_sim_id, simulation_output)

        persisted_data = get_simulation_results(generated_sim_id)
        self.assertIsNotNone(persisted_data)
        self.assertEqual(persisted_data["portfolio_id"], portfolio_id)
        self.assertEqual(persisted_data["simulations"], simulations_count)
        self.assertEqual(persisted_data["horizon_days"], time_horizon_days)

if __name__ == "__main__":
    unittest.main()