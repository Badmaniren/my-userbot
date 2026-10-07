import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import PortfolioStressReporter, generate_stress_report

class TestPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_portfolio_storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.shift_value = round(random.uniform(-0.5, 0.5), 4)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_pipeline_integration(self):
        reporter = PortfolioStressReporter(self.storage_file)
        shifts = [self.shift_value, self.shift_value * 2]
        
        report_result = reporter.run_stress_report(self.symbol, shifts)
        
        self.assertIsInstance(report_result, dict)
        self.assertIn("simulation_results", report_result)
        self.assertIn("base_report", report_result)
        self.assertIn("compact_text_report", report_result)
        self.assertIn("tabular_report", report_result)
        self.assertIn("chart_export", report_result)
        
        self.assertIn(self.symbol, report_result["compact_text_report"])
        self.assertEqual(report_result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(report_result["tabular_report"][0]["shifts"], shifts)

    def test_generate_stress_report_helper(self):
        result = generate_stress_report(self.storage_file, self.symbol, self.shift_value)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(result["tabular_report"][0]["shifts"], [self.shift_value])

if __name__ == "__main__":
    unittest.main()