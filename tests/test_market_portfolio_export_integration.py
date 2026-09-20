import unittest
import os
import json
import uuid
import random
import io
from skills.market_parser import MarketParser
from skills.market_portfolio_export import PortfolioExporter, export_to_json, export_to_csv, MarketPortfolioExporter

class TestMarketPortfolioExportIntegration(unittest.TestCase):

    def setUp(self):
        self.unique_id = str(uuid.uuid4())[:8]
        self.storage_filename = f"test_storage_{self.unique_id}.json"
        self.json_dest_filename = f"test_dest_{self.unique_id}.json"
        self.csv_dest_filename = f"test_dest_{self.unique_id}.csv"

        self.symbol = f"SYM_{random.randint(100, 999)}"
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.timestamp = f"2023-10-27T10:00:00Z"

        parser = MarketParser(self.storage_filename)
        parser.fetch_and_store(self.symbol, self.price)

    def tearDown(self):
        for filename in [self.storage_filename, self.json_dest_filename, self.csv_dest_filename]:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except OSError:
                    pass

    def test_exporter_json_integration(self):
        exporter = PortfolioExporter(self.storage_filename)
        success = exporter.export_json(self.json_dest_filename)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.json_dest_filename))

        with open(self.json_dest_filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn(self.symbol, data)
        records = data[self.symbol]
        self.assertIsInstance(records, list)
        self.assertTrue(any(r.get("price") == self.price for r in records if isinstance(r, dict)))

    def test_exporter_csv_integration(self):
        exporter = PortfolioExporter(self.storage_filename)
        success = exporter.export_csv(self.csv_dest_filename)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.csv_dest_filename))

        with open(self.csv_dest_filename, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("symbol", content)
        self.assertIn("price", content)
        self.assertIn(self.symbol, content)
        self.assertIn(str(self.price), content)

    def test_streams_integration(self):
        exporter = PortfolioExporter(self.storage_filename)

        json_stream = exporter.get_json_stream()
        self.assertIsInstance(json_stream, io.BytesIO)
        json_content = json_stream.getvalue().decode("utf-8")
        self.assertIn(self.symbol, json_content)

        csv_stream = exporter.get_csv_stream()
        self.assertIsInstance(csv_stream, io.BytesIO)
        csv_content = csv_stream.getvalue().decode("utf-8")
        self.assertIn(self.symbol, csv_content)
        self.assertIn(str(self.price), csv_content)

    def test_helper_functions_and_subclass(self):
        res_json = export_to_json(self.storage_filename, self.json_dest_filename)
        self.assertTrue(res_json)
        self.assertTrue(os.path.exists(self.json_dest_filename))

        res_csv = export_to_csv(self.storage_filename, self.csv_dest_filename)
        self.assertTrue(res_csv)
        self.assertTrue(os.path.exists(self.csv_dest_filename))

        sub_exporter = MarketPortfolioExporter(self.storage_filename)
        sub_res = sub_exporter.export_data(self.json_dest_filename)
        self.assertTrue(sub_res)

if __name__ == "__main__":
    unittest.main()