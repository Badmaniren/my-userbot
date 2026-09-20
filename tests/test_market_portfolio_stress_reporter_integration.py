import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import (
    run_stress_reporting_pipeline,
    PortfolioStressReporter
)

class TestMarketPortfolioStressReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.unique_id = str(uuid.uuid4())[:8]
        self.symbol = f"TICK_{self.unique_id}"
        self.storage_file = f"test_market_storage_{self.unique_id}.json"
        
        self.initial_price = round(random.uniform(10.0, 1000.0), 2)
        
        storage_dir = os.path.dirname(self.storage_file)
        if storage_dir and not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)

        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(f'{{"symbol": "{self.symbol}", "price": {self.initial_price}, "history": [{self.initial_price}]}}')

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_stress_reporter_composition_integration(self):
        shifts = [-20.0, -10.0, 10.0, 20.0]
        
        reporter_instance = PortfolioStressReporter(self.storage_file)
        self.assertTrue(hasattr(reporter_instance, 'run_stress_report'))
        
        report_result = reporter_instance.run_stress_report(self.symbol, shifts)
        self.assertIsNotNone(report_result)

        pipeline_result = run_stress_reporting_pipeline(self.storage_file, self.symbol, shifts)
        self.assertIsNotNone(pipeline_result)

if __name__ == "__main__":
    unittest.main()