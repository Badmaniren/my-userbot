import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter, generate_stress_report, run_stress_reporting_pipeline

class TestPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_portfolio_storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.shift_pct = round(random.uniform(-0.5, 0.5), 4)
        self.shifts = [self.shift_pct, round(self.shift_pct * 2, 4)]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_stress_reporter_pipeline_integration(self):
        reporter = StressReporter(self.storage_file)
        result = reporter.run_stress_reporting(self.symbol, self.shifts)
        
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)
        self.assertIsInstance(result["simulation_results"], (dict, list))

    def test_portfolio_stress_reporter_subclass(self):
        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIn(" simulation_results" if " simulation_results" in result else "simulation_results", result)

    def test_generate_stress_report_helper(self):
        result = generate_stress_report(self.storage_file, self.symbol, self.shift_pct)
        self.assertIsInstance(result, dict)
        self.assertTrue(len(result) > 0)

    def test_run_stress_reporting_pipeline_helper(self):
        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)

    def test_simulate_single_and_stream(self):
        reporter = StressReporter(self.storage_file)
        single_res = reporter.simulate_single(self.symbol, self.shift_pct)
        self.assertIsInstance(single_res, (dict, list, type(None)))
        
        stream_data = reporter.get_stream_data()
        self.assertIsInstance(stream_data, (dict, list, type(None)))

if __name__ == "__main__":
    unittest.main()