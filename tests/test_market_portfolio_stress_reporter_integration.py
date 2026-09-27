import json
import os
import random
import shutil
import tempfile
import unittest
import uuid

from skills.market_portfolio_stress_reporter import (
    PortfolioStressReporter,
    StressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline,
)


class TestMarketPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.storage_file = os.path.join(self.test_dir, f"portfolio_{uuid.uuid4().hex}.json")
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_price = round(random.uniform(10.0, 500.0), 2)
        self.random_qty = random.randint(5, 50)

        seed_data = {
            "portfolio": {
                self.random_symbol: {
                    "symbol": self.random_symbol,
                    "shares": self.random_qty,
                    "amount": self.random_qty,
                    "buy_price": self.random_price,
                    "current_price": self.random_price,
                    "price": self.random_price,
                }
            },
            "stream": [
                {
                    "symbol": self.random_symbol,
                    "price": self.random_price,
                    "event_id": str(uuid.uuid4()),
                }
            ],
            "symbols": {
                self.random_symbol: {
                    "price": self.random_price,
                }
            },
        }

        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(seed_data, f)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_stress_reporter_run_reporting_and_stream(self):
        reporter = StressReporter(self.storage_file)

        shift_1 = round(random.uniform(-0.4, -0.05), 3)
        shift_2 = round(random.uniform(0.05, 0.4), 3)
        shifts = [shift_1, shift_2]

        report = reporter.run_stress_reporting(self.random_symbol, shifts)

        self.assertIsInstance(report, dict)
        self.assertIn("simulation_results", report)
        self.assertIn("base_report", report)

        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

    def test_stress_reporter_simulate_single(self):
        reporter = StressReporter(self.storage_file)
        random_percentage = round(random.uniform(-0.35, 0.35), 3)

        single_result = reporter.simulate_single(self.random_symbol, random_percentage)
        self.assertIsNotNone(single_result)

    def test_portfolio_stress_reporter_subclass_and_run(self):
        self.assertTrue(issubclass(PortfolioStressReporter, StressReporter))

        reporter = PortfolioStressReporter(self.storage_file)
        shift = round(random.uniform(-0.25, 0.25), 3)

        result = reporter.run_stress_report(self.random_symbol, [shift])

        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_generate_stress_report_helper(self):
        random_percentage = round(random.uniform(-0.5, 0.5), 3)

        result = generate_stress_report(self.storage_file, self.random_symbol, random_percentage)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_run_stress_reporting_pipeline_helper(self):
        random_shifts = [
            round(random.uniform(-0.3, -0.1), 3),
            round(random.uniform(0.1, 0.3), 3),
        ]

        result = run_stress_reporting_pipeline(self.storage_file, self.random_symbol, random_shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)


if __name__ == "__main__":
    unittest.main()