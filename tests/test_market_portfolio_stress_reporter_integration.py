import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter, generate_stress_report, run_stress_reporting_pipeline

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

    def test_stress_reporter_integration_flow(self):
        reporter = StressReporter(self.storage_file)
        
        result = reporter.run_stress_reporting(self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_simulate_single_integration_behavior(self):
        reporter = StressReporter(self.storage_file)
        
        sim_result = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(sim_result, (dict, list, type(None)))

    def test_stream_data_retrieval(self):
        reporter = StressReporter(self.storage_file)
        stream_data = reporter.get_stream_data()
        self.assertIsInstance(stream_data, (dict, list, str, type(None)))

    def test_portfolio_stress_reporter_subclass(self):
        portfolio_reporter = PortfolioStressReporter(self.storage_file)
        
        result = portfolio_reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_generate_stress_report_functional(self):
        res = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        self.assertIsInstance(res, dict)
        self.assertIn("simulation_results", res)
        self.assertIn("base_report", res)

    def test_run_stress_reporting_pipeline_functional(self):
        res = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(res, dict)
        self.assertIn("simulation_results", res)
        self.assertIn("base_report", res)

if __name__ == "__main__":
    unittest.main()