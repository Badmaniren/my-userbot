import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import requests
import io
from skills.market_portfolio_telegram_command_center import (
    start_new,
    MarketPortfolioTelegramCommandCenter
)

class TestMarketPortfolioTelegramCommandCenter(unittest.TestCase):

    def setUp(self):
        self.token = f"bot_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.message = f"msg_{uuid.uuid4().hex}"
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM{random.randint(10, 99)}"

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
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}

        with patch('requests.post', return_value=mock_response) as mock_post:
            result = start_new(self.token, self.chat_id, self.message)
            self.assertTrue(result)
            mock_post.assert_called_once_with(url, json=payload)

    def test_start_new_invalid_inputs(self):
        self.assertFalse(start_new("", self.chat_id, self.message))
        self.assertFalse(start_new(self.token, "", self.message))
        self.assertFalse(start_new(self.token, self.chat_id, ""))

    def test_start_new_bad_status_code(self):
        mock_response = MagicMock()
        mock_response.status_code = random.choice([400, 401, 404, 500])
        with patch('requests.post', return_value=mock_response):
            result = start_new(self.token, self.chat_id, self.message)
            self.assertFalse(result)

    def test_start_new_request_exception(self):
        with patch('requests.post', side_effect=requests.RequestException("Network error")):
            result = start_new(self.token, self.chat_id, self.message)
            self.assertFalse(result)

    def test_start_new_value_error(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        with patch('requests.post', return_value=mock_response):
            result = start_new(self.token, self.chat_id, self.message)
            self.assertFalse(result)

    def test_command_center_help_commands(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        cmd = random.choice(["/start", "/help"])
        response = center.handle_command(cmd, self.chat_id)
        self.assertIn("Welcome to Market Portfolio Telegram Command Center", response)
        self.assertIn("/report", response)
        self.assertIn("/backtest", response)
        self.assertIn("/portfolio", response)

    def test_command_center_unknown_command(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        unknown_cmd = f"/{uuid.uuid4().hex[:6]}"
        response = center.handle_command(unknown_cmd, self.chat_id)
        self.assertIn("Unknown command", response)
        self.assertIn(unknown_cmd, response)

    def test_command_center_empty_command(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        response = center.handle_command("   ", self.chat_id)
        self.assertIn("Unknown command", response)

    def test_command_center_report_missing_symbol(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        response = center.handle_command("/report", self.chat_id)
        self.assertIn("Please specify a symbol", response)

    def test_command_center_report_with_data(self):
        price_val = round(random.uniform(10.0, 500.0), 2)
        test_data = {self.symbol: [price_val, price_val + 5.0]}
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        response = center.handle_command(f"/report {self.symbol}", self.chat_id)
        
        self.assertIn(f"Report for {self.symbol}:", response)
        self.assertIn(str(price_val), response)

    def test_command_center_backtest_missing_symbol(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        response = center.handle_command("/backtest", self.chat_id)
        self.assertIn("Please specify a symbol for backtest", response)

    def test_command_center_backtest_with_data(self):
        prices = [random.uniform(1.0, 100.0) for _ in range(5)]
        test_data = {self.symbol: prices}
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        response = center.handle_command(f"/backtest {self.symbol}", self.chat_id)

        self.assertIn(f"Backtest executed for {self.symbol}", response)
        self.assertIn("5", response)

    def test_command_center_portfolio(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        response = center.handle_command("/portfolio", self.chat_id)
        self.assertIn("Portfolio summary", response)

    def test_command_center_aliases(self):
        center = MarketPortfolioTelegramCommandCenter(self.storage_file)
        
        res_process = center.process_command("/portfolio", self.chat_id)
        self.assertIn("Portfolio summary", res_process)

        res_execute = center.execute_command("/portfolio", self.chat_id)
        self.assertIn("Portfolio summary", res_execute)

if __name__ == '__main__':
    unittest.main()