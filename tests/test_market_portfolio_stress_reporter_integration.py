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
from skills.market_portfolio_collector_agent import MarketParser

class TestMarketPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_data_integration"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_file = os.path.join(self.test_dir, f"test_storage_{uuid.uuid4().hex}.json")
        self.symbol = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        
        parser = MarketParser(self.storage_file)
        self.initial_price = round(random.uniform(10.0, 1000.0), 2)
        parser.fetch_and_store(self.symbol, self.initial_price)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_stress_reporter_integration_flow(self):
        reporter = StressReporter(self.storage_file)
        shifts = [round(random.uniform(-50.0, 50.0), 2), round(random.uniform(-50.0, 50.0), 2)]

        result = reporter.run_stress_reporting(self.symbol, shifts)
        
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)
        self.assertIsInstance(result["simulation_results"], (list, dict))
        self.assertIsInstance(result["base_report"], (dict, str, list))
        
        single_percentage = round(random.uniform(-20.0, 20.0), 2)
        single_sim = reporter.simulate_single(self.symbol, single_percentage)
        self.assertIsNotNone(single_sim)

        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

    def test_portfolio_stress_reporter_subclass(self):
        reporter = PortfolioStressReporter(self.storage_file)
        shifts = [round(random.uniform(-10.0, 10.0), 2)]

        report = reporter.run_stress_report(self.symbol, shifts)
        self.assertIn("simulation_results", report)

    def test_helper_functions_integration(self):
        percentage = round(random.uniform(-30.0, 30.0), 2)
        func_result = generate_stress_report(self.storage_file, self.symbol, percentage)
        self.assertIn("simulation_results", func_result)

        pipeline_shifts = [round(random.uniform(-15.0, 15.0), 2)]
        pipeline_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, pipeline_shifts)
        self.assertIn("simulation_results", pipeline_result)
        self.assertIn("base_report", pipeline_result)

if __name__ == "__main__":
    unittest.main()