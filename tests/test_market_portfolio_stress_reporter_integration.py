import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter, generate_stress_report, run_stress_reporting_pipeline

class TestPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = [random.uniform(-0.2, -0.05), random.uniform(0.05, 0.2)]
        self.percentage = random.choice(self.shifts)
        self.reporter = StressReporter(self.storage_file)
        self.pipeline_reporter = PortfolioStressReporter(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_run_stress_reporting_integration(self):
        result = self.reporter.run_stress_reporting(self.symbol, self.shifts)
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)
        self.assertIn("compact_text_report", result)
        self.assertIn("tabular_report", result)
        self.assertIn("chart_export", result)
        self.assertIn(self.symbol, result["compact_text_report"])
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)

    def test_simulate_single_integration(self):
        sim_res = self.reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(sim_res, (dict, type(None)))

    def test_get_stream_data_integration(self):
        stream_data = self.reporter.get_stream_data()
        self.assertIsInstance(stream_data, (list, dict, type(None)))

    def test_portfolio_stress_reporter_inheritance(self):
        result = self.pipeline_reporter.run_stress_report(self.symbol, self.shifts)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)

    def test_generate_stress_report_function(self):
        result = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertEqual(result["tabular_report"][0]["shifts"], [self.percentage])

    def test_run_stress_reporting_pipeline_function(self):
        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(result, dict)
        self.assertIn("chart_export", result)
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)

if __name__ == "__main__":
    unittest.main()