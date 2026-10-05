import io
import json
import os
import random
import string
import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch

try:
    from skills import market_portfolio_monitor as mpm
except ImportError:
    import market_portfolio_monitor as mpm


def _rand_str(length=None):
    if length is None:
        length = random.randint(8, 20)
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _rand_symbol():
    return "".join(random.choices(string.ascii_uppercase, k=random.randint(3, 5)))


def _rand_float():
    return round(random.uniform(1.0, 10000.0), 4)


def _rand_int():
    return random.randint(1000, 999999)


def _rand_url():
    return f"https://{_rand_str(10)}.org/api/{_rand_str(6)}"


class TestMarketParser(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_data_none_storage(self):
        parser = mpm.MarketParser(storage_file=None)
        res = parser.load_data(None)
        self.assertIsNone(res)

    def test_load_data_nonexistent_file(self):
        fake_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        parser = mpm.MarketParser(storage_file=fake_path)
        res = parser.load_data(fake_path)
        self.assertEqual(res, {})

    def test_load_data_empty_file(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("   \n\t  ")
        parser = mpm.MarketParser(storage_file=file_path)
        res = parser.load_data(file_path)
        self.assertEqual(res, {})

    def test_load_data_truncated_json_object(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f'{{"{_rand_symbol()}": {_rand_float()}')
        parser = mpm.MarketParser(storage_file=file_path)
        res = parser.load_data(file_path)
        self.assertEqual(res, {})

    def test_load_data_non_dict_json(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        rand_list = [_rand_str(), _rand_float()]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(rand_list, f)
        parser = mpm.MarketParser(storage_file=file_path)
        res = parser.load_data(file_path)
        self.assertEqual(res, {})

    def test_load_data_corrupt_content(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"MALFORMED_GARBAGE_{_rand_str()}")
        parser = mpm.MarketParser(storage_file=file_path)
        res = parser.load_data(file_path)
        self.assertEqual(res, {})

    def test_load_data_valid_payload(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        expected_sym = _rand_symbol()
        expected_price = _rand_float()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({expected_sym: expected_price}, f)
        parser = mpm.MarketParser(storage_file=file_path)
        res = parser.load_data(file_path)
        self.assertIn(expected_sym, res)
        self.assertEqual(res[expected_sym], expected_price)

    def test_load_data_bytes_like_stream_simulation(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        sym = _rand_symbol()
        val = _rand_float()
        raw_bytes = json.dumps({sym: val}).encode("utf-8")

        mock_f = MagicMock()
        mock_f.read.return_value = io.BytesIO(raw_bytes)
        parser = mpm.MarketParser(storage_file=file_path)

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", return_value=mock_f):
                mock_f.__enter__.return_value = mock_f
                res = parser.load_data(file_path)
                self.assertIsInstance(res, dict)
                self.assertEqual(res.get(sym), val)

    def test_fetch_and_store_creates_file_if_not_present(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        parser = mpm.MarketParser(storage_file=file_path)
        sym = _rand_symbol()
        price = _rand_float()

        parser.fetch_and_store(symbol=sym, price=price)
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, "r", encoding="utf-8") as f:
            stored = json.load(f)
        self.assertEqual(stored, {sym: price})

    def test_fetch_and_store_updates_existing_content(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        initial_sym = _rand_symbol()
        initial_price = _rand_float()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({initial_sym: initial_price}, f)

        parser = mpm.MarketParser(storage_file=file_path)
        new_sym = _rand_symbol()
        new_price = _rand_float()
        parser.fetch_and_store(symbol=new_sym, price=new_price)

        with open(file_path, "r", encoding="utf-8") as f:
            updated = json.load(f)
        self.assertEqual(updated[initial_sym], initial_price)
        self.assertEqual(updated[new_sym], new_price)

    def test_fetch_and_store_overwrites_corrupt_file(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f'{{"broken": "{_rand_str()}"')

        parser = mpm.MarketParser(storage_file=file_path)
        sym = _rand_symbol()
        price = _rand_float()
        parser.fetch_and_store(symbol=sym, price=price)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data, {sym: price})

    def test_fetch_and_store_with_none_storage(self):
        parser = mpm.MarketParser(storage_file=None)
        sym = _rand_symbol()
        price = _rand_float()
        # Should not raise exception
        parser.fetch_and_store(symbol=sym, price=price)


class TestMarketReportGenerator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generate_symbol_report_found(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        sym = _rand_symbol()
        price = _rand_float()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({sym: price}, f)

        generator = mpm.MarketReportGenerator(storage_file=file_path)
        report = generator.generate_symbol_report(sym)
        self.assertEqual(report, f"Report for {sym}: {price}")

    def test_generate_symbol_report_missing_symbol(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        sym_in_db = _rand_symbol()
        sym_query = _rand_symbol() + "_OTHER"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({sym_in_db: _rand_float()}, f)

        generator = mpm.MarketReportGenerator(storage_file=file_path)
        report = generator.generate_symbol_report(sym_query)
        self.assertEqual(report, f"Report for {sym_query}: No data")

    def test_get_raw_stream_dump_none_path(self):
        generator = mpm.MarketReportGenerator(storage_file=None)
        self.assertEqual(generator.get_raw_stream_dump(), "{}")

    def test_get_raw_stream_dump_nonexistent_file(self):
        fake_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        generator = mpm.MarketReportGenerator(storage_file=fake_path)
        self.assertEqual(generator.get_raw_stream_dump(), "{}")

    def test_get_raw_stream_dump_existing_file(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        payload = f'{{"random_key_{_rand_str()}": {_rand_int()}}}'
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(payload)

        generator = mpm.MarketReportGenerator(storage_file=file_path)
        self.assertEqual(generator.get_raw_stream_dump(), payload)

    def test_get_raw_stream_dump_decode_handling(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        raw_text = f"raw_data_{_rand_str()}"

        mock_f = MagicMock()
        mock_f.read.return_value = io.BytesIO(raw_text.encode("utf-8"))

        generator = mpm.MarketReportGenerator(storage_file=file_path)
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", return_value=mock_f):
                mock_f.__enter__.return_value = mock_f
                dump = generator.get_raw_stream_dump()
                self.assertEqual(dump, raw_text)


class TestStandaloneFunctionsAndPipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generate_market_report_helper(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        sym = _rand_symbol()
        price = _rand_float()
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({sym: price}, f)

        res = mpm.generate_market_report(storage_file=file_path, symbol=sym)
        self.assertEqual(res, f"Report for {sym}: {price}")

    def test_run_market_telegram_pipeline_existing_symbol(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        sym = _rand_symbol()
        price = _rand_float()
        chat_id = _rand_int()
        url = _rand_url()
        token = _rand_str(32)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({sym: price}, f)

        res = mpm.run_market_telegram_pipeline(
            storage_file=file_path,
            symbol=sym,
            chat_id=chat_id,
            url=url,
            telegram_token=token
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["symbol"], sym)
        self.assertEqual(res["price"], price)
        self.assertEqual(res["chat_id"], chat_id)
        self.assertEqual(res["url"], url)

    def test_run_market_telegram_pipeline_missing_symbol(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        sym = _rand_symbol()
        chat_id = _rand_int()
        url = _rand_url()

        res = mpm.run_market_telegram_pipeline(
            storage_file=file_path,
            symbol=sym,
            chat_id=chat_id,
            url=url,
            telegram_token=_rand_str()
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["symbol"], sym)
        self.assertEqual(res["price"], 0.0)

    def test_run_pipeline_end_to_end(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        sym = _rand_symbol()
        initial_price = _rand_float()
        url = _rand_url()
        token = _rand_str(16)
        chat_id = _rand_int()

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({sym: initial_price}, f)

        status = mpm.run_pipeline(
            symbol=sym,
            url=url,
            telegram_token=token,
            chat_id=chat_id,
            storage_file=file_path
        )
        self.assertTrue(status)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn(sym, data)
        self.assertEqual(data[sym], initial_price)

    def test_run_pipeline_fresh_symbol_defaults_to_zero(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        sym = _rand_symbol()
        url = _rand_url()
        token = _rand_str(16)
        chat_id = _rand_int()

        status = mpm.run_pipeline(
            symbol=sym,
            url=url,
            telegram_token=token,
            chat_id=chat_id,
            storage_file=file_path
        )
        self.assertTrue(status)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn(sym, data)
        self.assertEqual(data[sym], 0.0)

    def test_aliases_start_new_and_start_ened(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.json")
        sym = _rand_symbol()
        url = _rand_url()
        token = _rand_str(12)
        chat_id = _rand_int()

        res_new = mpm.start_new(
            symbol=sym,
            url=url,
            telegram_token=token,
            chat_id=chat_id,
            storage_file=file_path
        )
        self.assertTrue(res_new)

        sym2 = _rand_symbol()
        res_ened = mpm.start_ened(
            symbol=sym2,
            url=url,
            telegram_token=token,
            chat_id=chat_id,
            storage_file=file_path
        )
        self.assertTrue(res_ened)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn(sym, data)
        self.assertIn(sym2, data)


class TestExportAuditLogs(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_audit_logs_none_or_missing(self):
        self.assertFalse(mpm.export_audit_logs(None))
        fake_path = os.path.join(self.base_path, f"{_rand_str()}.log")
        self.assertFalse(mpm.export_audit_logs(fake_path))

    def test_export_audit_logs_empty_file(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.log")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("   \n")
        self.assertFalse(mpm.export_audit_logs(file_path))

    def test_export_audit_logs_valid_dict_json(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.log")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({_rand_str(): _rand_int()}, f)
        self.assertTrue(mpm.export_audit_logs(file_path))

    def test_export_audit_logs_valid_non_dict_json(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.log")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([_rand_str(), _rand_int()], f)
        self.assertFalse(mpm.export_audit_logs(file_path))

    def test_export_audit_logs_truncated_braces(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.log")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f'{{"audit_trail_{_rand_str()}":')
        self.assertTrue(mpm.export_audit_logs(file_path))

    def test_export_audit_logs_corrupted_json_exception(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.log")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"INVALID_RAW_LOG_ENTRY_{_rand_str()}")
        self.assertTrue(mpm.export_audit_logs(file_path))

    def test_export_audit_logs_with_stream_object(self):
        file_path = os.path.join(self.base_path, f"{_rand_str()}.log")
        payload = f'{{"trace_id": "{_rand_str()}"}}'
        mock_f = MagicMock()
        mock_f.read.return_value = io.BytesIO(payload.encode("utf-8"))

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", return_value=mock_f):
                mock_f.__enter__.return_value = mock_f
                res = mpm.export_audit_logs(file_path)
                self.assertTrue(res)


if __name__ == "__main__":
    unittest.main()