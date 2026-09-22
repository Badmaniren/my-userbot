import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import StressReporter, run_stress_reporting_pipeline
from skills.market_portfolio_collector_agent import MarketParser


class TestMarketPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_market_storage_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        
        parser = MarketParser(self.storage_file)
        for _ in range(5):
            price = round(random.uniform(10.0, 500.0), 2)
            parser.fetch_and_store(self.symbol, price)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_stress_reporter_integration_flow(self):
        reporter = StressReporter(self.storage_file)
        shift_value = round(random.uniform(-0.2, 0.2), 2)
        shifts = [shift_value]

        report_result = reporter.run_stress_reporting(self.symbol, shifts)
        self.assertIsInstance(report_result, dict)
        self.assertIn("simulation_results", report_result)
        self.assertIn("base_report", report_result)

        single_sim = reporter.simulate_single(self.symbol, shift_value)
        self.assertIsInstance(single_sim, (dict, list, float, int))

        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

        pipeline_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, shifts)
        self.assertIsInstance(pipeline_result, dict)
        self.assertIn("simulation_results", pipeline_result)
        self.assertIn("base_report", pipeline_result)


if __name__ == "__main__":
    unittest.main()