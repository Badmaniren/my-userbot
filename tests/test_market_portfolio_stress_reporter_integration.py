import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_reporter import generate_stress_report, PortfolioStressReporter

class TestMarketPortfolioStressReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.shifts = [round(random.uniform(-20.0, 20.0), 2) for _ in range(3)]

        initial_data = {
            self.symbol: [
                {"price": round(random.uniform(100.0, 500.0), 2), "timestamp": "2023-10-01T12:00:00"}
            ]
        }
        import json
        with open(self.storage_file, "w") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_stress_reporter_composition_and_execution(self):
        reporter = PortfolioStressReporter(self.storage_file)
        self.assertTrue(hasattr(reporter, "simulator"))
        self.assertTrue(hasattr(reporter, "report_generator"))

        report = reporter.generate_stress_report(self.symbol, self.shifts)
        self.assertIsInstance(report, dict)
        self.assertIn("stress_results", report)
        self.assertIn("base_report", report)

        functional_report = generate_stress_report(self.storage_file, self.symbol, self.shifts)
        self.assertIsInstance(functional_report, dict)
        self.assertTrue(len(functional_report) > 0)

if __name__ == "__main__":
    unittest.main()