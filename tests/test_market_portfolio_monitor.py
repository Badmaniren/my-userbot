import unittest
import os
import json
import tempfile
import io
from skills.market_portfolio_monitor import (
    MarketPortfolioMonitor,
    market_portfolio_monitor,
    MarketParser,
    MarketReportGenerator,
    run_pipeline,
    start_new,
    start_ened,
    generate_market_report,
    run_market_telegram_pipeline,
    export_audit_logs,
)


class TestMarketPortfolioMonitorUnit(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, "test_storage.json")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_market_portfolio_monitor_init_and_alias(self):
        monitor = MarketPortfolioMonitor(storage_file=self.storage_file)
        self.assertEqual(monitor.storage_file, self.storage_file)
        self.assertEqual(market_portfolio_monitor, MarketPortfolioMonitor)

    def test_load_macro_state_from_file_valid_and_invalid(self):
        self.assertEqual(MarketPortfolioMonitor.load_macro_state_from_file(None), {})
        self.assertEqual(MarketPortfolioMonitor.load_macro_state_from_file("/nonexistent/file.json"), {})

        # Empty file
        with open(self.storage_file, "w") as f:
            f.write("")
        self.assertEqual(MarketPortfolioMonitor.load_macro_state_from_file(self.storage_file), {})

        # Valid JSON
        valid_data = {"liquidity_score": 0.85, "macro_index": 1.2}
        with open(self.storage_file, "w") as f:
            json.dump(valid_data, f)
        self.assertEqual(MarketPortfolioMonitor.load_macro_state_from_file(self.storage_file), valid_data)

        # Corrupted JSON
        with open(self.storage_file, "w") as f:
            f.write("{invalid_json: 123")
        self.assertEqual(MarketPortfolioMonitor.load_macro_state_from_file(self.storage_file), {})

    def test_assess_portfolio_liquidity_state(self):
        monitor = MarketPortfolioMonitor()

        # None / Empty
        res = monitor.assess_portfolio_liquidity_state(None)
        self.assertEqual(res["status"], "unknown")
        self.assertEqual(res["risk_level"], "high")

        # High liquidity
        res = monitor.assess_portfolio_liquidity_state({"liquidity_score": 0.9})
        self.assertEqual(res["status"], "assessed")
        self.assertEqual(res["liquidity_score"], 0.9)
        self.assertEqual(res["risk_level"], "low")

        # Moderate liquidity
        res = monitor.assess_portfolio_liquidity_state({"liquidity_score": 0.5})
        self.assertEqual(res["risk_level"], "moderate")

        # Low liquidity
        res = monitor.assess_portfolio_liquidity_state({"liquidity_score": 0.2})
        self.assertEqual(res["risk_level"], "high")

        # List input fallback
        res = monitor.assess_portfolio_liquidity_state([1, 2, 3, 4, 5])
        self.assertEqual(res["liquidity_score"], 0.5)
        self.assertEqual(res["risk_level"], "moderate")

    def test_ingest_and_monitor(self):
        monitor = MarketPortfolioMonitor()
        # Non-existent file
        res = monitor.ingest_and_monitor("/nonexistent/path.json")
        self.assertEqual(res["status"], "error")

        # Valid file
        valid_data = {"liquidity_score": 0.95}
        with open(self.storage_file, "w") as f:
            json.dump(valid_data, f)

        res = monitor.ingest_and_monitor(self.storage_file)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["data"], valid_data)
        self.assertEqual(res["liquidity_state"]["risk_level"], "low")

    def test_get_portfolio_liquidity(self):
        monitor = MarketPortfolioMonitor(storage_file=self.storage_file)

        # Empty portfolio_id
        self.assertEqual(monitor.get_portfolio_liquidity(""), 0.0)

        # File does not exist -> default fallback 1.0
        self.assertEqual(monitor.get_portfolio_liquidity("P1"), 1.0)

        # File with float portfolio liquidity
        with open(self.storage_file, "w") as f:
            json.dump({"P1": 150.5, "P2": {"liquidity": 0.75}}, f)

        self.assertEqual(monitor.get_portfolio_liquidity("P1"), 150.5)
        self.assertEqual(monitor.get_portfolio_liquidity("P2"), 0.75)

    def test_market_parser_stream_and_decode(self):
        parser = MarketParser(self.storage_file)
        self.assertEqual(parser.load_data(None), None)
        self.assertEqual(parser.load_data(os.path.join(self.test_dir.name, "missing.json")), {})

        # Parse stream as string
        stream_str = '{"AAPL": 150.0}'
        parsed = parser.parse_stream(stream_str)
        self.assertEqual(parsed, {"AAPL": 150.0})

        # Parse stream as file-like object
        stream_io = io.StringIO('{"GOOG": 2800.0}')
        parsed_io = parser.parse_stream(stream_io)
        self.assertEqual(parsed_io, {"GOOG": 2800.0})

        # Parse stream invalid
        self.assertEqual(parser.parse_stream(None), {})
        self.assertEqual(parser.parse_stream("invalid json"), {})

    def test_market_report_generator(self):
        report_gen = MarketReportGenerator(storage_file=self.storage_file)
        self.assertEqual(report_gen.get_raw_stream_dump(), "{}")

        parser = MarketParser(storage_file=self.storage_file)
        parser.fetch_and_store("BTC", 50000.0)

        self.assertIn("BTC", report_gen.get_raw_stream_dump())

        report_str = generate_market_report(self.storage_file, "BTC")
        self.assertIn("50000.0", report_str)

        no_data_str = generate_market_report(self.storage_file, "ETH")
        self.assertIn("No data", no_data_str)

    def test_pipeline_and_helpers(self):
        res = run_pipeline(
            symbol="TEST",
            url="https://test.local",
            telegram_token="token123",
            chat_id="12345",
            storage_file=self.storage_file,
        )
        self.assertTrue(res)

        res_start = start_new("TEST", "https://test.local", "token123", "12345", self.storage_file)
        self.assertTrue(res_start)

        res_start_ened = start_ened("TEST", "https://test.local", "token123", "12345", self.storage_file)
        self.assertTrue(res_start_ened)

        tg_res = run_market_telegram_pipeline(self.storage_file, "TEST", "12345", "https://test.local", "token123")
        self.assertEqual(tg_res["status"], "success")
        self.assertEqual(tg_res["symbol"], "TEST")

    def test_export_audit_logs(self):
        self.assertFalse(export_audit_logs(None))
        self.assertFalse(export_audit_logs("/nonexistent/file.json"))

        # Empty file
        with open(self.storage_file, "w") as f:
            f.write("")
        self.assertFalse(export_audit_logs(self.storage_file))

        # Truncated JSON
        with open(self.storage_file, "w") as f:
            f.write("{\"key\": \"value\"")
        self.assertTrue(export_audit_logs(self.storage_file))

        # Valid JSON
        with open(self.storage_file, "w") as f:
            json.dump({"audit": True}, f)
        self.assertTrue(export_audit_logs(self.storage_file))


if __name__ == "__main__":
    unittest.main()
