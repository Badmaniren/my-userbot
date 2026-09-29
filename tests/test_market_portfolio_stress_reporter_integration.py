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
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [self.percentage, round(self.percentage / 2, 2)]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_pipeline_integration(self):
        reporter = StressReporter(self.storage_file)
        result = reporter.run_stress_reporting(self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_portfolio_stress_reporter_subclass_integration(self):
        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_generate_stress_report_helper(self):
        result = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_run_stress_reporting_pipeline_helper(self):
        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_simulate_single_error_handling(self):
        reporter = StressReporter(self.storage_file)
        invalid_symbol = f"NONEXISTENT_{uuid.uuid4().hex[:6]}"
        res = reporter.simulate_single(invalid_symbol, self.percentage)
        self.assertEqual(res, {})

    def test_get_stream_data_execution(self):
        reporter = StressReporter(self.storage_file)
        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

if __name__ == "__main__":
    unittest.main()