import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_monte_carlo_engine import run_monte_carlo_stress_test
from skills.db_storage import save_stress_test_result, get_stress_test_result
from skills.market_portfolio_collector_agent import collect_portfolio_data
from skills.market_portfolio_valuation import calculate_portfolio_value
from skills.market_portfolio_scenario_simulator import generate_stress_scenario

class TestMarketPortfolioStressMonteCarloEngineIntegration(unittest.TestCase):
    def test_monte_carlo_stress_engine_integration_real_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_capital = round(random.uniform(50000.0, 500000.0), 2)
        simulations_count = random.randint(100, 1000)
        volatility = round(random.uniform(0.15, 0.45), 4)

        raw_data = collect_portfolio_data(portfolio_id=portfolio_id, capital=initial_capital)
        self.assertIsNotNone(raw_data)

        valuation = calculate_portfolio_value(portfolio_data=raw_data)
        self.assertGreater(valuation, 0.0)

        scenario = generate_stress_scenario(volatility_factor=volatility)
        self.assertIsInstance(scenario, dict)

        engine_result = run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            portfolio_value=valuation,
            scenario_params=scenario,
            iterations=simulations_count
        )

        self.assertIn("simulation_id", engine_result)
        sim_id = engine_result["simulation_id"]
        self.assertIsInstance(sim_id, str)
        self.assertTrue(len(sim_id) > 0)

        self.assertIn("var_95", engine_result)
        self.assertIn("expected_shortfall", engine_result)
        self.assertIsInstance(engine_result["var_95"], float)

        save_success = save_stress_test_result(simulation_id=sim_id, result_data=engine_result)
        self.assertTrue(save_success)

        stored_data = get_stress_test_result(simulation_id=sim_id)
        self.assertIsInstance(stored_data, dict)
        self.assertEqual(stored_data.get("simulation_id"), sim_id)
        self.assertEqual(stored_data.get("portfolio_id"), portfolio_id)

if __name__ == "__main__":
    unittest.main()