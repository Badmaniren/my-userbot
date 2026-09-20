import unittest
from unittest.mock import patch
import io
import csv
import json
import os
import uuid
import random
from skills.market_portfolio_export import (
    PortfolioExporter,
    export_to_json,
    export_to_csv,
    MarketPortfolioExporter
)

class TestMarketPortfolioExport(unittest.TestCase):
    def setUp(self):
        self.storage_filename = f"storage_{uuid.uuid4().hex}.json"
        self.dest_filename = f"dest_{uuid.uuid4().hex}"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.price = round(random.uniform(10.0, 1000.0), 2)
        self.timestamp = f"2023-10-{random.randint(10, 30)}T12:00:00Z"

        self.test_data = {
            self.symbol: [
                {"price": self.price, "timestamp": self.timestamp}
            ]
        }

    def tearDown(self):
        for fname in [self.storage_filename, f"{self.dest_filename}.json", f"{self.dest_filename}.csv"]:
            if os.path.exists(fname):
                try:
                    os.remove(fname)
                except OSError:
                    pass

    def test_exporter_init_and_inheritance(self):
        exporter = PortfolioExporter(self.storage_filename)
        self.assertEqual(exporter.storage_file, self.storage_filename)

        market_exporter = MarketPortfolioExporter(self.storage_filename)
        self.assertIsInstance(market_exporter, PortfolioExporter)

    def test_export_json_success(self):
        raw_json = json.dumps(self.test_data)
        with open(self.storage_filename, "w", encoding="utf-8") as f:
            f.write(raw_json)

        dest_file = f"{self.dest_filename}.json"
        exporter = PortfolioExporter(self.storage_filename)
        result = exporter.export_json(dest_file)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(dest_file))

        with open(dest_file, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)
            self.assertIn(self.symbol, loaded_data)
            self.assertEqual(loaded_data[self.symbol][0]["price"], self.price)

    def test_export_json_file_not_found(self):
        non_existent = f"ghost_{uuid.uuid4().hex}.json"
        dest_file = f"{self.dest_filename}.json"
        exporter = PortfolioExporter(non_existent)
        result = exporter.export_json(dest_file)
        self.assertFalse(result)

    def test_export_json_io_error(self):
        raw_json = json.dumps(self.test_data)
        with open(self.storage_filename, "w", encoding="utf-8") as f:
            f.write(raw_json)

        exporter = PortfolioExporter(self.storage_filename)
        bad_dest = f"/invalid_dir_{uuid.uuid4().hex}/dest.json"
        result = exporter.export_json(bad_dest)
        self.assertFalse(result)

    def test_export_csv_success(self):
        raw_json = json.dumps(self.test_data)
        with open(self.storage_filename, "w", encoding="utf-8") as f:
            f.write(raw_json)

        dest_file = f"{self.dest_filename}.csv"
        exporter = PortfolioExporter(self.storage_filename)
        result = exporter.export_csv(dest_file)

        self.assertTrue(result)
        self.assertTrue(os.path.exists(dest_file))

        with open(dest_file, "r", encoding="utf-8", newline="") as f:
            reader = list(csv.reader(f))
            self.assertGreaterEqual(len(reader), 2)
            self.assertEqual(reader[0], ["symbol", "price", "timestamp"])
            self.assertEqual(reader[1][0], self.symbol)
            self.assertEqual(float(reader[1][1]), self.price)
            self.assertEqual(reader[1][2], self.timestamp)

    def test_export_csv_complex_structures(self):
        complex_data = {
            self.symbol: [
                {"price": self.price},
                "scalar_record"
            ],
            f"OTHER_{uuid.uuid4().hex[:4]}": 42.5
        }
        with open(self.storage_filename, "w", encoding="utf-8") as f:
            json.dump(complex_data, f)

        dest_file = f"{self.dest_filename}.csv"
        exporter = PortfolioExporter(self.storage_filename)
        result = exporter.export_csv(dest_file)
        self.assertTrue(result)

        with open(dest_file, "r", encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
            self.assertGreaterEqual(len(rows), 4)

    def test_export_csv_file_not_found(self):
        non_existent = f"ghost_{uuid.uuid4().hex}.json"
        dest_file = f"{self.dest_filename}.csv"
        exporter = PortfolioExporter(non_existent)
        result = exporter.export_csv(dest_file)
        self.assertFalse(result)

    def test_get_json_stream_success(self):
        raw_json = json.dumps(self.test_data)
        with open(self.storage_filename, "w", encoding="utf-8") as f:
            f.write(raw_json)

        exporter = PortfolioExporter(self.storage_filename)
        stream = exporter.get_json_stream()

        self.assertIsInstance(stream, io.BytesIO)
        content = stream.read().decode("utf-8")
        parsed = json.loads(content)
        self.assertIn(self.symbol, parsed)

    def test_get_json_stream_file_not_found(self):
        non_existent = f"ghost_{uuid.uuid4().hex}.json"
        exporter = PortfolioExporter(non_existent)
        stream = exporter.get_json_stream()

        self.assertIsInstance(stream, io.BytesIO)
        content = stream.read().decode("utf-8")
        self.assertEqual(content, "{}")

    def test_get_csv_stream_success(self):
        raw_json = json.dumps(self.test_data)
        with open(self.storage_filename, "w", encoding="utf-8") as f:
            f.write(raw_json)

        exporter = PortfolioExporter(self.storage_filename)
        stream = exporter.get_csv_stream()

        self.assertIsInstance(stream, io.BytesIO)
        content = stream.read().decode("utf-8")
        self.assertIn("symbol,price,timestamp", content)
        self.assertIn(self.symbol, content)
        self.assertIn(str(self.price), content)

    def test_get_csv_stream_file_not_found(self):
        non_existent = f"ghost_{uuid.uuid4().hex}.json"
        exporter = PortfolioExporter(non_existent)
        stream = exporter.get_csv_stream()

        self.assertIsInstance(stream, io.BytesIO)
        content = stream.read().decode("utf-8")
        self.assertIn("symbol,price,timestamp", content)

    def test_helper_functions_and_market_portfolio_exporter(self):
        raw_json = json.dumps(self.test_data)
        with open(self.storage_filename, "w", encoding="utf-8") as f:
            f.write(raw_json)

        dest_json = f"{self.dest_filename}_func.json"
        dest_csv = f"{self.dest_filename}_func.csv"

        res_json = export_to_json(self.storage_filename, dest_json)
        self.assertTrue(res_json)
        self.assertTrue(os.path.exists(dest_json))

        res_csv = export_to_csv(self.storage_filename, dest_csv)
        self.assertTrue(res_csv)
        self.assertTrue(os.path.exists(dest_csv))

        market_exporter = MarketPortfolioExporter(self.storage_filename)
        dest_market = f"{self.dest_filename}_market.json"
        res_market = market_exporter.export_data(dest_market)
        self.assertTrue(res_market)
        self.assertTrue(os.path.exists(dest_market))

if __name__ == "__main__":
    unittest.main()