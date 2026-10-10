import unittest
import uuid
import random
import os
from skills.market_portfolio_predictive_var_hedge_synthesizer import PredictiveVarHedgeSynthesizer

class TestPredictiveVarHedgeSynthesizerIntegration(unittest.TestCase):
    def setUp(self):
        self.db_storage = f":memory:"
        self.synthesizer = PredictiveVarHedgeSynthesizer(
            storage_file=self.db_storage
        )

    def test_synthesize_and_execute_hedge_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        scenario_code = f"SCENARIO_{random.randint(100, 999)}"
        symbol = random.choice(["BTC/USD", "ETH/USD", "AAPL", "TSLA", "EUR/USD"])
        percentage = round(random.uniform(5.0, 95.0), 2)
        portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        simulations = random.randint(100, 1000)
        horizon_days = random.randint(1, 30)
        confidence_level = random.choice([0.95, 0.99])
        iterations = random.randint(10, 100)
        
        scenario_params = {
            "volatility": round(random.uniform(0.1, 0.9), 4),
            "drift": round(random.uniform(-0.05, 0.05), 4)
        }
        shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]

        result = self.synthesizer.synthesize_and_execute_hedge(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            simulations=simulations,
            horizon_days=horizon_days,
            confidence_level=confidence_level,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            iterations=iterations,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertIn("var_metrics", result)
        self.assertIn("hedge_result", result)
        
        var_metrics = result["var_metrics"]
        self.assertEqual(var_metrics.get("portfolio_id"), portfolio_id)
        self.assertEqual(var_metrics.get("scenario_code"), scenario_code)

    def test_synthesize_stress_var_and_hedge_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        symbol = random.choice(["SPY", "QQQ", "GLD"])
        percentage = round(random.uniform(1.0, 50.0), 2)
        portfolio_value = round(random.uniform(50000.0, 500000.0), 2)
        confidence_level = 0.99
        horizon_days = random.randint(5, 60)
        iterations = random.randint(50, 200)
        
        scenario_params = {
            "stress_factor": round(random.uniform(1.5, 3.0), 2)
        }
        shifts = [round(random.uniform(-0.2, 0.2), 4) for _ in range(2)]

        result = self.synthesizer.synthesize_stress_var_and_hedge(
            portfolio_id=portfolio_id,
            portfolio_value=portfolio_value,
            scenario_params=scenario_params,
            confidence_level=confidence_level,
            horizon_days=horizon_days,
            iterations=iterations,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertIn("stress_var_metrics", result)
        self.assertIn("hedge_result", result)

    def test_synthesize_and_simulate_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        scenario_code = f"SIM_{random.randint(1000, 9999)}"
        symbol = "BTC/USDT"
        percentage = round(random.uniform(10.0, 90.0), 2)
        portfolio_value = 123456.78
        simulations = 500
        horizon_days = 10
        confidence_level = 0.95
        scenario_params = {"mode": "monte_carlo"}
        iterations = 50
        shifts = [0.01, -0.02, 0.03]

        result = self.synthesizer.synthesize_and_simulate(
            portfolio_id=portfolio_id,
            scenario_code=scenario_code,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            portfolio_value=portfolio_value,
            simulations=simulations,
            horizon_days=horizon_days,
            confidence_level=confidence_level,
            scenario_params=scenario_params,
            iterations=iterations,
            shifts=shifts
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertIn("var_metrics", result)
        self.assertIn("hedge_result", result)
        self.assertIn("hedge_status", result)
        self.assertIsInstance(result.get("hedge_status"), str)

if __name__ == "__main__":
    unittest.main()