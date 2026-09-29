import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter, generate_stress_report, run_stress_reporting_pipeline

class TestPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.shifts = [float(random.randint(-20, -5)), float(random.randint(5, 20))]
        self.percentage = float(random.randint(-15, 15))

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_stress_reporter_integration_flow(self):
        reporter = StressReporter(self.storage_file)
        result = reporter.run_stress_reporting(self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

        single_sim = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(single_sim, dict)

        stream_data = reporter.get_stream_data()
        self.assertIsInstance(stream_data, (list, dict, type(None)))

    def test_portfolio_stress_reporter_pipeline(self):
        pipeline_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(pipeline_result, dict)
        self.assertIn("simulation_results", pipeline_result)

    def test_generate_stress_report_wrapper(self):
        gen_result = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        self.assertIsInstance(gen_result, dict)
        self.assertIn("simulation_results", gen_result)

if __name__ == "__main__":
    unittest.main()