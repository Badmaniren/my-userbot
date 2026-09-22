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
        self.storage_file = f"test_storage_{uuid.uuid4()}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [self.percentage, round(self.percentage * 1.5, 2)]

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

        single_sim = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(single_sim, dict)

        stream_data = reporter.get_stream_data()
        self.assertTrue(isinstance(stream_data, (bytes, str, dict, list)))

    def test_portfolio_stress_reporter_subclass(self):
        pipeline_reporter = PortfolioStressReporter(self.storage_file)
        pipeline_result = pipeline_reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIsInstance(pipeline_result, dict)
        self.assertIn("simulation_results", pipeline_result)
        self.assertIn("base_report", pipeline_result)

    def test_functional_wrappers(self):
        res_generated = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        self.assertIsInstance(res_generated, dict)
        self.assertIn("simulation_results", res_generated)

        res_pipelined = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(res_pipelined, dict)
        self.assertIn("base_report", res_pipelined)

if __name__ == "__main__":
    unittest.main()