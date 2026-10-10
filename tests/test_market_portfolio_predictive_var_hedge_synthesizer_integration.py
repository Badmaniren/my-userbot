import unittest
import uuid
import random
import os
from skills.market_portfolio_predictive_var_hedge_synthesizer import PredictiveVarHedgeSynthesizer

class TestPredictiveVarHedgeSynthesizerIntegration(unittest.TestCase):
    def setUp(self):
        self.synthesizer = PredictiveVarHedgeSynthesizer()
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.request_id = f"req-{uuid.uuid4()}"
        self.scenario_code = f"SCENARIO-{random.randint(100, 999)}"
        self.symbol = random.choice(["BTC-USD", "ETH-USD", "AAPL", "MSFT", "SPY"])
        self.percentage = round(random.uniform(1.0, 25.0), 2)
        self.portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.horizon_days = random.randint(1, 30)
        self.simulations = random.randint(100, 1000)
        self.iterations = random.randint(10, 100)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]
        self.scenario_params = {"volatility_multiplier": round(random.uniform(1.0, 3.0), 2)}

    def test_synthesize_and_execute_hedge_integration(self):
        result = self.synthesizer.synthesize_and_execute_hedge(
            portfolio_id=self.portfolio_id,
            scenario_code=self.scenario_code,
            simulations=self.simulations,
            horizon_days=self.horizon_days,
            confidence_level=self.confidence_level,
            portfolio_value=self.portfolio_value,
            scenario_params=self.scenario_params,
            iterations=self.iterations,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var_metrics", result)
        self.assertIn("hedge_result", result)

    def test_synthesize_stress_var_and_hedge_integration(self):
        result = self.synthesizer.synthesize_stress_var_and_hedge(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.portfolio_value,
            scenario_params=self.scenario_params,
            confidence_level=self.confidence_level,
            horizon_days=self.horizon_days,
            iterations=self.iterations,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("stress_var_metrics", result)
        self.assertIn("hedge_result", result)

    def test_synthesize_and_simulate_integration(self):
        result = self.synthesizer.synthesize_and_simulate(
            portfolio_id=self.portfolio_id,
            scenario_code=self.scenario_code,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            portfolio_value=self.portfolio_value,
            simulations=self.simulations,
            horizon_days=self.horizon_days,
            confidence_level=self.confidence_level,
            scenario_params=self.scenario_params,
            iterations=self.iterations,
            shifts=self.shifts
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var_metrics", result)
        self.assertIn("hedge_result", result)
        self.assertIn("hedge_status", result)

if __name__ == "__main__":
    unittest.main()