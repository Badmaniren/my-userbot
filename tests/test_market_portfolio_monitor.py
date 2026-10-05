import unittest
from unittest.mock import patch, mock_open
import os
import json
import uuid
import random
import io

from skills.market_portfolio_monitor import (
    MarketParser,
    MarketReportGenerator,
    run_pipeline,
    start_new,
    start_ened,
    generate_market_report,
    run_market_telegram_pipeline,
    export_audit_logs,
)


class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self) -> None:
        self.rand_suffix = uuid.uuid4().hex
        self.storage_file = f"test_storage_{self.rand_suffix}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/api/{uuid.uuid4().hex}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))

    def tearDown(self) -> None:
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_market_parser_fetch_and_store_and_load(self) -> None:
        parser = MarketParser(storage_file=self.storage_file)
        price = round(random.uniform(10.0, 1000.0), 4)

        parser.fetch_and_store(symbol=self.symbol, price=price)
        self.assertTrue(os.path.exists(self.storage_file))

        loaded_data = parser.load_data(self.storage_file)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.symbol, loaded_data)
        self.assertEqual(float(loaded_data[self.symbol]), price)

    def test_market_parser_load_data_invalid_json(self) -> None:
        invalid_content = f"{{corrupted_{uuid.uuid4().hex}"
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(invalid_content)

        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

    def test_market_parser_load_data_non_dict_json(self) -> None:
        list_json = json.dumps([random.randint(1, 100), random.randint(101, 200)])
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(list_json)

        parser = MarketParser(storage_file=self.storage_file)
        data = parser.load_data(self.storage_file)
        self.assertEqual(data, {})

    def test_market_report_generator_symbol_report(self) -> None:
        price = round(random.uniform(1.0, 500.0), 2)
        initial_data = {self.symbol: price}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(price), report)

    def test_market_report_generator_no_data(self) -> None:
        gen = MarketReportGenerator(storage_file=self.storage_file)
        report = gen.generate_symbol_report(symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self) -> None:
        content = json.dumps({uuid.uuid4().hex: uuid.uuid4().hex})
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(content)

        gen = MarketReportGenerator(storage_file=self.storage_file)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, content)

    def test_market_report_generator_get_raw_stream_dump_none_path(self) -> None:
        gen = MarketReportGenerator(storage_file="")
        gen.storage_file = None  # type: ignore
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, "{}")

    def test_generate_market_report_wrapper(self) -> None:
        price = round(random.uniform(5.0, 50.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        report = generate_market_report(storage_file=self.storage_file, symbol=self.symbol)
        self.assertIn(self.symbol, report)
        self.assertIn(str(price), report)

    def test_run_market_telegram_pipeline(self) -> None:
        price = round(random.uniform(100.0, 200.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.telegram_token
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("symbol"), self.symbol)
        self.assertEqual(result.get("price"), price)
        self.assertEqual(result.get("chat_id"), self.chat_id)
        self.assertEqual(result.get("url"), self.url)

    def test_run_pipeline(self) -> None:
        price = round(random.uniform(1.0, 10.0), 2)
        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store(symbol=self.symbol, price=price)

        success = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(success)

    def test_start_new_and_start_ened(self) -> None:
        res_new = start_new(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_new)

        res_ened = start_ened(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertTrue(res_ened)

    def test_export_audit_logs_valid_dict(self) -> None:
        valid_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(valid_data, f)

        res = export_audit_logs(storage_file=self.storage_file)
        self.assertTrue(res)

    def test_export_audit_logs_empty(self) -> None:
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("   ")

        res = export_audit_logs(storage_file=self.storage_file)
        self.assertFalse(res)

    def test_export_audit_logs_non_existent(self) -> None:
        non_existent = f"missing_{uuid.uuid4().hex}.json"
        res = export_audit_logs(storage_file=non_existent)
        self.assertFalse(res)

    def test_market_parser_io_bytes_mocking(self) -> None:
        dummy_data = json.dumps({self.symbol: 999.99})
        m = mock_open(read_data=dummy_data)
        with patch("builtins.open", m):
            parser = MarketParser(storage_file=self.storage_file)
            parser.fetch_and_store(self.symbol, 123.45)

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps({self.symbol: 777.77}))):
                data = parser.load_data(self.storage_file)
                self.assertEqual(data.get(self.symbol), 777.77)


if __name__ == "__main__":
    unittest.main()