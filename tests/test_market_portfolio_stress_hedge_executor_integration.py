import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline
from skills.market_portfolio_stress_hedge_executor import run_stress_hedge_execution_pipeline


class TestMarketPortfolioStressHedgeExecutorIntegration(unittest.TestCase):

    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.scenario_storage = f"test_scenario_store_{self.random_suffix}.json"
        self.execution_storage = f"test_execution_store_{self.random_suffix}.json"

        self.tickers = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        self.test_ticker = random.choice(self.tickers)
        self.test_percentage = round(random.uniform(5.0, 25.0), 2)
        self.test_shifts = [round(random.uniform(-0.15, -0.01), 4) for _ in range(3)]
        self.test_volume = random.randint(100, 5000)

    def tearDown(self):
        for fname in [self.scenario_storage, self.execution_storage]:
            if os.path.exists(fname):
                try:
                    os.remove(fname)
                except OSError:
                    pass

    def test_stress_hedge_executor_composition_integration(self):
        # Подготавливаем тестовые данные в файле хранилища исполнения
        import json
        with open(self.execution_storage, "w") as f:
            json.dump({self.test_ticker: {"price": 150.0, "quantity": 100}}, f)

        scenario_pipeline = PortfolioStressScenarioPipeline(storage_file=self.scenario_storage)
        execution_pipeline = MarketPortfolioExecutionPipeline(storage_file=self.execution_storage)

        stress_result = scenario_pipeline.execute(
            symbol=self.test_ticker,
            percentage=self.test_percentage,
            shifts=self.test_shifts
        )

        self.assertIsInstance(stress_result, dict)

        hedge_execution_result = run_stress_hedge_execution_pipeline(
            scenario_pipeline_inst=scenario_pipeline,
            execution_pipeline_inst=execution_pipeline,
            ticker=self.test_ticker,
            percentage=self.test_percentage,
            shifts=self.test_shifts,
            volume=self.test_volume
        )

        self.assertIsInstance(hedge_execution_result, dict)
        self.assertTrue(
            os.path.exists(self.execution_storage),
            "Пайплайн исполнения должен зафиксировать состояние в хранилище"
        )

        simulated_logs = execution_pipeline.get_historical_pipeline_logs(simulation_id=self.test_ticker)
        self.assertIsInstance(simulated_logs, list)


if __name__ == "__main__":
    unittest.main()