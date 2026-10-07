import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import PortfolioStressReporter, StressReporter, generate_stress_report, run_stress_reporting_pipeline

class TestMarketPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.db"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.shifts = [round(random.uniform(-0.5, 0.5), 2), round(random.uniform(-0.5, 0.5), 2)]
        self.percentage = round(random.uniform(-0.2, 0.2), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_full_pipeline(self):
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

    def test_portfolio_stress_reporter_inheritance(self):
        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)

    def test_generate_stress_report_function(self):
        result = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(result["tabular_report"][0]["shifts"], [self.percentage])

    def test_run_stress_reporting_pipeline_function(self):
        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(result, dict)
        self.assertIn("base_report", result)
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)

    def test_simulate_single_exception_handling(self):
        reporter = StressReporter(self.storage_file)
        res = reporter.simulate_single(f"NONEXISTENT_{uuid.uuid4()}", self.percentage)
        self.assertIsInstance(res, dict)

    def test_get_stream_data(self):
        reporter = StressReporter(self.storage_file)
        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

if __name__ == "__main__":
    unittest.main()