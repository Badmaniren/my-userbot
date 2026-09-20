import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_data_exporter import MarketPortfolioDataExporter
from skills.market_portfolio_api_gateway import MarketPortfolioAPIGateway
from skills.market_portfolio_stress_reporter import StressReporter

class TestMarketPortfolioDataExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.rand_str = str(uuid.uuid4())[:8]
        self.storage_file = f"test_storage_{self.rand_str}.json"
        self.symbol = f"SYM_{self.rand_str}".upper()
        self.url = f"http://example.com/api/{self.rand_str}"
        self.shifts = [random.uniform(-0.1, 0.1), random.uniform(-0.2, 0.2)]

        initial_data = {
            "symbol": self.symbol,
            "prices": [random.uniform(100.0, 200.0), random.uniform(100.0, 200.0)],
            "timestamp": str(uuid.uuid4())
        }
        with open(self.storage_file, "w") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_exporter_integration_with_gateway_and_reporter(self):
        gateway = MarketPortfolioAPIGateway(storage_file=self.storage_file)
        reporter = StressReporter(storage_file=self.storage_file)

        exporter = MarketPortfolioDataExporter(storage_file=self.storage_file)

        self.assertTrue(hasattr(exporter, "export_data") or hasattr(exporter, "export_summary") or hasattr(exporter, "run_export_pipeline"),
                        "Модуль MarketPortfolioDataExporter должен содержать метод экспорта")

        if hasattr(exporter, "export_data"):
            export_result = exporter.export_data(self.url, self.shifts)
        elif hasattr(exporter, "export_summary"):
            export_result = exporter.export_summary(self.url)
        else:
            export_result = exporter.run_export_pipeline(self.url, self.shifts)

        gateway_summary = gateway.export_portfolio_summary(self.url)
        stress_data = reporter.run_stress_reporting(self.symbol, self.shifts)

        self.assertIsNotNone(export_result)
        self.assertIsNotNone(gateway_summary)
        self.assertIsNotNone(stress_data)

        export_dump_file = f"export_{self.rand_str}.json"
        if os.path.exists(export_dump_file):
            os.remove(export_dump_file)

if __name__ == "__main__":
    unittest.main()