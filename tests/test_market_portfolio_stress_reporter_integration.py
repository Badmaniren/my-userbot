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
        self.test_dir = f"test_vault_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"storage_{uuid.uuid4().hex}.db")
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = [round(random.uniform(-0.5, 0.5), 4) for _ in range(random.randint(1, 3))]
        self.percentage = round(random.uniform(-0.2, 0.2), 4)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_stress_reporter_integration_flow(self):
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

    def test_portfolio_stress_reporter_pipeline(self):
        pipeline_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, self.shifts)
        
        self.assertIsInstance(pipeline_result, dict)
        self.assertIn("simulation_results", pipeline_result)
        self.assertIn("tabular_report", pipeline_result)
        self.assertEqual(pipeline_result["tabular_report"][0]["symbol"], self.symbol)

    def test_generate_stress_report_wrapper(self):
        gen_result = generate_stress_report(self.storage_file, self.symbol, self.percentage)
        
        self.assertIsInstance(gen_result, dict)
        self.assertIn("simulation_results", gen_result)
        self.assertEqual(gen_result["tabular_report"][0]["shifts"], [self.percentage])

    def test_simulate_single_and_stream(self):
        reporter = PortfolioStressReporter(self.storage_file)
        single_res = reporter.simulate_single(self.symbol, self.percentage)
        self.assertIsInstance(single_res, (dict, list))
        
        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

if __name__ == "__main__":
    unittest.main()