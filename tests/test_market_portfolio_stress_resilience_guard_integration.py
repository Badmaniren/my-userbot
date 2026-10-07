import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_resilience_guard import market_portfolio_stress_resilience_guard
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.db_storage import db_storage

class TestMarketPortfolioStressResilienceGuardIntegration(unittest.TestCase):
    def test_stress_resilience_guard_pipeline_real_execution(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulation_seed = random.randint(1000, 99999)
        shock_factor = round(random.uniform(0.05, 0.45), 4)

        simulator_result = market_portfolio_scenario_simulator(
            portfolio_id=portfolio_id,
            shock_factor=shock_factor,
            seed=simulation_seed
        )

        self.assertIsInstance(simulator_result, dict)
        self.assertIn("scenario_id", simulator_result)

        mc_result = market_portfolio_stress_monte_carlo_engine(
            scenario_id=simulator_result["scenario_id"],
            iterations=100
        )

        self.assertIsInstance(mc_result, dict)
        self.assertIn("metrics", mc_result)

        guard_result = market_portfolio_stress_resilience_guard(
            portfolio_id=portfolio_id,
            simulation_metrics=mc_result["metrics"]
        )

        self.assertIsInstance(guard_result, dict)
        self.assertIn("resilience_status", guard_result)
        self.assertEqual(guard_result.get("portfolio_id"), portfolio_id)

        stored_data = db_storage(
            action="get",
            key=f"resilience_{portfolio_id}"
        )
        self.assertIsNotNone(stored_data)

if __name__ == "__main__":
    unittest.main()