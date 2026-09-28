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
        self.storage_file = f"test_market_storage_{uuid.uuid4()}.db"
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

    def test_portfolio_stress_reporter_pipeline(self):
        pipeline_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        
        self.assertIsInstance(pipeline_result, dict)
        self.assertIn("simulation_results", pipeline_result)
        self.assertIn("base_report", pipeline_result)

    def test_generate_stress_report_wrapper(self):
        report = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        
        self.assertIsInstance(report, dict)
        self.assertIn("simulation_results", report)
        self.assertIn("base_report", report)

    def test_single_simulation_and_stream(self):
        reporter = PortfolioStressReporter(self.storage_file)
        sim_single = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(sim_single, (dict, list, type(None)))

        stream_data = reporter.get_stream_data()
        self.assertIsInstance(stream_data, (dict, list, type(None)))

if __name__ == "__main__":
    unittest.main()