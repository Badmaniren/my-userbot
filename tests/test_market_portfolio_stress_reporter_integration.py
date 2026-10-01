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
        self.random_suffix = uuid.uuid4().hex[:8]
        self.storage_file = f"test_market_storage_{self.random_suffix}.db"
        self.symbol = f"SYM_{random.randint(100, 999)}"
        self.shift_value = round(random.uniform(-0.5, 0.5), 4)
        self.shifts = [self.shift_value, round(self.shift_value * 2, 4)]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_class_and_methods(self):
        reporter = StressReporter(self.storage_file)
        
        report_result = reporter.run_stress_reporting(self.symbol, self.shifts)
        self.assertIsInstance(report_result, dict)
        self.assertIn("simulation_results", report_result)
        self.assertIn("base_report", report_result)
        self.assertIn("compact_text_report", report_result)
        self.assertIn("tabular_report", report_result)
        self.assertIn("chart_export", report_result)
        
        self.assertIn(self.symbol, report_result["compact_text_report"])
        self.assertIsInstance(report_result["tabular_report"], list)
        self.assertEqual(report_result["chart_export"]["type"], "line")

        single_sim = reporter.simulate_single(self.symbol, self.shift_value)
        self.assertIsInstance(single_sim, (dict, list, float, int, type(None)))

        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

    def test_portfolio_stress_reporter_inheritance(self):
        pipeline_reporter = PortfolioStressReporter(self.storage_file)
        pipeline_result = pipeline_reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIsInstance(pipeline_result, dict)
        self.assertEqual(pipeline_result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(pipeline_result["tabular_report"][0]["shifts"], self.shifts)

    def test_functional_helpers(self):
        func_report = generate_stress_report(self.storage_file, self.symbol, self.shift_value)
        self.assertIsInstance(func_report, dict)
        self.assertIn("simulation_results", func_report)

        pipeline_res = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(pipeline_res, dict)
        self.assertIn("compact_text_report", pipeline_res)
        self.assertTrue(len(pipeline_res["compact_text_report"]) > 0)


if __name__ == "__main__":
    unittest.main()