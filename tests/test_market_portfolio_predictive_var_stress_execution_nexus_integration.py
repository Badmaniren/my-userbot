import unittest
import os
import uuid
import random
from skills.market_portfolio_predictive_var_hedge_synthesizer import PredictiveVarHedgeSynthesizer
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline
from skills.market_portfolio_predictive_var_stress_execution_nexus import (
    PredictiveVarStressExecutionNexus,
)


class TestMarketPortfolioPredictiveVarStressExecutionNexusIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_nexus_storage_{uuid.uuid4()}.db"
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.request_id = str(uuid.uuid4())
        self.symbol = random.choice(["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"])
        self.volume = random.randint(100, 5000)
        self.portfolio_value = round(random.uniform(100000.0, 1000000.0), 2)
        self.confidence_level = random.choice([0.95, 0.99])
        self.horizon_days = random.randint(1, 30)
        self.iterations = random.randint(100, 1000)
        self.percentage = round(random.uniform(1.0, 10.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]
        self.scenario_params = {"volatility_multiplier": round(random.uniform(1.0, 3.0), 2)}
        self.scenario_code = f"SCENARIO_{uuid.uuid4().hex[:6].upper()}"

        self.execution_pipeline = MarketPortfolioExecutionPipeline(storage_file=self.storage_file)
        self.var_hedge_synthesizer = PredictiveVarHedgeSynthesizer(db_storage=self.storage_file)
        
        self.nexus = PredictiveVarStressExecutionNexus(
            hedge_synthesizer=self.var_hedge_synthesizer,
            execution_pipeline=self.execution_pipeline,
            storage_file=self.storage_file
        )

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_nexus_integration_flow(self):
        self.assertTrue(
            hasattr(self.nexus, "execute_nexus_stress_hedge_pipeline"),
            "Nexus must implement execute_nexus_stress_hedge_pipeline method"
        )

        result = self.nexus.execute_nexus_stress_hedge_pipeline(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.portfolio_value,
            scenario_params=self.scenario_params,
            confidence_level=self.confidence_level,
            horizon_days=self.horizon_days,
            iterations=self.iterations,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts,
            scenario_code=self.scenario_code,
            simulations=self.iterations
        )

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("request_id"), self.request_id)
        
        self.assertTrue(
            os.path.exists(self.storage_file),
            "Integration must persist state and create the storage database file."
        )


if __name__ == "__main__":
    unittest.main()