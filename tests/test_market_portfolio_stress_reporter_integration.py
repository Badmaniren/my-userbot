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
        self.storage_file = f"test_storage_{uuid.uuid4()}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = [round(random.uniform(-0.2, 0.2), 4) for _ in range(3)]
        self.percentage = round(random.uniform(-0.15, 0.15), 4)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_class_methods(self):
        reporter = StressReporter(self.storage_file)
        
        report_res = reporter.run_stress_reporting(self.symbol, self.shifts)
        self.assertIsInstance(report_res, dict)
        self.assertIn("simulation_results", report_res)
        self.assertIn("base_report", report_res)
        self.assertIn("compact_text_report", report_res)
        self.assertIn("tabular_report", report_res)
        self.assertIn("chart_export", report_res)
        
        self.assertIn(self.symbol, report_res["compact_text_report"])
        self.assertEqual(report_res["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(report_res["tabular_report"][0]["shifts"], self.shifts)

        single_sim = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(single_sim, dict)

        stream_data = reporter.get_stream_data()
        self.assertIsInstance(stream_data, (dict, list, type(None)))

    def test_portfolio_stress_reporter_inheritance(self):
        portfolio_reporter = PortfolioStressReporter(self.storage_file)
        pipeline_res = portfolio_reporter.run_stress_report(self.symbol, self.shifts)
        
        self.assertIsInstance(pipeline_res, dict)
        self.assertEqual(pipeline_res["tabular_report"][0]["symbol"], self.symbol)

    def test_module_helper_functions(self):
        gen_res = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        self.assertIsInstance(gen_res, dict)
        self.assertEqual(gen_res["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(gen_res["tabular_report"][0]["shifts"], [self.percentage])

        pipe_res = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(pipe_res, dict)
        self.assertEqual(pipe_res["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(pipe_res["tabular_report"][0]["shifts"], self.shifts)

if __name__ == "__main__":
    unittest.main()