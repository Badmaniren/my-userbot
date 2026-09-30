import unittest
import json
import os
import uuid
import random
from unittest.mock import patch, mock_open
from skills.market_portfolio_monitor import (
    MarketParser,
    MarketReportGenerator,
    MarketPortfolioMonitor,
    market_portfolio_monitor,
    run_pipeline,
    export_audit_logs,
)


class TestMarketPortfolioMonitor(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = uuid.uuid4().hex[:8].upper()
        self.price = round(random.uniform(10.0, 1000.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_market_portfolio_monitor_calculate_drawdown(self):
        monitor = MarketPortfolioMonitor()
        self.assertEqual(monitor.calculate_drawdown([]), 0.0)
        self.assertAlmostEqual(monitor.calculate_drawdown([100.0, 120.0, 90.0]), (120.0 - 90.0) / 120.0)
        self.assertEqual(monitor.calculate_drawdown([0.0, -10.0]), 0.0)

    def test_market_portfolio_monitor_evaluate_portfolio_liquidity(self):
        monitor = MarketPortfolioMonitor()
        healthy_res = monitor.evaluate_portfolio_liquidity({"positions": ["AAPL", "GOOG"], "liquidity_score": 0.8})
        self.assertEqual(healthy_res["status"], "HEALTHY")
        self.assertEqual(healthy_res["liquidity_risk"], "LOW")
        self.assertEqual(healthy_res["positions_evaluated"], 2)

        illiquid_res = monitor.evaluate_portfolio_liquidity({"positions": ["PRIVATE_EQ"], "liquidity_score": 0.2})
        self.assertEqual(illiquid_res["status"], "ILLIQUID")
        self.assertEqual(illiquid_res["liquidity_risk"], "HIGH")

    def test_market_portfolio_monitor_entry_point_function(self):
        # Calling market_portfolio_monitor with no args returns instance
        instance = market_portfolio_monitor()
        self.assertIsInstance(instance, MarketPortfolioMonitor)

        # Calling with data evaluates liquidity
        res = market_portfolio_monitor({"positions": ["MSFT"], "liquidity_score": 0.9})
        self.assertIsInstance(res, dict)
        self.assertEqual(res["status"], "HEALTHY")

    def test_market_parser_fetch_and_store(self):
        parser = MarketParser(self.storage_file)
        test_data = {self.symbol: self.price}
        
        with patch("builtins.open", mock_open(read_data=json.dumps({}))) as mocked_file:
            parser.fetch_and_store(self.symbol, self.price)

            mocked_file.assert_called_with(self.storage_file, "w", encoding="utf-8")
            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            self.assertEqual(json.loads(written_data), test_data)

    def test_market_report_generator_logic(self):
        gen = MarketReportGenerator(self.storage_file)
        expected_report = f"Report for {self.symbol}: {self.price}"
        
        with patch("skills.market_portfolio_monitor.MarketParser.load_data") as mock_load:
            mock_load.return_value = {self.symbol: self.price}
            result = gen.generate_symbol_report(self.symbol)
            self.assertEqual(result, expected_report)

    def test_run_pipeline_execution_flow(self):
        url = f"https://{uuid.uuid4().hex}.com"
        token = uuid.uuid4().hex
        chat_id = str(random.randint(10000, 99999))
        
        with patch("skills.market_portfolio_monitor.MarketParser") as MockParser:
            with patch("skills.market_portfolio_monitor.MarketReportGenerator") as MockGen:
                with patch("skills.market_portfolio_monitor.generate_market_report") as mock_gen_mkt:
                    with patch("skills.market_portfolio_monitor.run_market_telegram_pipeline") as mock_tg:

                        instance = MockParser.return_value
                        instance.load_data.return_value = {self.symbol: self.price}

                        result = run_pipeline(self.symbol, url, token, chat_id, self.storage_file)

                        self.assertTrue(result)
                        instance.fetch_and_store.assert_called_once_with(symbol=self.symbol, price=self.price)
                        mock_tg.assert_called_once()

    def test_export_audit_logs_invalid_data(self):
        random_content = uuid.uuid4().hex
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=random_content)):
                result = export_audit_logs(self.storage_file)
                self.assertFalse(result)

    def test_export_audit_logs_valid_json(self):
        valid_data = json.dumps({uuid.uuid4().hex: random.random()})
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=valid_data)):
                result = export_audit_logs(self.storage_file)
                self.assertTrue(result)

    def test_parser_load_data_corrupted_file(self):
        parser = MarketParser(self.storage_file)
        corrupted_data = "!!!NOT_JSON!!!"
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=corrupted_data)):
                result = parser.load_data(self.storage_file)
                self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
