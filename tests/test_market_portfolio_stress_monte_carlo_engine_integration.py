import unittest
import uuid
import random

from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_audit_compliance_hub
from skills import market_portfolio_stress_audit_visualizer
from skills import market_portfolio_stress_monte_carlo_engine


class TestIntegrationMonteCarloStressEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.initial_value = round(random.uniform(50000.0, 200000.0), 2)
        self.volatility = round(random.uniform(0.1, 0.4), 2)
        self.drift = round(random.uniform(-0.05, 0.05), 4)
        
        # Подготовка данных в реальном хранилище без моков
        if hasattr(db_storage, "_in_memory_db") and isinstance(db_storage._in_memory_db, dict):
            db_storage._in_memory_db[self.portfolio_id] = {
                "portfolio_id": self.portfolio_id,
                "initial_value": self.initial_value,
                "volatility": self.volatility,
                "drift": self.drift
            }

    def test_run_simulation_integration(self):
        engine = market_portfolio_stress_monte_carlo_engine.MonteCarloStressEngine()
        simulations = random.randint(100, 300)
        horizon_days = random.randint(5, 30)

        result = engine.run_simulation(self.portfolio_id, simulations=simulations, horizon_days=horizon_days)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("simulation_results", result)
        self.assertIn("var_95", result)
        self.assertIn("cvar_95", result)
        
        # Проверка математического инварианта CVaR >= VaR
        self.assertGreaterEqual(result["cvar_95"], result["var_95"])
        
        # Проверка размера результатов симуляции
        self.assertEqual(len(result["simulation_results"]), simulations)

    def test_run_monte_carlo_stress_test_function(self):
        scenario_params = {
            "volatility": self.volatility,
            "drift": self.drift,
            "horizon_days": random.randint(1, 15)
        }
        iterations = random.randint(100, 250)

        stress_result = market_portfolio_stress_monte_carlo_engine.run_monte_carlo_stress_test(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.initial_value,
            scenario_params=scenario_params,
            iterations=iterations
        )

        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(stress_result.get("initial_value"), self.initial_value)
        self.assertEqual(stress_result.get("iterations"), iterations)
        self.assertIn("simulation_id", stress_result)
        self.assertIn("var_95", stress_result)
        self.assertIn("expected_shortfall", stress_result)
        self.assertGreaterEqual(stress_result["expected_shortfall"], stress_result["var_95"])


if __name__ == "__main__":
    unittest.main()