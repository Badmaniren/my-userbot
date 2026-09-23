import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_monitor import (
    run_pipeline,
    start_new,
    MarketParser,
    MarketReportGenerator,
    generate_market_report,
    run_market_telegram_pipeline
)

class TestMarketPortfolioMonitor(unittest.TestCase):

    def test_market_parser_fetch_and_store_success(self):
        rand_symbol = uuid.uuid4().hex[:8]
        rand_price = round(random.uniform(10.0, 1000.0), 2)
        rand_storage = f"{uuid.uuid4().hex}.json"

        mock_file_data = {}

        def mock_open_side_effect(file, mode="r", encoding=None):
            if "r" in mode:
                if not mock_file_data:
                    raise FileNotFoundError
                return io.StringIO(json.dumps(mock_file_data))
            elif "w" in mode:
                m = MagicMock()
                def write_side_effect(content):
                    nonlocal mock_file_data
                    mock_file_data = json.loads(content)
                m.write.side_effect = write_side_effect
                return m

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", side_effect=mock_open_side_effect):
                parser = MarketParser(storage_file=rand_storage)
                parser.fetch_and_store(symbol=rand_symbol, price=rand_price)

                self.assertIn(rand_symbol, mock_file_data)
                self.assertEqual(mock_file_data[rand_symbol], rand_price)

    def test_market_parser_load_data_missing_file(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        with patch("os.path.exists", return_value=False):
            parser = MarketParser(storage_file=rand_storage)
            result = parser.load_data(rand_storage)
            self.assertIsNone(result)

    def test_market_parser_load_data_valid(self):
        rand_symbol = uuid.uuid4().hex[:6]
        rand_val = random.randint(100, 500)
        rand_storage = f"{uuid.uuid4().hex}.json"
        dump_data = {rand_symbol: rand_val}

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", return_value=io.StringIO(json.dumps(dump_data))):
                parser = MarketParser(storage_file=rand_storage)
                res = parser.load_data(rand_storage)
                self.assertEqual(res.get(rand_symbol), rand_val)

    def test_market_report_generator_symbol_found(self):
        rand_symbol = uuid.uuid4().hex[:6]
        rand_val = round(random.uniform(1.0, 50.0), 4)
        rand_storage = f"{uuid.uuid4().hex}.json"
        dump_data = {rand_symbol: rand_val}

        with patch.object(MarketParser, "load_data", return_value=dump_data):
            gen = MarketReportGenerator(storage_file=rand_storage)
            report = gen.generate_symbol_report(symbol=rand_symbol)
            self.assertIn(rand_symbol, report)
            self.assertIn(str(rand_val), report)

    def test_market_report_generator_symbol_not_found(self):
        rand_symbol = uuid.uuid4().hex[:6]
        rand_other = uuid.uuid4().hex[:6]
        rand_storage = f"{uuid.uuid4().hex}.json"
        dump_data = {rand_other: 999.9}

        with patch.object(MarketParser, "load_data", return_value=dump_data):
            gen = MarketReportGenerator(storage_file=rand_storage)
            report = gen.generate_symbol_report(symbol=rand_symbol)
            self.assertIn("No data", report)

    def test_market_report_generator_get_raw_stream_dump(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_content = uuid.uuid4().hex

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", return_value=io.StringIO(rand_content)):
                gen = MarketReportGenerator(storage_file=rand_storage)
                stream = gen.get_raw_stream_dump()
                self.assertEqual(stream, rand_content)

    def test_market_report_generator_get_raw_stream_dump_missing(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        with patch("os.path.exists", return_value=False):
            gen = MarketReportGenerator(storage_file=rand_storage)
            stream = gen.get_raw_stream_dump()
            self.assertEqual(stream, "{}")

    def test_generate_market_report_proxy(self):
        rand_symbol = uuid.uuid4().hex[:6]
        rand_storage = f"{uuid.uuid4().hex}.json"
        
        with patch.object(MarketReportGenerator, "generate_symbol_report", return_value=rand_symbol) as mock_gen:
            res = generate_market_report(storage_file=rand_storage, symbol=rand_symbol)
            mock_gen.assert_called_once_with(symbol=rand_symbol)
            self.assertEqual(res, rand_symbol)

    def test_run_market_telegram_pipeline(self):
        rand_symbol = uuid.uuid4().hex[:6]
        rand_chat = str(random.randint(10000, 99999))
        rand_url = f"https://{uuid.uuid4().hex}.com/webhook"
        rand_token = uuid.uuid4().hex
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_price = random.random() * 100

        with patch.object(MarketParser, "load_data", return_value={rand_symbol: rand_price}):
            res = run_market_telegram_pipeline(
                storage_file=rand_storage,
                symbol=rand_symbol,
                chat_id=rand_chat,
                url=rand_url,
                telegram_token=rand_token
            )
            self.assertEqual(res["status"], "success")
            self.assertEqual(res["symbol"], rand_symbol)
            self.assertEqual(res["price"], rand_price)
            self.assertEqual(res["chat_id"], rand_chat)
            self.assertEqual(res["url"], rand_url)

    def test_run_pipeline_integration(self):
        rand_symbol = uuid.uuid4().hex[:6]
        rand_chat = str(random.randint(100, 500))
        rand_url = f"https://{uuid.uuid4().hex}.org"
        rand_token = uuid.uuid4().hex
        rand_storage = f"{uuid.uuid4().hex}.json"

        with patch.object(MarketParser, "fetch_and_store") as mock_fetch, \
             patch.object(MarketReportGenerator, "generate_symbol_report") as mock_rep, \
             patch("skills.market_portfolio_monitor.generate_market_report") as mock_gen_mkt, \
             patch("skills.market_portfolio_monitor.run_market_telegram_pipeline") as mock_tg:

            success = run_pipeline(
                symbol=rand_symbol,
                url=rand_url,
                telegram_token=rand_token,
                chat_id=rand_chat,
                storage_file=rand_storage
            )

            self.assertTrue(success)
            mock_fetch.assert_called_once_with(symbol=rand_symbol, price=0.0)
            mock_rep.assert_called_once_with(symbol=rand_symbol)
            mock_gen_mkt.assert_called_once_with(storage_file=rand_storage, symbol=rand_symbol)
            mock_tg.assert_called_once()

    def test_start_new_entrypoint(self):
        rand_symbol = uuid.uuid4().hex[:6]
        rand_chat = str(random.randint(100, 500))
        rand_url = f"https://{uuid.uuid4().hex}.net"
        rand_token = uuid.uuid4().hex
        rand_storage = f"{uuid.uuid4().hex}.json"

        with patch("skills.market_portfolio_monitor.run_pipeline", return_value=True) as mock_run:
            res = start_new(
                symbol=rand_symbol,
                url=rand_url,
                telegram_token=rand_token,
                chat_id=rand_chat,
                storage_file=rand_storage
            )
            self.assertTrue(res)
            mock_run.assert_called_once_with(
                symbol=rand_symbol,
                url=rand_url,
                telegram_token=rand_token,
                chat_id=rand_chat,
                storage_file=rand_storage
            )

if __name__ == "__main__":
    unittest.main()