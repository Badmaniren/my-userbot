import unittest
import os
import uuid
import random
import tempfile

from skills.market_portfolio_stress_backtest_runner import run_stress_backtest_pipeline, MarketPortfolioStressBacktester
from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline

class TestMarketPortfolioStressBacktestRunnerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.data_filepath = os.path.join(self.test_dir.name, f"test_market_data_{uuid.uuid4().hex}.csv")

        with open(self.data_filepath, "w", encoding="utf-8") as f:
            f.write("date,open,high,low,close,volume\n")
            base_price = 100.0
            for i in range(30):
                change = random.uniform(-2.0, 2.0)
                base_price += change
                f.write(f"2023-01-{i+1:02d},{base_price},{base_price+1},{base_price-1},{base_price},{random.randint(1000, 5000)}\n")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_stress_backtest_runner_integration(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(5.0, 25.0), 2)
        shifts = random.randint(1, 5)
        initial_capital = round(random.uniform(10000.0, 50000.0), 2)

        strategy_params = {
            "sma_short": random.randint(3, 5),
            "sma_long": random.randint(10, 15)
        }

        pipeline_result = run_stress_backtest_pipeline(
            filepath=self.data_filepath,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts,
            initial_capital=initial_capital,
            strategy_params=strategy_params
        )

        self.assertIsNotNone(pipeline_result)
        self.assertIn("backtest_summary", pipeline_result)
        self.assertIn("stress_results", pipeline_result)
        self.assertIn("validation_report", pipeline_result)

        backtester = MarketPortfolioBacktester(filepath=self.data_filepath)
        loaded_data = backtester.load_data(self.data_filepath)
        self.assertIsNotNone(loaded_data)

        stress_pipeline = PortfolioStressScenarioPipeline(storage_file=self.data_filepath)
        stress_execution = stress_pipeline.execute(symbol=symbol, percentage=percentage, shifts=shifts)
        self.assertIsNotNone(stress_execution)

        runner = MarketPortfolioStressBacktester(filepath=self.data_filepath)
        run_output = runner.run_complete_pipeline(
            symbol=symbol,
            percentage=percentage,
            shifts=shifts,
            initial_capital=initial_capital,
            strategy_params=strategy_params
        )

        self.assertIsInstance(run_output, dict)
        self.assertTrue(len(run_output) > 0)
        self.assertIn("status", run_output)
        self.assertEqual(run_output["status"], "SUCCESS")

if __name__ == "__main__":
    unittest.main()