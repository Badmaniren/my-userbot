import unittest
import os
import uuid
import random
import tempfile

from skills.market_portfolio_backtester import MarketPortfolioBacktester
from skills.market_portfolio_predictive_var_engine import PredictiveVarEngine
from skills.market_portfolio_stress_backtest_runner_v2 import StressBacktestRunnerV2

class TestMarketPortfolioStressBacktestRunnerV2Integration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.symbol = f"SYM_{random.choice(['AAPL', 'MSFT', 'GOOGL', 'TSLA'])}"
        self.scenario_code = f"SCENARIO_{uuid.uuid4().hex[:6]}"
        self.initial_capital = round(random.uniform(10000.0, 1000000.0), 2)
        self.portfolio_value = round(random.uniform(50000.0, 5000000.0), 2)
        self.confidence_level = round(random.uniform(0.90, 0.99), 4)
        self.horizon_days = random.randint(1, 30)
        self.iterations = random.randint(100, 1000)

        self.temp_dir = tempfile.TemporaryDirectory()
        self.csv_path = os.path.join(self.temp_dir.name, f"{self.symbol}.csv")

        with open(self.csv_path, "w", encoding="utf-8") as f:
            f.write("Date,Open,High,Low,Close,Volume\n")
            base_price = round(random.uniform(50.0, 500.0), 2)
            for i in range(30):
                date_str = f"2023-01-{i+1:02d}"
                change = random.uniform(-0.05, 0.05)
                base_price = max(1.0, round(base_price * (1.0 + change), 2))
                f.write(f"{date_str},{base_price},{base_price+1},{base_price-1},{base_price},{random.randint(1000, 100000)}\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_end_to_end_stress_backtest_pipeline(self):
        backtester = MarketPortfolioBacktester(filepath=self.csv_path)

        dummy_db_storage = object()
        dummy_extractor = object()
        dummy_anomaly_detector = object()
        var_engine = PredictiveVarEngine(
            db_storage=dummy_db_storage,
            extractor_tool=dummy_extractor,
            market_anomaly_detector=dummy_anomaly_detector
        )

        runner = StressBacktestRunnerV2(
            backtester=backtester,
            predictive_var_engine=var_engine
        )

        self.assertTrue(hasattr(runner, "run_stress_backtest_pipeline"), "Модуль должен содержать метод run_stress_backtest_pipeline")

        strategy_params = {"sma_window": random.randint(5, 20), "threshold": random.uniform(0.01, 0.05)}
        scenario_params = {"shock_magnitude": round(random.uniform(0.1, 0.4), 2)}

        result = runner.run_stress_backtest_pipeline(
            portfolio_id=self.portfolio_id,
            symbol=self.symbol,
            filepath=self.csv_path,
            initial_capital=self.initial_capital,
            strategy_params=strategy_params,
            scenario_code=self.scenario_code,
            portfolio_value=self.portfolio_value,
            scenario_params=scenario_params,
            confidence_level=self.confidence_level,
            horizon_days=self.horizon_days,
            iterations=self.iterations
        )

        self.assertIsInstance(result, dict, "Результат конвейера должен быть словарем")
        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("backtest_summary", result)
        self.assertIn("predictive_var", result)

if __name__ == "__main__":
    unittest.main()