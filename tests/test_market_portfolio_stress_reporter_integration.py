import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import PortfolioStressReporter, StressReporter, generate_stress_report, run_stress_reporting_pipeline

class TestPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_portfolio_storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-0.5, 0.5), 4)
        self.shifts = [self.percentage, round(self.percentage * 2, 4)]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_pipeline_integration(self):
        reporter = PortfolioStressReporter(self.storage_file)
        result = reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)
        self.assertIn("compact_text_report", result)
        self.assertIn("tabular_report", result)
        self.assertIn("chart_export", result)
        
        self.assertIn(self.symbol, result["compact_text_report"])
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)

    def helper_verify_standalone_functions(self):
        res_single = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        self.assertIsInstance(res_single, dict)
        self.assertIn("simulation_results", res_single)

        res_pipeline = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(res_pipeline, dict)
        self.assertEqual(res_pipeline["tabular_report"][0]["symbol"], self.symbol)

    def test_simulate_single_and_stream(self):
        base_reporter = StressReporter(self.storage_file)
        single_sim = base_reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(single_sim, dict)

        stream_data = base_reporter.get_stream_data()
        self.assertIsInstance(stream_data, (dict, list, str, type(None)))
        
        self.helper_verify_standalone_functions()

if __name__ == "__main__":
    unittest.main()