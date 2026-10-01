import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import (
    StressReporter,
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline
)

class TestMarketPortfolioStressReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [self.percentage, round(self.percentage / 2, 2)]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_integration_pipeline(self):
        reporter = StressReporter(self.storage_file)
        result = reporter.run_stress_reporting(self.symbol, self.shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)
        self.assertIn("compact_text_report", result)
        self.assertIn("tabular_report", result)
        self.assertIn("chart_export", result)

        self.assertIn(self.symbol, result["compact_text_report"])
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)
        self.assertEqual(result["chart_export"]["type"], "line")
        self.assertEqual(result["chart_export"]["data"], result["simulation_results"])

    def test_portfolio_stress_reporter_subclass(self):
        pipeline_reporter = PortfolioStressReporter(self.storage_file)
        result = pipeline_reporter.run_stress_report(self.symbol, self.shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_generate_stress_report_helper(self):
        result = generate_stress_report(self.storage_file, self.symbol, self.percentage)

        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("tabular_report", result)
        self.assertEqual(result["tabular_report"][0]["shifts"], [self.percentage])

    def test_run_stress_reporting_pipeline_helper(self):
        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)

        self.assertIsInstance(result, dict)
        self.assertIn("chart_export", result)
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)

    def test_simulate_single_and_stream_data(self):
        reporter = StressReporter(self.storage_file)
        single_res = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(single_res, (dict, list, type(None)))

        stream_data = reporter.get_stream_data()
        self.assertIsInstance(stream_data, (dict, list, type(None)))


if __name__ == "__main__":
    unittest.main()