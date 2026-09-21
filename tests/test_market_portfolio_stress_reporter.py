import os
import unittest
import uuid
import random
import json
from unittest.mock import patch
from skills.market_parser import MarketParser
from skills.market_portfolio_stress_reporter import (
    StressReporter,
    PortfolioStressReporter,
    generate_stress_report,
    run_stress_reporting_pipeline,
    start_new,
)


class TestMarketPortfolioStressReporter(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_reporter_storage_{uuid.uuid4().hex}.json"
        self.symbol = f"TEST_SYM_{random.randint(100, 999)}"
        self.parser = MarketParser(self.storage_file)
        self.parser.fetch_and_store(self.symbol, 100.0)
        self.reporter = StressReporter(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_class_alias(self):
        self.assertIs(PortfolioStressReporter, StressReporter)

    def test_simulate_single_dict_data(self):
        result = self.reporter.simulate_single(self.symbol, 0.1)
        self.assertEqual(result["symbol"], self.symbol)
        self.assertEqual(result["shift"], 0.1)
        self.assertEqual(len(result["simulated_records"]), 1)
        self.assertEqual(result["simulated_records"][0]["price"], 110.0)

    def test_simulate_single_list_data(self):
        list_storage = f"test_list_storage_{uuid.uuid4().hex}.json"
        try:
            with open(list_storage, "w", encoding="utf-8") as f:
                json.dump([
                    {"symbol": self.symbol, "price": 100.0},
                    {"symbol": self.symbol, "price": 200.0}
                ], f)
            reporter = StressReporter(list_storage)
            result = reporter.simulate_single(self.symbol, 0.1)
            self.assertEqual(len(result["simulated_records"]), 2)
            prices = [r["price"] for r in result["simulated_records"]]
            self.assertEqual(prices, [110.0, 220.0])
        finally:
            if os.path.exists(list_storage):
                os.remove(list_storage)

    def test_run_stress_reporting(self):
        shifts = [-0.1, 0.0, 0.1]
        report = self.reporter.run_stress_reporting(self.symbol, shifts)
        self.assertEqual(report["symbol"], self.symbol)
        self.assertIn("base_metrics", report)
        self.assertEqual(len(report["simulations"]), 3)

    def test_generate_report_text(self):
        shifts = [-0.05, 0.05]
        text = self.reporter.generate_report_text(self.symbol, shifts)
        self.assertIn(f"Stress Test Report: {self.symbol}", text)
        self.assertIn("Base Return:", text)
        self.assertIn("Simulations", text)

    def test_send_report_telegram(self):
        with patch("skills.market_portfolio_stress_reporter.send_telegram_notification") as mock_send:
            mock_send.return_value = True
            result = self.reporter.send_report_telegram(
                self.symbol, [-0.1, 0.1], "mock_token", "mock_chat"
            )
            self.assertTrue(result)
            mock_send.assert_called_once()

    def test_get_stream_data(self):
        stream_data = self.reporter.get_stream_data()
        self.assertIsNotNone(stream_data)

    def test_top_level_generate_stress_report(self):
        shifts = [0.05, -0.05]
        report = generate_stress_report(self.storage_file, self.symbol, shifts)
        self.assertEqual(report["symbol"], self.symbol)
        self.assertEqual(len(report["simulations"]), 2)

    def test_top_level_run_stress_reporting_pipeline(self):
        with patch("skills.market_portfolio_stress_reporter.send_telegram_notification") as mock_send:
            mock_send.return_value = True
            report = run_stress_reporting_pipeline(
                self.storage_file,
                self.symbol,
                [0.1],
                telegram_token="token123",
                chat_id="chat456",
            )
            self.assertEqual(report["symbol"], self.symbol)
            mock_send.assert_called_once()

    def test_top_level_start_new(self):
        report = start_new(self.storage_file, self.symbol, [0.02])
        self.assertEqual(report["symbol"], self.symbol)

    def test_nonexistent_file_handling(self):
        non_existent = f"nonexistent_{uuid.uuid4().hex}.json"
        reporter = StressReporter(non_existent)
        sim = reporter.simulate_single(self.symbol, 0.1)
        self.assertEqual(sim["simulated_records"], [])
        report = reporter.run_stress_reporting(self.symbol, [0.1])
        self.assertEqual(report["symbol"], self.symbol)


if __name__ == "__main__":
    unittest.main()
