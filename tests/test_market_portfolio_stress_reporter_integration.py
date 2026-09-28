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
        self.shift_val = round(random.uniform(-0.5, 0.5), 4)
        self.shifts = [self.shift_val, round(self.shift_val * 2, 4)]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_integration(self):
        reporter = StressReporter(self.storage_file)
        result = reporter.run_stress_reporting(self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)
        
        single_sim = reporter.simulate_single(self.symbol, self.shift_val)
        self.assertIsInstance(single_sim, (dict, list, type(None)))
        
        stream_data = reporter.get_stream_data()
        self.assertIsInstance(stream_data, (dict, list, str, type(None)))

    def test_portfolio_stress_reporter_subclass(self):
        pipeline_reporter = PortfolioStressReporter(self.storage_file)
        result = pipeline_reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_functional_wrappers_integration(self):
        report_from_func = generate_stress_report(self.storage_file, self.symbol, self.shift_val)
        self.assertIsInstance(report_from_func, dict)
        self.assertIn("simulation_results", report_from_func)
        
        pipeline_from_func = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(pipeline_from_func, dict)
        self.assertIn("base_report", pipeline_from_func)

if __name__ == "__main__":
    unittest.main()