import unittest
import uuid
import random
from skills import market_portfolio_stress_monte_carlo_resiliency_engine, db_storage

class TestMarketPortfolioStressMonteCarloResiliencyEngineIntegration(unittest.TestCase):
    def test_monte_carlo_simulation_and_persistence_integration(self):
        engine = market_portfolio_stress_monte_carlo_resiliency_engine.MarketPortfolioStressMonteCarloResiliencyEngine()

        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        iterations = random.randint(500, 5000)
        liquidity_shock = round(random.uniform(0.01, 0.25), 4)

        simulation_result = engine.run_monte_carlo_simulation(portfolio_id, iterations, liquidity_shock)

        self.assertIsInstance(simulation_result, dict)
        self.assertEqual(simulation_result["portfolio_id"], portfolio_id)
        self.assertIn("resiliency_score", simulation_result)
        self.assertIn("var_99", simulation_result)

        engine.persist_simulation_state(portfolio_id, simulation_result)

        func_entry = market_portfolio_stress_monte_carlo_resiliency_engine.market_portfolio_stress_monte_carlo_resiliency_engine({
            "simulations": iterations,
            "portfolio_id": portfolio_id
        })

        self.assertIsInstance(func_entry, dict)
        self.assertEqual(func_entry["simulations_run"], iterations)
        self.assertIn("resiliency_score", func_entry)

if __name__ == "__main__":
    unittest.main()