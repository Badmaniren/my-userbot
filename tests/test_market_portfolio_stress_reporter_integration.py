import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter, generate_stress_report, run_stress_reporting_pipeline

class TestMarketPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = [round(random.uniform(-0.2, 0.2), 4) for _ in range(3)]
        self.percentage = self.shifts[0]

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_integration_flow(self):
        reporter = StressReporter(self.storage_file)
        
        try:
            result = reporter.run_stress_reporting(self.symbol, self.shifts)
            self.assertIsInstance(result, dict)
            self.assertIn("simulation_results", result)
            self.assertIn("base_report", result)
            self.assertIn("compact_text_report", result)
            self.assertIn("tabular_report", result)
            self.assertIn("chart_export", result)
            self.assertIn(self.symbol, result["compact_text_report"])
        except Exception as e:
            self.fail(f"StressReporter failed with real integration: {e}")

    def test_portfolio_stress_reporter_pipeline(self):
        pipeline_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(pipeline_result, dict)
        self.assertEqual(pipeline_result["tabular_report"][0]["symbol"], self.symbol)
        self.assertEqual(pipeline_result["tabular_report"][0]["shifts"], self.shifts)

    def test_generate_stress_report_wrapper(self):
        single_result = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        self.assertIsInstance(single_result, dict)
        self.assertIn("simulation_results", single_result)

    def test_simulate_single_and_stream(self):
        reporter = PortfolioStressReporter(self.storage_file)
        try:
            single_sim = reporter.simulate_single(self.symbol, self.percentage)
            self.assertIsInstance(single_sim, (dict, list, float, int))
        except Exception as e:
            self.fail(f"simulate_single raised unexpected exception: {e}")

        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

if __name__ == "__main__":
    unittest.main()