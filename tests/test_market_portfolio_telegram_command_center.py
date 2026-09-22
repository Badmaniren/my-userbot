import unittest
from unittest.mock import patch
import uuid
import random
import json
import os
from skills.market_portfolio_telegram_command_center import (
    start_new,
    MarketPortfolioTelegramCommandCenter
)


class TestMarketPortfolioTelegramCommandCenter(unittest.TestCase):

    def setUp(self):
        self.token = f"bot_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM{random.randint(10, 99)}"
        self.center = MarketPortfolioTelegramCommandCenter(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_start_new_success(self):
        message = f"Hello_{uuid.uuid4().hex}"
        expected_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        
        with patch('requests.post') as mock_post:
            mock_response = mock_post.return_value
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}

            result = start_new(self.token, self.chat_id, message)

            self.assertTrue(result)
            mock_post.assert_called_once_with(
                expected_url,
                json={"chat_id": self.chat_id, "text": message}
            )

    def test_start_new_invalid_status(self):
        message = f"ErrorMsg_{uuid.uuid4().hex}"
        with patch('requests.post') as mock_post:
            mock_response = mock_post.return_value
            mock_response.status_code = 400

            result = start_new(self.token, self.chat_id, message)

            self.assertFalse(result)

    def test_start_new_missing_arguments(self):
        self.assertFalse(start_new("", self.chat_id, "test"))
        self.assertFalse(start_new(self.token, "", "test"))
        self.assertFalse(start_new(self.token, self.chat_id, ""))

    def test_handle_command_empty(self):
        res_empty = self.center.handle_command("", self.chat_id)
        self.assertIn("Unknown command", res_empty)

        res_spaces = self.center.handle_command("   ", self.chat_id)
        self.assertIn("Unknown command", res_spaces)

    def test_handle_command_help_variants(self):
        for cmd in ("/start", "/help"):
            res = self.center.handle_command(cmd, self.chat_id)
            self.assertIn("Welcome to Market Portfolio Telegram Command Center", res)

    def test_handle_command_report_missing_symbol(self):
        res = self.center.handle_command("/report", self.chat_id)
        self.assertIn("Please specify a symbol", res)

    def test_handle_command_report_with_data(self):
        random_price = float(random.randint(100, 1000))
        test_data = {
            self.symbol: [random_price, random_price + 10.0]
        }
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        res = self.center.handle_command(f"/report {self.symbol}", self.chat_id)
        self.assertIn(f"Report for {self.symbol}:", res)
        self.assertIn(str(random_price), res)

    def test_handle_command_backtest_missing_symbol(self):
        res = self.center.handle_command("/backtest", self.chat_id)
        self.assertIn("Please specify a symbol for backtest", res)

    def test_handle_command_backtest_with_data(self):
        prices = [float(random.randint(10, 500)) for _ in range(3)]
        test_data = {
            self.symbol: prices
        }
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        res = self.center.handle_command(f"/backtest {self.symbol}", self.chat_id)
        self.assertIn(f"Backtest executed for {self.symbol}.", res)
        self.assertIn("Historical data points: 3", res)

    def test_handle_command_portfolio(self):
        res = self.center.handle_command("/portfolio", self.chat_id)
        self.assertIn("Portfolio summary:", res)

    def test_handle_command_unknown(self):
        unknown = f"/unknown_{uuid.uuid4().hex}"
        res = self.center.handle_command(unknown, self.chat_id)
        self.assertIn("Unknown command:", res)

    def test_aliases_execution(self):
        cmd = f"/report {self.symbol}"
        res_process = self.center.process_command(cmd, self.chat_id)
        res_execute = self.center.execute_command(cmd, self.chat_id)
        self.assertEqual(res_process, res_execute)


if __name__ == '__main__':
    unittest.main()