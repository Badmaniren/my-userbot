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
        self.test_dir = "test_data_storage"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"test_storage_{uuid.uuid4().hex}.db")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [self.percentage, round(self.percentage / 2, 2)]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        if os.path.exists(self.test_dir) and not os.listdir(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_stress_reporter_pipeline_integration(self):
        reporter = StressReporter(self.storage_file)
        result = reporter.run_stress_reporting(self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)
        self.assertIn("compact_text_report", result)
        self.assertIn("tabular_report", result)
        self.assertIn("chart_export", result)
        
        self.assertIn(self.symbol, result["compact_text_report"])
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)

    def test_portfolio_stress_reporter_subclass(self):
        pipeline_reporter = PortfolioStressReporter(self.storage_file)
        pipeline_result = pipeline_reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIsInstance(pipeline_result, dict)
        self.assertIn("simulation_results", pipeline_result)
        self.assertEqual(pipeline_result["tabular_report"][0]["symbol"], self.symbol)

    def test_generate_stress_report_helper(self):
        helper_result = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        
        self.assertIsInstance(helper_result, dict)
        self.assertIn("simulation_results", helper_result)
        self.assertEqual(helper_result["tabular_report"][0]["shifts"], [self.percentage])

    def test_run_stress_reporting_pipeline_helper(self):
        pipeline_func_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        
        self.assertIsInstance(pipeline_func_result, dict)
        self.assertIn("simulation_results", pipeline_func_result)
        self.assertEqual(pipeline_func_result["tabular_report"][0]["symbol"], self.symbol)

    def test_simulate_single_error_handling(self):
        reporter = StressReporter(self.storage_file)
        invalid_symbol = f"NONEXISTENT_{uuid.uuid4().hex}"
        single_res = reporter.simulate_single(invalid_symbol, self.percentage)
        self.assertIsInstance(single_res, dict)

    def test_get_stream_data_integration(self):
        reporter = StressReporter(self.storage_file)
        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

if __name__ == "__main__":
    unittest.main()