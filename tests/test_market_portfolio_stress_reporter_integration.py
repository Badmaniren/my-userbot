import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter, generate_stress_report, run_stress_reporting_pipeline

class TestIntegrationPortfolioStressReporter(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shift = round(random.uniform(-0.5, 0.5), 4)
        self.shifts = [self.shift, round(self.shift * 2, 4)]

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

        single_sim = reporter.simulate_single(self.symbol, self.shift)
        self.assertIsInstance(single_sim, dict)

        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

    def test_portfolio_stress_reporter_subclass(self):
        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)

    def test_convenience_functions(self):
        res_generate = generate_stress_report(self.storage_file, self.symbol, self.shift)
        self.assertIsInstance(res_generate, dict)
        self.assertIn("simulation_results", res_generate)

        res_pipeline = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(res_pipeline, dict)
        self.assertIn("simulation_results", res_pipeline)

if __name__ == "__main__":
    unittest.main()