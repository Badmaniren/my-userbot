import unittest
import os
import uuid
import random
from skills.market_portfolio_data_exporter import PortfolioDataExporter, export_portfolio_data_pipeline

class TestMarketPortfolioDataExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.url = f"https://api.example.com/v1/portfolio/{uuid.uuid4().hex}"
        self.symbol = f"SYM_{random.randint(1000, 9999)}"
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.template = f"Report_{uuid.uuid4().hex[:6]}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_exporter_pipeline_integration(self):
        pipeline_result = export_portfolio_data_pipeline(
            storage_file=self.storage_file,
            url=self.url,
            symbol=self.symbol,
            shifts=self.shifts,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            notification_template=self.template
        )
        self.assertTrue(pipeline_result)

    def test_exporter_class_methods(self):
        exporter = PortfolioDataExporter(self.storage_file)
        
        data_summary = exporter.export_data(self.url, self.shifts)
        self.assertIsInstance(data_summary, dict)

        all_data = exporter.export_all(self.url, self.symbol, self.shifts)
        self.assertIsInstance(all_data, dict)
        self.assertIn("portfolio_summary", all_data)
        self.assertIn("stress_report", all_data)

        stream_data = exporter.export_stream()
        self.assertIsNotNone(stream_data)

if __name__ == "__main__":
    unittest.main()