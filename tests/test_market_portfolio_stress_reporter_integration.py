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
from skills.market_parser import MarketParser

class TestStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_market_data_{uuid.uuid4().hex}.json"
        self.symbol = f"TICK_{random.randint(1000, 9999)}"
        
        parser = MarketParser(self.storage_file)
        base_price = round(random.uniform(100.0, 500.0), 2)
        parser.fetch_and_store(self.symbol, base_price)
        
        for i in range(5):
            new_price = round(base_price * (1 + random.uniform(-0.05, 0.05)), 2)
            parser.fetch_and_store(self.symbol, new_price)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_stress_reporter_integration(self):
        shifts = [round(random.uniform(-10.0, 10.0), 2), round(random.uniform(-10.0, 10.0), 2)]
        
        reporter = StressReporter(self.storage_file)
        report_result = reporter.run_stress_reporting(self.symbol, shifts)
        
        self.assertIn("simulation_results", report_result)
        self.assertIn("base_report", report_result)
        
        sim_single_pct = round(random.uniform(-5.0, 5.0), 2)
        single_result = reporter.simulate_single(self.symbol, sim_single_pct)
        self.assertIsNotNone(single_result)
        
        stream_data = reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

    def test_portfolio_stress_reporter_subclass(self):
        shifts = [round(random.uniform(-15.0, 15.0), 2)]
        portfolio_reporter = PortfolioStressReporter(self.storage_file)
        sub_result = portfolio_reporter.run_stress_report(self.symbol, shifts)
        
        self.assertIn("simulation_results", sub_result)
        self.assertIn("base_report", sub_result)

    def test_functional_wrappers(self):
        pct = round(random.uniform(-20.0, 20.0), 2)
        func_result = generate_stress_report(self.storage_file, self.symbol, pct)
        self.assertIn("simulation_results", func_result)
        self.assertIn("base_report", func_result)

        shifts_pipeline = [round(random.uniform(-5.0, 5.0), 2)]
        pipeline_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, shifts_pipeline)
        self.assertIn("simulation_results", pipeline_result)
        self.assertIn("base_report", pipeline_result)

if __name__ == "__main__":
    unittest.main()