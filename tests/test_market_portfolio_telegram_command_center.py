import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import os
import json
import requests
from skills.market_portfolio_telegram_command_center import start_new, MarketPortfolioTelegramCommandCenter

class TestMarketPortfolioTelegramCommandCenter(unittest.TestCase):

    def setUp(self):
        self.token = f"bot_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.message = f"msg_{uuid.uuid4().hex}"
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:4].upper()}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_start_new_success(self):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}

        with patch("requests.post", return_value=mock_response) as mock_post:
            result = start_new(self.token, self.chat_id, self.message)
            self.assertTrue(result)
            mock_post.assert_called_once_with(
                url,
                json={"chat_id": self.chat_id, "text": self.message}
            )

    def test_start_new_invalid_arguments(self):
        self.assertFalse(start_new("", self.chat_id, self.message))
        self.assertFalse(start_new(self.token, "", self.message))
        self.assertFalse(start_new(self.token, self.chat_id, ""))

    def test_start_new_http_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 400
        with patch("requests.post", return_value=mock_response):
            result = start_new(self.token, self.chat_id, self.message)
            self.assertFalse(result)

    def test_start_new_exception(self):
        with patch("requests.post", side_effect=requests.RequestException):
            result = start_new(self.token, self.chat_id, self.message)
            self.assertFalse(result)

    def test_handle_command_empty_and_unknown(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        res_empty = center.handle_command("   ", self.chat_id)
        self.assertIn("Unknown command", res_empty)

        random_cmd = f"/{uuid.uuid4().hex}"
        res_unknown = center.handle_command(random_cmd, self.chat_id)
        self.assertIn("Unknown command", res_unknown)

    def test_handle_command_start_help(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        for cmd in ("/start", "/help"):
            res = center.handle_command(cmd, self.chat_id)
            self.assertIn("Welcome to Market Portfolio Telegram Command Center", res)

    def test_handle_command_portfolio(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        res = center.handle_command("/portfolio", self.chat_id)
        self.assertIn("Portfolio summary", res)

    def test_handle_command_report_no_symbol(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        res = center.handle_command("/report", self.chat_id)
        self.assertIn("Please specify a symbol", res)

    def test_handle_command_report_with_data(self):
        prices = [random.randint(10, 100), random.randint(101, 200)]
        data = {self.symbol: prices}
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        res = center.handle_command(f"/report {self.symbol}", self.chat_id)
        self.assertIn(f"Report for {self.symbol}", res)
        self.assertIn(str(prices), res)

    def test_handle_command_backtest_no_symbol(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        res = center.handle_command("/backtest", self.chat_id)
        self.assertIn("Please specify a symbol for backtest", res)

    def test_handle_command_backtest_with_data(self):
        prices = [random.randint(1, 50) for _ in range(random.randint(3, 10))]
        data = {self.symbol: prices}
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        res = center.handle_command(f"/backtest {self.symbol}", self.chat_id)
        self.assertIn(f"Backtest executed for {self.symbol}", res)
        self.assertIn(f"Historical data points: {len(prices)}", res)

    def test_process_and_execute_aliases(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        cmd = "/portfolio"
        self.assertEqual(
            center.process_command(cmd, self.chat_id),
            center.handle_command(cmd, self.chat_id)
        )
        self.assertEqual(
            center.execute_command(cmd, self.chat_id),
            center.handle_command(cmd, self.chat_id)
        )

if __name__ == "__main__":
    unittest.main()