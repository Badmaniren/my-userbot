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

class TestPortfolioStressReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = [round(random.uniform(-0.5, 0.5), 2) for _ in range(3)]
        self.percentage = round(random.uniform(-0.3, 0.3), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_pipeline_integration(self):
        reporter = StressReporter(self.storage_file)
        
        # Test run_stress_reporting without mocks between dependencies
        report_data = reporter.run_stress_reporting(self.symbol, self.shifts)
        
        self.assertIsInstance(report_data, dict)
        self.assertIn("simulation_results", report_data)
        self.assertIn("base_report", report_data)

    def test_portfolio_stress_reporter_subclass(self):
        reporter = PortfolioStressReporter(self.storage_file)
        report_data = reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIsInstance(report_data, dict)
        self.assertIn("simulation_results", report_data)
        self.assertIn("base_report", report_data)

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

    def test_simulate_single_and_stream(self):
        reporter = StressReporter(self.storage_file)
        single_res = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(single_res, (dict, list))
        
        stream_data = reporter.get_stream_data()
        self.assertIsInstance(stream_data, (dict, list, type(None)))

if __name__ == "__main__":
    unittest.main()