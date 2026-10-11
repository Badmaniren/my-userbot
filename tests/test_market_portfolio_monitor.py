import unittest
from unittest.mock import patch
import json
import os
import io
import uuid
import random
from skills.market_portfolio_monitor import (
    run_pipeline,
    start_new,
    start_ened,
    MarketParser,
    MarketReportGenerator,
    generate_market_report,
    run_market_telegram_pipeline,
    export_audit_logs
)

class TestMarketPortfolioMonitor(unittest.TestCase):

    def test_run_pipeline_success(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        price = round(random.uniform(10.0, 5000.0), 2)
        url = f"https://{uuid.uuid4().hex[:8]}.com/api"
        telegram_token = uuid.uuid4().hex
        chat_id = str(random.randint(100000, 999999))
        storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"

        try:
            initial_data = {symbol: price}
            with open(storage_file, "w", encoding="utf-8") as f:
                json.dump(initial_data, f)

            res = run_pipeline(symbol, url, telegram_token, chat_id, storage_file)
            self.assertTrue(res)
        finally:
            if os.path.exists(storage_file):
                os.remove(storage_file)

    def test_start_new_and_ened_aliases(self):
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        price = round(random.uniform(1.0, 100.0), 2)
        url = f"https://{uuid.uuid4().hex[:8]}.org"
        telegram_token = uuid.uuid4().hex
        chat_id = str(random.randint(10000, 99999))
        storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"

        try:
            with open(storage_file, "w", encoding="utf-8") as f:
                json.dump({symbol: price}, f)

            res_new = start_new(symbol, url, telegram_token, chat_id, storage_file)
            res_ened = start_ened(symbol, url, telegram_token, chat_id, storage_file)
            
            self.assertTrue(res_new)
            self.assertTrue(res_ened)
        finally:
            if os.path.exists(storage_file):
                os.remove(storage_file)

    def test_market_parser_read_content_bytes(self):
        storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        parser = MarketParser(storage_file)
        
        rand_key = uuid.uuid4().hex[:6]
        rand_val = random.randint(100, 999)
        raw_bytes = json.dumps({rand_key: rand_val}).encode("utf-8")
        
        stream = io.BytesIO(raw_bytes)
        content = parser._read_content(stream)
        self.assertIn(rand_key, content)

    def test_market_parser_fetch_and_store_corrupted(self):
        storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        price = round(random.uniform(1.0, 50.0), 2)

        try:
            corrupted_str = "{invalid_json_stream_" + uuid.uuid4().hex
            with open(storage_file, "w", encoding="utf-8") as f:
                f.write(corrupted_str)

            parser = MarketParser(storage_file)
            parser.fetch_and_store(symbol, price)

            data = parser.load_data(storage_file)
            self.assertIsInstance(data, dict)
            self.assertEqual(data.get(symbol), price)
        finally:
            if os.path.exists(storage_file):
                os.remove(storage_file)

    def test_market_parser_load_data_edge_cases(self):
        parser = MarketParser(None)
        self.assertIsNone(parser.load_data(None))

        storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        try:
            parser_with_file = MarketParser(storage_file)
            self.assertEqual(parser_with_file.load_data(storage_file), {})

            with open(storage_file, "w", encoding="utf-8") as f:
                f.write("   ")
            self.assertEqual(parser_with_file.load_data(storage_file), {})

            corrupted_str = "{broken_json_" + uuid.uuid4().hex
            with open(storage_file, "w", encoding="utf-8") as f:
                f.write(corrupted_str)
            self.assertEqual(parser_with_file.load_data(storage_file), {})

            with open(storage_file, "w", encoding="utf-8") as f:
                json.dump([random.randint(1, 100)], f)
            self.assertEqual(parser_with_file.load_data(storage_file), {})
        finally:
            if os.path.exists(storage_file):
                os.remove(storage_file)

    def test_market_report_generator(self):
        storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        price = round(random.uniform(50.0, 150.0), 2)

        try:
            parser = MarketParser(storage_file)
            parser.fetch_and_store(symbol, price)

            gen = MarketReportGenerator(storage_file)
            report = gen.generate_symbol_report(symbol)
            self.assertIn(symbol, report)
            self.assertIn(str(price), report)

            missing_symbol = f"SYM_{uuid.uuid4().hex[:6]}"
            missing_report = gen.generate_symbol_report(missing_symbol)
            self.assertIn("No data", missing_report)

            raw_dump = gen.get_raw_stream_dump()
            self.assertIn(symbol, raw_dump)
        finally:
            if os.path.exists(storage_file):
                os.remove(storage_file)

    def test_market_report_generator_none_path(self):
        gen = MarketReportGenerator(None)
        self.assertEqual(gen.get_raw_stream_dump(), "{}")

    def test_generate_market_report_wrapper(self):
        storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        price = round(random.uniform(1.0, 10.0), 2)

        try:
            parser = MarketParser(storage_file)
            parser.fetch_and_store(symbol, price)

            rep = generate_market_report(storage_file, symbol)
            self.assertIn(symbol, rep)
        finally:
            if os.path.exists(storage_file):
                os.remove(storage_file)

    def test_run_market_telegram_pipeline(self):
        storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        price = round(random.uniform(200.0, 400.0), 2)
        chat_id = str(random.randint(100, 999))
        url = f"https://{uuid.uuid4().hex[:8]}.net"
        token = uuid.uuid4().hex

        try:
            parser = MarketParser(storage_file)
            parser.fetch_and_store(symbol, price)

            result = run_market_telegram_pipeline(storage_file, symbol, chat_id, url, token)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["symbol"], symbol)
            self.assertEqual(result["price"], price)
            self.assertEqual(result["chat_id"], chat_id)
            self.assertEqual(result["url"], url)
        finally:
            if os.path.exists(storage_file):
                os.remove(storage_file)

    def test_export_audit_logs(self):
        storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        try:
            self.assertFalse(export_audit_logs(None))
            self.assertFalse(export_audit_logs(storage_file))

            with open(storage_file, "w", encoding="utf-8") as f:
                f.write("   ")
            self.assertFalse(export_audit_logs(storage_file))

            corrupted_str = "{unbalanced_brace_" + uuid.uuid4().hex
            with open(storage_file, "w", encoding="utf-8") as f:
                f.write(corrupted_str)
            self.assertFalse(export_audit_logs(storage_file))

            with open(storage_file, "w", encoding="utf-8") as f:
                f.write("invalid_json_alt")
            self.assertFalse(export_audit_logs(storage_file))

            with open(storage_file, "w", encoding="utf-8") as f:
                json.dump([1, 2, 3], f)
            self.assertFalse(export_audit_logs(storage_file))

            with open(storage_file, "w", encoding="utf-8") as f:
                json.dump({uuid.uuid4().hex: random.randint(1, 10)}, f)
            self.assertTrue(export_audit_logs(storage_file))
        finally:
            if os.path.exists(storage_file):
                os.remove(storage_file)

    def test_market_parser_latin1_fallback(self):
        storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        price = round(random.uniform(1.0, 10.0), 2)

        try:
            payload = json.dumps({symbol: price}).encode("latin-1")
            with open(storage_file, "wb") as f:
                f.write(payload)

            parser = MarketParser(storage_file)
            data = parser.load_data(storage_file)
            self.assertEqual(data.get(symbol), price)
        finally:
            if os.path.exists(storage_file):
                os.remove(storage_file)
                
    def test_market_report_generator_latin1_fallback(self):
        storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        price = round(random.uniform(1.0, 10.0), 2)

        try:
            payload = json.dumps({symbol: price}).encode("latin-1")
            with open(storage_file, "wb") as f:
                f.write(payload)

            gen = MarketReportGenerator(storage_file)
            dump = gen.get_raw_stream_dump()
            self.assertIn(symbol, dump)
        finally:
            if os.path.exists(storage_file):
                os.remove(storage_file)

    def test_export_audit_logs_latin1_fallback(self):
        storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"
        try:
            payload = json.dumps({uuid.uuid4().hex: 123}).encode("latin-1")
            with open(storage_file, "wb") as f:
                f.write(payload)

            self.assertTrue(export_audit_logs(storage_file))
        finally:
            if os.path.exists(storage_file):
                os.remove(storage_file)

if __name__ == "__main__":
    unittest.main()