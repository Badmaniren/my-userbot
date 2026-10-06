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
        self.shifts = [round(random.uniform(-0.2, 0.2), 4), round(random.uniform(-0.5, 0.5), 4)]
        self.percentage = round(random.uniform(-0.1, 0.1), 4)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_class_methods(self):
        reporter = StressReporter(self.storage_file)
        
        report_result = reporter.run_stress_reporting(self.symbol, self.shifts)
        self.assertIsInstance(report_result, dict)
        self.assertIn("simulation_results", report_result)
        self.assertIn("base_report", report_result)
        self.assertIn("compact_text_report", report_result)
        self.assertIn("tabular_report", report_result)
        self.assertIn("chart_export", report_result)
        
        self.assertIn(self.symbol, report_result["compact_text_report"])

        single_sim = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(single_sim, (dict, float, int))

        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

    def test_portfolio_stress_reporter_inheritance(self):
        pipeline_reporter = PortfolioStressReporter(self.storage_file)
        result = pipeline_reporter.run_stress_report(self.symbol, self.shifts)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)

    def test_functional_wrappers(self):
        gen_result = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        self.assertIsInstance(gen_result, dict)
        self.assertIn("simulation_results", gen_result)

        pipe_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(pipe_result, dict)
        self.assertIn("chart_export", pipe_result)

if __name__ == "__main__":
    unittest.main()