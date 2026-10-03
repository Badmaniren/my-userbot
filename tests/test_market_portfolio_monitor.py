import io
import json
import os
import random
import shutil
import string
import tempfile
import unittest
from unittest.mock import patch, MagicMock

try:
    from skills import market_portfolio_monitor as mpm
except ImportError:
    import market_portfolio_monitor as mpm


class TestMarketPortfolioMonitor(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix=f"test_mpm_{uuid_hex()}_")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _generate_random_symbol(self):
        return "".join(random.choices(string.ascii_uppercase, k=random.randint(3, 6)))

    def _generate_random_price(self):
        return round(random.uniform(10.0, 50000.0), random.randint(2, 6))

    def _generate_random_path(self):
        return os.path.join(self.test_dir, f"storage_{uuid_hex()}.json")

    def _generate_random_url(self):
        domain = "".join(random.choices(string.ascii_lowercase, k=8))
        path = "".join(random.choices(string.ascii_lowercase, k=6))
        return f"https://{domain}.org/api/{path}"

    def _generate_random_token(self):
        prefix = random.randint(100000, 999999)
        suffix = uuid_hex()
        return f"bot{prefix}:{suffix}"

    def test_market_parser_load_data_nonexistent_file(self):
        nonexistent_path = self._generate_random_path()
        parser = mpm.MarketParser(storage_file=nonexistent_path)
        result = parser.load_data(nonexistent_path)
        self.assertIsNone(result)

    def test_market_parser_load_data_empty_file(self):
        file_path = self._generate_random_path()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(random.choice(["", "   ", "\n\t  \n"]))
        parser = mpm.MarketParser(storage_file=file_path)
        result = parser.load_data(file_path)
        self.assertEqual(result, {})

    def test_market_parser_load_data_valid_json(self):
        file_path = self._generate_random_path()
        sym = self._generate_random_symbol()
        price = self._generate_random_price()
        expected_data = {sym: price, uuid_hex(): random.randint(1, 1000)}
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(expected_data, f)

        parser = mpm.MarketParser(storage_file=file_path)
        loaded = parser.load_data(file_path)
        self.assertEqual(loaded, expected_data)
        self.assertEqual(loaded[sym], price)

    def test_market_parser_load_data_unterminated_json_raises(self):
        file_path = self._generate_random_path()
        corrupted_content = f'{{"{self._generate_random_symbol()}": {self._generate_random_price()}'
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(corrupted_content)

        parser = mpm.MarketParser(storage_file=file_path)
        with self.assertRaises(json.JSONDecodeError):
            parser.load_data(file_path)

    def test_market_parser_load_data_malformed_syntax_returns_none(self):
        file_path = self._generate_random_path()
        bad_content = f"INVALID_DATA_{uuid_hex()} = [123, 456"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(bad_content)

        parser = mpm.MarketParser(storage_file=file_path)
        result = parser.load_data(file_path)
        self.assertIsNone(result)

    def test_market_parser_fetch_and_store_fresh_and_update(self):
        file_path = self._generate_random_path()
        parser = mpm.MarketParser(storage_file=file_path)

        sym1 = self._generate_random_symbol()
        price1 = self._generate_random_price()
        parser.fetch_and_store(symbol=sym1, price=price1)

        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get(sym1), price1)

        sym2 = self._generate_random_symbol()
        price2 = self._generate_random_price()
        parser.fetch_and_store(symbol=sym2, price=price2)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get(sym1), price1)
        self.assertEqual(data.get(sym2), price2)

    def test_market_parser_fetch_and_store_overwrites_corrupted_file(self):
        file_path = self._generate_random_path()
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"corrupt_noise_{uuid_hex()}")

        parser = mpm.MarketParser(storage_file=file_path)
        sym = self._generate_random_symbol()
        price = self._generate_random_price()
        parser.fetch_and_store(symbol=sym, price=price)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data, {sym: price})

    def test_market_report_generator_symbol_present(self):
        file_path = self._generate_random_path()
        sym = self._generate_random_symbol()
        price = self._generate_random_price()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({sym: price}, f)

        gen = mpm.MarketReportGenerator(storage_file=file_path)
        report = gen.generate_symbol_report(symbol=sym)
        self.assertEqual(report, f"Report for {sym}: {price}")

    def test_market_report_generator_symbol_absent(self):
        file_path = self._generate_random_path()
        sym_in_file = self._generate_random_symbol()
        target_sym = sym_in_file + "_ABSENT"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({sym_in_file: self._generate_random_price()}, f)

        gen = mpm.MarketReportGenerator(storage_file=file_path)
        report = gen.generate_symbol_report(symbol=target_sym)
        self.assertEqual(report, f"Report for {target_sym}: No data")

    def test_market_report_generator_raw_stream_dump(self):
        file_path = self._generate_random_path()
        random_raw = f'{{"entropy": "{uuid_hex()}", "val": {random.randint(100, 999)}}}'
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(random_raw)

        gen = mpm.MarketReportGenerator(storage_file=file_path)
        dump = gen.get_raw_stream_dump()
        self.assertEqual(dump, random_raw)

        missing_path = self._generate_random_path()
        missing_gen = mpm.MarketReportGenerator(storage_file=missing_path)
        self.assertEqual(missing_gen.get_raw_stream_dump(), "{}")

    def test_generate_market_report_function(self):
        file_path = self._generate_random_path()
        sym = self._generate_random_symbol()
        price = self._generate_random_price()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({sym: price}, f)

        report = mpm.generate_market_report(storage_file=file_path, symbol=sym)
        self.assertEqual(report, f"Report for {sym}: {price}")

    def test_run_market_telegram_pipeline_existing_and_missing(self):
        file_path = self._generate_random_path()
        sym = self._generate_random_symbol()
        price = self._generate_random_price()
        chat_id = random.randint(100000, 99999999)
        url = self._generate_random_url()
        token = self._generate_random_token()

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({sym: price}, f)

        res = mpm.run_market_telegram_pipeline(
            storage_file=file_path,
            symbol=sym,
            chat_id=chat_id,
            url=url,
            telegram_token=token,
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["symbol"], sym)
        self.assertEqual(res["price"], price)
        self.assertEqual(res["chat_id"], chat_id)
        self.assertEqual(res["url"], url)

        other_sym = sym + "_NOT_THERE"
        res_other = mpm.run_market_telegram_pipeline(
            storage_file=file_path,
            symbol=other_sym,
            chat_id=chat_id,
            url=url,
            telegram_token=token,
        )
        self.assertEqual(res_other["price"], 0.0)

    def test_export_audit_logs_matrix(self):
        self.assertFalse(mpm.export_audit_logs(None))

        nonexistent = self._generate_random_path()
        self.assertFalse(mpm.export_audit_logs(nonexistent))

        empty_path = self._generate_random_path()
        with open(empty_path, "w", encoding="utf-8") as f:
            f.write("   \n")
        self.assertFalse(mpm.export_audit_logs(empty_path))

        unterminated_path = self._generate_random_path()
        with open(unterminated_path, "w", encoding="utf-8") as f:
            f.write(f'{{"key": "{uuid_hex()}"')
        self.assertFalse(mpm.export_audit_logs(unterminated_path))

        malformed_path = self._generate_random_path()
        with open(malformed_path, "w", encoding="utf-8") as f:
            f.write(f"not_json_{uuid_hex()}")
        self.assertFalse(mpm.export_audit_logs(malformed_path))

        valid_path = self._generate_random_path()
        with open(valid_path, "w", encoding="utf-8") as f:
            json.dump({uuid_hex(): random.randint(1, 100)}, f)
        self.assertTrue(mpm.export_audit_logs(valid_path))

    def test_run_pipeline_end_to_end(self):
        file_path = self._generate_random_path()
        sym = self._generate_random_symbol()
        initial_price = self._generate_random_price()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({sym: initial_price}, f)

        url = self._generate_random_url()
        token = self._generate_random_token()
        chat_id = random.randint(10000, 999999)

        result = mpm.run_pipeline(
            symbol=sym,
            url=url,
            telegram_token=token,
            chat_id=chat_id,
            storage_file=file_path,
        )
        self.assertTrue(result)

        with open(file_path, "r", encoding="utf-8") as f:
            updated_data = json.load(f)
        self.assertEqual(updated_data[sym], initial_price)

    def test_start_new_and_start_ened_aliases(self):
        file_path = self._generate_random_path()
        sym = self._generate_random_symbol()
        url = self._generate_random_url()
        token = self._generate_random_token()
        chat_id = random.randint(1000, 99999)

        res_new = mpm.start_new(
            symbol=sym,
            url=url,
            telegram_token=token,
            chat_id=chat_id,
            storage_file=file_path,
        )
        self.assertTrue(res_new)

        sym2 = self._generate_random_symbol()
        res_ened = mpm.start_ened(
            symbol=sym2,
            url=url,
            telegram_token=token,
            chat_id=chat_id,
            storage_file=file_path,
        )
        self.assertTrue(res_ened)

    def test_stream_reading_via_mock(self):
        file_path = self._generate_random_path()
        sym = self._generate_random_symbol()
        random_price = self._generate_random_price()
        payload = json.dumps({sym: random_price}).encode("utf-8")

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open") as mock_open:
                mock_file = io.BytesIO(payload)
                mock_text_stream = io.StringIO(payload.decode("utf-8"))
                mock_open.return_value.__enter__.return_value = mock_text_stream

                parser = mpm.MarketParser(storage_file=file_path)
                data = parser.load_data(file_path)
                self.assertIsNotNone(data)
                self.assertEqual(data.get(sym), random_price)


def uuid_hex():
    import uuid
    return uuid.uuid4().hex


if __name__ == "__main__":
    unittest.main()