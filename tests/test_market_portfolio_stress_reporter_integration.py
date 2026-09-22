import os
import unittest
import uuid
import random
from skills.market_portfolio_stress_reporter import (
    StressReporter,
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline
)
from skills.market_parser import MarketParser


class TestMarketPortfolioStressReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        
        parser = MarketParser(self.storage_file)
        for _ in range(5):
            price = round(random.uniform(10.0, 1000.0), 2)
            parser.fetch_and_store(self.symbol, price)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_stress_reporter_class_integration(self):
        reporter = StressReporter(self.storage_file)
        shifts = [round(random.uniform(-0.5, 0.5), 2), round(random.uniform(-0.5, 0.5), 2)]
        
        result = reporter.run_stress_reporting(self.symbol, shifts)
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

        single_percentage = round(random.uniform(-0.2, 0.2), 2)
        single_res = reporter.simulate_single(self.symbol, single_percentage)
        self.assertIsNotNone(single_res)

        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

    def test_portfolio_stress_reporter_subclass(self):
        reporter = PortfolioStressReporter(self.storage_file)
        shifts = [round(random.uniform(-0.3, 0.3), 2)]
        
        result = reporter.run_stress_report(self.symbol, shifts)
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_generate_stress_report_function(self):
        percentage = round(random.uniform(-0.15, 0.15), 2)
        result = generate_stress_report(self.storage_file, self.symbol, percentage)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)

    def test_run_stress_reporting_pipeline_function(self):
        shifts = [round(random.uniform(-0.4, 0.4), 2), round(random.uniform(-0.4, 0.4), 2)]
        result = run_stress_reporting_pipeline(self.storage_file, self.symbol, shifts)
        
        self.assertIsInstance(result, dict)
        self.assertIn("simulation_results", result)
        self.assertIn("base_report", result)


if __name__ == "__main__":
    unittest.main()