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
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.shifts = [round(random.uniform(-0.5, 0.5), 4) for _ in range(3)]
        self.percentage = round(random.uniform(-0.2, 0.2), 4)

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
        self.assertIsInstance(single_sim, (dict, list, float, int))

        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

    def test_portfolio_stress_reporter_subclass(self):
        pipeline_reporter = PortfolioStressReporter(self.storage_file)
        report = pipeline_reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIsInstance(report, dict)
        self.assertIn("simulation_results", report)
        self.assertIn("base_report", report)

    def test_functional_wrappers_integration(self):
        gen_result = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        self.assertIsInstance(gen_result, dict)
        self.assertIn("simulation_results", gen_result)
        self.assertIn("base_report", gen_result)

        pipeline_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(pipeline_result, dict)
        self.assertIn("simulation_results", pipeline_result)
        self.assertIn("base_report", pipeline_result)


if __name__ == "__main__":
    unittest.main()