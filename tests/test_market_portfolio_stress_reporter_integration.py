import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import PortfolioStressReporter, generate_stress_report, run_stress_reporting_pipeline


class TestPortfolioStressReporterIntegration(unittest.TestCase):

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

    def test_portfolio_stress_reporter_pipeline(self):
        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)
        self.assertIn("compact_text_report", result)
        self.assertIn("tabular_report", result)
        self.assertIn("chart_export", result)
        
        self.assertIn(self.symbol, result["compact_text_report"])
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(result["tabular_report"][0]["shifts"], self.shifts)

    def test_generate_stress_report_helper(self):
        result = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("tabular_report", result)
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(result["tabular_report"][0]["shifts"], [self.percentage])

    def test_stress_reporter_class_methods(self):
        reporter = PortfolioStressReporter(self.storage_file)
        
        report_data = reporter.run_stress_report(self.symbol, self.shifts)
        self.assertIsInstance(report_data, dict)
        self.assertEqual(report_data["tabular_report"][0]["symbol"], self.symbol)

        single_sim = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(single_sim, (dict, list, float, int, type(None)))

        stream_data = reporter.get_stream_data()
        self.assertIsInstance(stream_data, (dict, list, type(None)))


if __name__ == "__main__":
    unittest.main()