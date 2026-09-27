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
        self.storage_file = f"test_portfolio_storage_{uuid.uuid4().hex}.db"
        self.symbol = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = [round(random.uniform(-0.5, 0.5), 4) for _ in range(3)]
        self.percentage = round(random.uniform(-0.3, 0.3), 4)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_end_to_end_integration(self):
        reporter = StressReporter(self.storage_file)
        
        result = reporter.run_stress_reporting(self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)
        
        single_sim = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(single_sim, (dict, list, float, int, type(None)))
        
        stream_data = reporter.get_stream_data()
        self.assertIsInstance(stream_data, (dict, list, type(None)))

    def test_portfolio_stress_reporter_subclass_pipeline(self):
        pipeline_reporter = PortfolioStressReporter(self.storage_file)
        
        report = pipeline_reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIsInstance(report, dict)
        self.assertIn("simulation_results", report)
        self.assertIn("base_report", report)

    def test_functional_wrappers_integration(self):
        func_report = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        self.assertIsInstance(func_report, dict)
        self.assertIn("simulation_results", func_report)
        self.assertIn("base_report", func_report)

        pipeline_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(pipeline_result, dict)
        self.assertIn("simulation_results", pipeline_result)
        self.assertIn("base_report", pipeline_result)

if __name__ == "__main__":
    unittest.main()