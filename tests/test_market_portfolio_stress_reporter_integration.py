import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter, generate_stress_report, run_stress_reporting_pipeline

class TestMarketPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.percentage = round(random.uniform(5.0, 50.0), 2)
        self.shifts = [self.percentage, round(self.percentage * 1.5, 2)]

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

        single_sim = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(single_sim, (dict, list))

        stream_data = reporter.get_stream_data()
        self.assertIsInstance(stream_data, (dict, list, str, type(None)))

    def test_portfolio_stress_reporter_subclass(self):
        pipeline_reporter = PortfolioStressReporter(self.storage_file)
        report = pipeline_reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIsInstance(report, dict)
        self.assertIn(" simulation_results".strip(), report)
        self.assertIn(" base_report".strip(), report)

    def test_functional_wrappers_integration(self):
        functional_result = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        self.assertIsInstance(functional_result, dict)
        self.assertIn("simulation_results", functional_result)

        pipeline_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(pipeline_result, dict)
        self.assertIn("base_report", pipeline_result)

if __name__ == "__main__":
    unittest.main()