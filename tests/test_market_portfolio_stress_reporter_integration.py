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
        self.storage_file = f"test_storage_{uuid.uuid4()}.db"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.percentage = round(random.uniform(-50.0, 50.0), 2)
        self.shifts = [self.percentage, round(self.percentage / 2, 2)]

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
        self.assertEqual(report_result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(report_result["tabular_report"][0]["shifts"], self.shifts)

        single_sim = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(single_sim, dict)

        stream_data = reporter.get_stream_data()
        self.assertIsInstance(stream_data, (dict, list, type(None)))

    def t_portfolio_stress_reporter_subclass(self):
        portfolio_reporter = PortfolioStressReporter(self.storage_file)
        pipeline_result = portfolio_reporter.run_stress_report(self.symbol, self.shifts)
        self.assertIsInstance(pipeline_result, dict)
        self.assertEqual(pipeline_result["tabular_report"][0]["symbol"], self.symbol)

    def test_functional_wrappers(self):
        gen_result = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        self.assertIsInstance(gen_result, dict)
        self.assertIn("simulation_results", gen_result)
        self.assertEqual(gen_result["tabular_report"][0]["shifts"], [self.percentage])

        pipe_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(pipe_result, dict)
        self.assertIn("chart_export", pipe_result)
        self.assertEqual(pipe_result["tabular_report"][0]["symbol"], self.symbol)


if __name__ == "__main__":
    unittest.main()