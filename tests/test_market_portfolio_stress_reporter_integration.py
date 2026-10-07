import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import (
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline
)

class IntegrationTestPortfolioStressReporter(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shift = round(random.uniform(-0.2, 0.2), 4)
        self.shifts = [self.shift, round(self.shift * 2, 4)]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_portfolio_stress_reporter_integration(self):
        reporter = PortfolioStressReporter(self.storage_file)
        
        try:
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
        except Exception as e:
            self.fail(f"Integration pipeline failed with unsuppressed/unexpected error: {e}")

    def test_generate_stress_report_function(self):
        try:
            res = generate_stress_report(self.storage_file, self.symbol, self.shift)
            self.assertIsInstance(res, dict)
            self.assertIn("simulation_results", res)
        except Exception as e:
            self.fail(f"generate_stress_report failed: {e}")

    def test_run_stress_reporting_pipeline_function(self):
        try:
            res = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
            self.assertIsInstance(res, dict)
            self.assertIn("chart_export", res)
            self.assertEqual(res["chart_export"]["data"], res["simulation_results"])
        except Exception as e:
            self.fail(f"run_stress_reporting_pipeline failed: {e}")

    def test_error_handling_no_suppression(self):
        invalid_storage = f"/nonexistent_dir_{uuid.uuid4().hex}/invalid.db"
        reporter = PortfolioStressReporter(invalid_storage)
        with self.assertRaises(Exception):
            reporter.run_stress_report(self.symbol, self.shifts)

if __name__ == "__main__":
    unittest.main()