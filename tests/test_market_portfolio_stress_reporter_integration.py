import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter, generate_stress_report, run_stress_reporting_pipeline

class TestPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = [round(random.uniform(-0.5, 0.5), 4) for _ in range(random.randint(1, 3))]
        self.percentage = round(random.uniform(-0.2, 0.2), 4)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_integration(self):
        reporter = StressReporter(self.storage_file)
        report = reporter.run_stress_reporting(self.symbol, self.shifts)
        
        self.assertIsInstance(report, dict)
        self.assertIn("simulation_results", report)
        self.assertIn("base_report", report)
        self.assertIn("compact_text_report", report)
        self.assertIn("tabular_report", report)
        self.assertIn("chart_export", report)
        
        self.assertIn(self.symbol, report["compact_text_report"])
        self.assertEqual(report["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(report["tabular_report"][0]["shifts"], self.shifts)

    def test_portfolio_stress_reporter_subclass(self):
        reporter = PortfolioStressReporter(self.storage_file)
        report = reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIsInstance(report, dict)
        self.assertEqual(report["tabular_report"][0]["symbol"], self.symbol)

    def test_generate_stress_report_function(self):
        report = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        
        self.assertIsInstance(report, dict)
        self.assertIn("simulation_results", report)
        self.assertEqual(report["tabular_report"][0]["shifts"], [self.percentage])

    def test_run_stress_reporting_pipeline_function(self):
        report = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        
        self.assertIsInstance(report, dict)
        self.assertIn("chart_export", report)
        self.assertEqual(report["chart_export"]["data"], report["simulation_results"])

    def test_simulate_single_and_stream(self):
        reporter = StressReporter(self.storage_file)
        single_result = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(single_result, (dict, list, float, int))
        
        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

if __name__ == "__main__":
    unittest.main()