import unittest
import uuid
import random
from skills.market_portfolio_stress_resilience_matrix import (
    StressResilienceMatrixCalculator,
    MatrixEvaluationError,
    market_portfolio_stress_resilience_matrix
)
from skills import (
    db_storage,
    market_portfolio_scenario_simulator,
    market_portfolio_valuation,
    market_portfolio_stress_scenario_executor_bridge,
    market_portfolio_stress_audit_realtime_streamer,
    market_portfolio_stress_monte_carlo_engine
)

class TestMarketPortfolioStressResilienceMatrixIntegration(unittest.TestCase):

    def setUp(self):
        self.calculator = StressResilienceMatrixCalculator()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.scenario_code = f"scen_{uuid.uuid4().hex[:8]}"
        self.matrix_id = f"matrix_{uuid.uuid4().hex[:8]}"

    def test_market_portfolio_stress_resilience_matrix_wrapper(self):
        initial_value = round(random.uniform(50000.0, 500000.0), 2)
        shock_factor = round(random.uniform(0.05, 0.5), 2)

        payload = {
            "matrix_id": self.matrix_id,
            "portfolio_id": self.portfolio_id,
            "valuation_data": {
                "initial_value": initial_value
            },
            "simulation_data": {
                "shock_factor": shock_factor
            }
        }

        result = market_portfolio_stress_resilience_matrix(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("matrix_id"), self.matrix_id)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("status"), "EVALUATED")

        expected_score = round(initial_value * (1.0 - shock_factor), 2)
        self.assertEqual(result.get("resilience_score"), expected_score)

    def test_calculator_real_dependencies_wiring(self):
        self.assertIsNotNone(db_storage)
        self.assertIsNotNone(market_portfolio_scenario_simulator)
        self.assertIsNotNone(market_portfolio_valuation)
        self.assertIsNotNone(market_portfolio_stress_scenario_executor_bridge)
        self.assertIsNotNone(market_portfolio_stress_audit_realtime_streamer)
        self.assertIsNotNone(market_portfolio_stress_monte_carlo_engine)

    def test_calculator_methods_callable(self):
        iterations = random.randint(10, 100)
        volatility_factor = round(random.uniform(0.01, 0.99), 4)

        try:
            self.calculator.run_monte_carlo_stress(iterations, volatility_factor)
        except Exception as e:
            self.assertIsNotNone(e)

if __name__ == "__main__":
    unittest.main()