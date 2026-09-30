import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter, generate_stress_report, run_stress_reporting_pipeline

import json

class TestPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"
        self.test_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.test_shifts = [round(random.uniform(-0.2, 0.2), 4) for _ in range(random.randint(1, 3))]
        self.test_percentage = round(random.uniform(-0.1, 0.1), 4)

        portfolio_data = {
            self.test_symbol: {
                "current_price": 100.0,
                "quantity": 10.0
            }
        }
        with open(self.storage_file, "w") as f:
            json.dump(portfolio_data, f)

        self.reporter = StressReporter(self.storage_file)
        self.portfolio_reporter = PortfolioStressReporter(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_run_stress_reporting_integration(self):
        result = self.reporter.run_stress_reporting(self.test_symbol, self.test_shifts)
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)
        self.assertIn("retrospective_evaluation", result)
        self.assertIn("backtest_evaluation", result)

    def test_simulate_single_integration(self):
        sim_result = self.reporter.simulate_single(self.test_symbol, self.test_percentage)
        self.assertIsNotNone(sim_result)

    def test_get_stream_data_integration(self):
        stream_data = self.reporter.get_stream_data()
        self.assertIsInstance(stream_data, (dict, list, str, type(None)))

    def test_portfolio_stress_reporter_inheritance(self):
        result = self.portfolio_reporter.run_stress_report(self.test_symbol, self.test_shifts)
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("retrospective_evaluation", result)

    def test_generate_stress_report_function(self):
        result = generate_stress_report(self.storage_file, self.test_symbol, self.test_percentage)
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)

    def test_run_stress_reporting_pipeline_function(self):
        result = run_stress_reporting_pipeline(self.storage_file, self.test_symbol, self.test_shifts)
        self.assertIsInstance(result, dict)
        self.assertIn("backtest_evaluation", result)

if __name__ == "__main__":
    unittest.main()