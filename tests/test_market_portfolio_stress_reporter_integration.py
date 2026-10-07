import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter, generate_stress_report, run_stress_reporting_pipeline

class TestMarketPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.percentage = round(random.uniform(-0.5, 0.5), 4)
        self.shifts = [self.percentage, round(self.percentage * 2, 4)]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_integration_flow(self):
        reporter = StressReporter(self.storage_file)
        result = reporter.run_stress_reporting(self.symbol, self.shifts)
        
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)
        self.assertIn("compact_text_report", result)
        self.assertIn("tabular_report", result)
        self.assertIn("chart_export", result)
        
        self.assertIn(self.symbol, result["compact_text_report"])
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)

    def test_simulate_single_and_stream_data(self):
        reporter = StressReporter(self.storage_file)
        single_result = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(single_result, dict)
        
        stream_data = reporter.get_stream_data()
        self.assertIsInstance(stream_data, (list, dict, type(None)))

    def test_portfolio_stress_reporter_subclass(self):
        pipeline_reporter = PortfolioStressReporter(self.storage_file)
        report = pipeline_reporter.run_stress_report(self.symbol, self.shifts)
        self.assertIsInstance(report, dict)
        self.assertEqual(report["tabular_report"][0]["symbol"], self.symbol)

    def test_functional_helpers_integration(self):
        func_result = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        self.assertIsInstance(func_result, dict)
        self.assertEqual(func_result["tabular_report"][0]["shifts"], [self.percentage])

        pipeline_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(pipeline_result, dict)
        self.assertEqual(pipeline_result["tabular_report"][0]["symbol"], self.symbol)

if __name__ == "__main__":
    unittest.main()