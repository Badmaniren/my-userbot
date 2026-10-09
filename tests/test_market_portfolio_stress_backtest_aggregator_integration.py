import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_backtest_aggregator import aggregate_stress_backtest_report


class TestMarketPortfolioStressBacktestAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_market_storage_{uuid.uuid4().hex}.json"

        # Заполним временный файл минимально необходимыми данными для симулятора и пайплайна
        import json
        initial_data = {
            "symbols": {
                "TEST": {
                    "price": round(random.uniform(100.0, 500.0), 2),
                    "volatility": round(random.uniform(0.1, 0.5), 2)
                }
            }
        }
        with open(self.storage_file, "w") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_aggregate_stress_backtest_report_integration(self):
        symbol = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        percentage = round(random.uniform(-0.3, -0.05), 2)
        shifts_count = random.randint(3, 7)
        shifts = [round(random.uniform(-0.2, 0.2), 2) for _ in range(shifts_count)]

        report = aggregate_stress_backtest_report(
            storage_file=self.storage_file,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts
        )

        self.assertIsInstance(report, dict)
        self.assertIn("symbol", report)
        self.assertEqual(report["symbol"], symbol)
        self.assertIn("pipeline_results", report)
        self.assertIn("simulation_results", report)
        self.assertIn("aggregated_metrics", report)


if __name__ == "__main__":
    unittest.main()