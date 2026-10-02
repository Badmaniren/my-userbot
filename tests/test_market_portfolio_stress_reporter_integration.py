import json
import os
import random
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
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4().hex}.json")

        self.random_symbol = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.random_price = round(random.uniform(50.0, 500.0), 2)
        self.random_qty = random.randint(10, 1000)

        initial_storage = {
            "portfolio": {
                self.random_symbol: {
                    "shares": self.random_qty,
                    "buy_price": self.random_price,
                    "current_price": self.random_price,
                }
            },
            "positions": [
                {
                    "symbol": self.random_symbol,
                    "amount": self.random_qty,
                    "price": self.random_price,
                }
            ],
            "market_data": {
                self.random_symbol: {
                    "price": self.random_price,
                    "history": [self.random_price * (1.0 + random.uniform(-0.05, 0.05)) for _ in range(5)],
                }
            },
            "symbols": [self.random_symbol],
            "quotes": {self.random_symbol: self.random_price},
            "events": [],
            "reports": [],
        }

        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_storage, f)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_stress_reporter_run_stress_reporting_end_to_end(self):
        reporter = StressReporter(self.storage_file)

        shift_down = -round(random.uniform(5.0, 25.0), 2)
        shift_up = round(random.uniform(5.0, 25.0), 2)
        shifts = [shift_down, 0.0, shift_up]

        report = reporter.run_stress_reporting(self.random_symbol, shifts)

        self.assertIsInstance(report, dict)
        self.assertIn("simulation_results", report)
        self.assertIn("base_report", report)
        self.assertIn("compact_text_report", report)
        self.assertIn("tabular_report", report)
        self.assertIn("chart_export", report)

        self.assertIn(self.random_symbol, report["compact_text_report"])
        self.assertIn(str(shifts), report["compact_text_report"])

        tabular = report["tabular_report"]
        self.assertIsInstance(tabular, list)
        self.assertEqual(len(tabular), 1)
        self.assertEqual(tabular[0]["symbol"], self.random_symbol)
        self.assertEqual(tabular[0]["shifts"], shifts)
        self.assertEqual(tabular[0]["results"], report["simulation_results"])

        chart = report["chart_export"]
        self.assertEqual(chart["type"], "line")
        self.assertEqual(chart["data"], report["simulation_results"])

    def test_stress_reporter_simulate_single_and_stream_data(self):
        reporter = StressReporter(self.storage_file)
        percentage = round(random.uniform(-15.0, 15.0), 2)

        single_result = reporter.simulate_single(self.random_symbol, percentage)
        self.assertIsInstance(single_result, (dict, list, float, int))

        non_existent_symbol = f"NONEXISTENT_{uuid.uuid4().hex[:8]}"
        empty_result = reporter.simulate_single(non_existent_symbol, percentage)
        self.assertIsInstance(empty_result, (dict, list))

        stream_dump = reporter.get_stream_data()
        self.assertIsNotNone(stream_dump)

    def test_portfolio_stress_reporter_subclass(self):
        portfolio_reporter = PortfolioStressReporter(self.storage_file)
        shift = round(random.uniform(-10.0, 10.0), 2)
        shifts = [shift]

        report = portfolio_reporter.run_stress_report(self.random_symbol, shifts)
        self.assertIsInstance(report, dict)
        self.assertEqual(report["tabular_report"][0]["symbol"], self.random_symbol)
        self.assertEqual(report["tabular_report"][0]["shifts"], shifts)

    def test_standalone_functions_pipeline(self):
        shift_pct = round(random.uniform(-30.0, 30.0), 2)
        gen_result = generate_stress_report(self.storage_file, self.random_symbol, shift_pct)

        self.assertIsInstance(gen_result, dict)
        self.assertEqual(gen_result["tabular_report"][0]["symbol"], self.random_symbol)
        self.assertEqual(gen_result["tabular_report"][0]["shifts"], [shift_pct])

        pipeline_shifts = [round(random.uniform(-20.0, -1.0), 2), round(random.uniform(1.0, 20.0), 2)]
        pipeline_result = run_stress_reporting_pipeline(self.storage_file, self.random_symbol, pipeline_shifts)

        self.assertIsInstance(pipeline_result, dict)
        self.assertEqual(pipeline_result["tabular_report"][0]["symbol"], self.random_symbol)
        self.assertEqual(pipeline_result["tabular_report"][0]["shifts"], pipeline_shifts)
        self.assertIn("chart_export", pipeline_result)


if __name__ == "__main__":
    unittest.main()