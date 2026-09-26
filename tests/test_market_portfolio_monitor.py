import unittest
from unittest.mock import patch
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
    export_audit_logs
)


class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        self.random_price = round(random.uniform(10.0, 1500.0), 2)
        self.random_chat_id = str(random.randint(100000, 999999))
        self.random_url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        self.random_token = f"{random.randint(100,999)}:{uuid.uuid4().hex[:10]}"

    def tearDown(self):
        if os.path.exists(self.random_storage):
            try:
                os.remove(self.random_storage)
            except OSError:
                pass

    def test_market_parser_fetch_and_load(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        self.assertTrue(os.path.exists(self.random_storage))
        loaded_data = parser.load_data(self.random_storage)
        self.assertIsInstance(loaded_data, dict)
        self.assertIn(self.random_symbol, loaded_data)
        self.assertEqual(loaded_data[self.random_symbol], self.random_price)

    def test_market_parser_load_invalid_json(self):
        garbage_data = uuid.uuid4().bytes
        with open(self.random_storage, "wb") as f:
            f.write(garbage_data)

        parser = MarketParser(storage_file=self.random_storage)
        loaded_data = parser.load_data(self.random_storage)
        self.assertIsNone(loaded_data)

    def test_market_parser_load_nonexistent(self):
        non_existent_file = f"{uuid.uuid4().hex}.json"
        parser = MarketParser(storage_file=non_existent_file)
        loaded_data = parser.load_data(non_existent_file)
        self.assertIsNone(loaded_data)

    def test_market_report_generator_success(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        gen = MarketReportGenerator(storage_file=self.random_storage)
        report = gen.generate_symbol_report(self.random_symbol)
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(self.random_price), report)

    def test_market_report_generator_no_data(self):
        gen = MarketReportGenerator(storage_file=self.random_storage)
        report = gen.generate_symbol_report(self.random_symbol)
        self.assertIn(self.random_symbol, report)
        self.assertIn("No data", report)

    def test_market_report_generator_raw_stream_dump(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        gen = MarketReportGenerator(storage_file=self.random_storage)
        raw_dump = gen.get_raw_stream_dump()
        self.assertIn(self.random_symbol, raw_dump)
        self.assertIn(str(self.random_price), raw_dump)

    def test_market_report_generator_raw_stream_dump_io_error(self):
        gen = MarketReportGenerator(storage_file=self.random_storage)
        with patch("builtins.open", side_effect=IOError("Disk explosion")):
            raw_dump = gen.get_raw_stream_dump()
            self.assertEqual(raw_dump, "{}")

    def test_generate_market_report_wrapper(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        report = generate_market_report(storage_file=self.random_storage, symbol=self.random_symbol)
        self.assertIn(self.random_symbol, report)
        self.assertIn(str(self.random_price), report)

    def test_run_market_telegram_pipeline(self):
        parser = MarketParser(storage_file=self.random_storage)
        parser.fetch_and_store(symbol=self.random_symbol, price=self.random_price)

        result = run_market_telegram_pipeline(
            storage_file=self.random_storage,
            symbol=self.random_symbol,
            chat_id=self.random_chat_id,
            url=self.random_url,
            telegram_token=self.random_token
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("symbol"), self.random_symbol)
        self.assertEqual(result.get("price"), self.random_price)
        self.assertEqual(result.get("chat_id"), self.random_chat_id)
        self.assertEqual(result.get("url"), self.random_url)

    def test_export_audit_logs_valid(self):
        random_content = uuid.uuid4().hex
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write(random_content)

        res = export_audit_logs(storage_file=self.random_storage)
        self.assertTrue(res)

    def test_export_audit_logs_empty(self):
        with open(self.random_storage, "w", encoding="utf-8") as f:
            f.write("")

        res = export_audit_logs(storage_file=self.random_storage)
        self.assertFalse(res)

    def test_export_audit_logs_nonexistent(self):
        non_file = f"{uuid.uuid4().hex}.log"
        res = export_audit_logs(storage_file=non_file)
        self.assertFalse(res)

    def test_export_audit_logs_none(self):
        res = export_audit_logs(storage_file=None)
        self.assertFalse(res)

    def test_export_audit_logs_exception(self):
        with patch("builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")):
            res = export_audit_logs(storage_file=self.random_storage)
            self.assertFalse(res)

    def test_run_pipeline(self):
        with patch("skills.market_portfolio_monitor.run_market_telegram_pipeline") as mock_tg:
            mock_tg.return_value = {"status": "success"}
            res = run_pipeline(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage
            )
            self.assertTrue(res)
            mock_tg.assert_called_once()

    def test_start_new(self):
        with patch("skills.market_portfolio_monitor.run_pipeline") as mock_run:
            mock_run.return_value = True
            res = start_new(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage
            )
            self.assertTrue(res)
            mock_run.assert_called_once()

    def test_start_ened(self):
        with patch("skills.market_portfolio_monitor.start_new") as mock_start:
            mock_start.return_value = True
            res = start_ened(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id,
                storage_file=self.random_storage
            )
            self.assertTrue(res)
            mock_start.assert_called_once()

    def test_stream_bytes_io_mock(self):
        random_garbage = io.BytesIO(uuid.uuid4().bytes)
        with patch("builtins.open", return_value=random_garbage):
            parser = MarketParser(storage_file=self.random_storage)
            loaded = parser.load_data(self.random_storage)
            self.assertIsNone(loaded)


if __name__ == "__main__":
    unittest.main()