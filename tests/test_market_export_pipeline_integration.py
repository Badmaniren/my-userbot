import unittest
import os
import uuid
import random
from skills.market_export_pipeline import MarketExportPipeline


class TestMarketExportPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4().hex}.json"
        self.pipeline = MarketExportPipeline(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_export_aggregated_data_integration(self):
        random_symbol = f"SYM_{random.randint(1000, 9999)}"
        random_price = round(random.uniform(10.0, 1000.0), 2)
        random_url = f"http://example.com/market/{uuid.uuid4().hex}"
        random_export_id = uuid.uuid4().hex

        result = self.pipeline.export_aggregated_data(
            symbol=random_symbol,
        price=random_price,
            url=random_url,
            export_id=random_export_id
        )

        self.assertIn(random_export_id, result)
        self.assertIn(random_symbol, result)
        self.assertTrue(os.path.exists(self.storage_file), "Файл хранилища должен быть создан реальным DBStorage")

    def test_export_symbol_report_integration(self):
        random_symbol = f"BTC_{random.randint(100, 999)}"
        report = self.pipeline.export_symbol_report(random_symbol)
        self.assertIsNotNone(report)


if __name__ == "__main__":
    unittest.main()