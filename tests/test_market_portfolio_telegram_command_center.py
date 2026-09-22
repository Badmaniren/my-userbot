import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import json
import os
import requests

from skills.market_portfolio_telegram_command_center import (
    start_new,
    MarketPortfolioTelegramCommandCenter
)


class TestMarketPortfolioTelegramCommandCenter(unittest.TestCase):

    def setUp(self):
        self.token = f"{random.randint(100000, 999999)}:AA{uuid.uuid4().hex[:8]}"
        self.chat_id = str(random.randint(1000000, 99999999))
        self.message = f"test_msg_{uuid.uuid4().hex[:6]}"
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.symbol = f"SYM{random.choice(['A', 'B', 'C', 'X', 'Z'])}{random.randint(10, 99)}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_start_new_success(self):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": self.message
        }
        
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True, "result": {}}
            mock_post.return_value = mock_response

            result = start_new(self.token, self.chat_id, self.message)
            
            self.assertTrue(result)
            mock_post.assert_called_once_with(url, json=payload)

    def test_start_new_invalid_arguments(self):
        self.assertFalse(start_new("", self.chat_id, self.message))
        self.assertFalse(start_new(self.token, "", self.message))
        self.assertFalse(start_new(self.token, self.chat_id, ""))

    def test_start_new_http_error(self):
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = random.choice([400, 401, 403, 404, 500])
            mock_post.return_value = mock_response

            result = start_new(self.token, self.chat_id, self.message)
            self.assertFalse(result)

    def test_start_new_request_exception(self):
        with patch('requests.post', side_effect=requests.RequestException("Network failure")):
            result = start_new(self.token, self.chat_id, self.message)
            self.assertFalse(result)

    def test_command_center_start_help(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        for cmd in ["/start", "/help", f"   /start   ", f"/{uuid.uuid4().hex[:3]}help"]:
            if cmd.strip() not in ("/start", "/help"):
                continue
            res = center.handle_command(cmd, self.chat_id)
            self.assertIn("Welcome to Market Portfolio Telegram Command Center!", res)
            self.assertIn("/report", res)
            self.assertIn("/backtest", res)
            self.assertIn("/portfolio", res)

    def test_command_center_unknown_command(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        random_cmd = f"/{uuid.uuid4().hex[:8]}"
        res = center.handle_command(random_cmd, self.chat_id)
        self.assertIn(f"Unknown command: {random_cmd.lower()}", res)
        
        empty_res = center.handle_command("   ", self.chat_id)
        self.assertEqual(empty_res, "Unknown command. Type /start for help.")

    def test_command_center_report_missing_symbol(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        res = center.handle_command("/report", self.chat_id)
        self.assertEqual(res, "Please specify a symbol, e.g., /report AAPL")

    def test_command_center_report_with_data_file(self):
        price_val = round(random.uniform(10.0, 1000.0), 2)
        test_data = {
            self.symbol: [price_val, price_val + 5.0]
        }
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        res = center.handle_command(f"/report {self.symbol.lower()}", self.chat_id)
        
        self.assertIn(f"Report for {self.symbol}:", res)
        self.assertIn(str(price_val), res)

    def test_command_center_backtest_missing_symbol(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        res = center.handle_command("/backtest", self.chat_id)
        self.assertEqual(res, "Please specify a symbol for backtest, e.g., /backtest AAPL")

    def test_command_center_backtest_with_data_file(self):
        prices = [round(random.uniform(50.0, 500.0), 2) for _ in range(random.randint(3, 10))]
        test_data = {
            self.symbol: prices
        }
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        res = center.handle_command(f"/backtest {self.symbol}", self.chat_id)
        
        self.assertIn(f"Backtest executed for {self.symbol}.", res)
        self.assertIn(f"Historical data points: {len(prices)}", res)

    def test_command_center_portfolio(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        res = center.handle_command("/portfolio", self.chat_id)
        self.assertEqual(res, "Portfolio summary: active assets monitored via MarketParser.")

    def test_command_center_aliases(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        
        res_process = center.process_command("/portfolio", self.chat_id)
        self.assertEqual(res_process, "Portfolio summary: active assets monitored via MarketParser.")

        res_execute = center.execute_command("/portfolio", self.chat_id)
        self.assertEqual(res_execute, "Portfolio summary: active assets monitored via MarketParser.")


if __name__ == '__main__':
    unittest.main()