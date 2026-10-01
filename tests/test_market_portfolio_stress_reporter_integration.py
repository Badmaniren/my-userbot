import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter, generate_stress_report, run_stress_reporting_pipeline

class TestIntegrationPortfolioStressReporter(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
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

        single_sim = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(single_sim, (dict, list, float, int))

        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

    def test_portfolio_stress_reporter_pipeline(self):
        pipeline_reporter = PortfolioStressReporter(self.storage_file)
        result = pipeline_reporter.run_stress_report(self.symbol, self.shifts)
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_functional_wrappers(self):
        gen_res = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        self.assertIsInstance(gen_res, dict)
        
        pipe_res = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(pipe_res, dict)
        self.assertIn("simulation_results", pipe_res)

if __name__ == "__main__":
    unittest.main()