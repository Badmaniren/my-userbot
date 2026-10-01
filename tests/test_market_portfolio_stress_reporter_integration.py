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
        self.storage_file = f"test_portfolio_{uuid.uuid4()}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shift_value = round(random.uniform(-0.25, -0.01), 4)
        self.shifts = [self.shift_value, round(self.shift_value * 2, 4)]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_stress_reporter_flow_without_mocks(self):
        reporter = StressReporter(self.storage_file)
        
        result = reporter.run_stress_reporting(self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_portfolio_stress_reporter_subclass_pipeline(self):
        reporter = PortfolioStressReporter(self.storage_file)
        
        result = reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_functional_wrappers_execution(self):
        gen_result = generate_stress_report(self.storage_file, self.symbol, self.shift_value)
        self.assertIsInstance(gen_result, dict)
        self.assertIn("simulation_results", gen_result)

        pipe_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(pipe_result, dict)
        self.assertIn("base_report", pipe_result)

    def test_simulate_single_and_stream_data(self):
        reporter = StressReporter(self.storage_file)
        
        single_sim = reporter.simulate_single(self.symbol, self.shift_value)
        self.assertIsInstance(single_sim, dict)

        stream_data = reporter.get_stream_data()
        self.assertIsInstance(stream_data, (list, dict, type(None)))


if __name__ == "__main__":
    unittest.main()