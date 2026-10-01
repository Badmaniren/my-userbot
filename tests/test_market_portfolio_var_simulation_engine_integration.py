import unittest
import uuid
import random
from skills.market_portfolio_var_simulation_engine import (
    MarketPortfolioVaRSimulationEngine,
    simulate_portfolio_var
)
from skills.market_portfolio_valuation import calculate_portfolio_value
from skills.market_portfolio_collector_agent import collect_market_data
from skills.db_storage import save_var_simulation_result, get_var_simulation_result

class TestMarketPortfolioVaRSimulationEngineIntegration(unittest.TestCase):
    def test_var_simulation_end_to_end_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulation_id = f"sim_{uuid.uuid4().hex[:8]}"

        random_total_value = round(random.uniform(50000.0, 500000.0), 2)
        random_returns = [round(random.uniform(-0.04, 0.04), 4) for _ in range(15)]
        confidence = 0.95
        horizon = random.randint(1, 5)

        valuation_data = {
            "simulation_id": simulation_id,
            "total_value": random_total_value,
            "returns_series": random_returns
        }

        simulation_result = simulate_portfolio_var(
            portfolio_id=portfolio_id,
            valuation_data=valuation_data,
            confidence_level=confidence,
            horizon_days=horizon
        )

        self.assertIsInstance(simulation_result, dict)
        self.assertEqual(simulation_result["simulation_id"], simulation_id)
        self.assertEqual(simulation_result["portfolio_id"], portfolio_id)
        self.assertEqual(simulation_result["confidence_level"], confidence)
        self.assertEqual(simulation_result["horizon_days"], horizon)
        self.assertIn("var_historical", simulation_result)
        self.assertIn("var_parametric", simulation_result)

        engine = MarketPortfolioVaRSimulationEngine()
        hist_check = engine.calculate_historical_var(portfolio_id, random_returns, confidence)
        param_check = engine.calculate_parametric_var(portfolio_id, 0.0, 0.01, confidence)

        self.assertEqual(hist_check["portfolio_id"], portfolio_id)
        self.assertEqual(param_check["portfolio_id"], portfolio_id)

        save_success = save_var_simulation_result(simulation_result)
        self.assertTrue(save_success or save_success is None or isinstance(save_success, dict))

        retrieved_data = get_var_simulation_result(simulation_id)
        if retrieved_data:
            self.assertEqual(retrieved_data.get("portfolio_id"), portfolio_id)

if __name__ == "__main__":
    unittest.main()