import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import PortfolioStressReporter, StressReporter, generate_stress_report, run_stress_reporting_pipeline

class TestPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.db"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.shift_value = round(random.uniform(-0.5, 0.5), 4)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_pipeline_real_execution(self):
        reporter = PortfolioStressReporter(self.storage_file)
        shifts = [self.shift_value, self.shift_value * 2]
        
        result = reporter.run_stress_report(self.symbol, shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)
        self.assertIn("compact_text_report", result)
        self.assertIn("tabular_report", result)
        self.assertIn("chart_export", result)
        
        self.assertIn(self.symbol, result["compact_text_report"])
        self.assertEqual(result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(result["tabular_report"][0]["shifts"], shifts)

    def test_generate_stress_report_helper(self):
        result = generate_stress_report(self.storage_file, self.symbol, self.shift_value)
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_run_stress_reporting_pipeline_helper(self):
        shifts = [self.shift_value]
        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, shifts)
        self.assertIsInstance(result, dict)
        self.assertIn("chart_export", result)
        self.assertEqual(result["chart_export"]["data"], result["simulation_results"])

    def test_stress_reporter_single_simulation(self):
        reporter = StressReporter(self.storage_file)
        res = reporter.simulate_single(self.symbol, self.shift_value)
        self.assertIsInstance(res, (dict, type(None)))

    def test_get_stream_data_execution(self):
        reporter = StressReporter(self.storage_file)
        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

if __name__ == "__main__":
    unittest.main()