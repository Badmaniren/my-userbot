import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import requests
from skills.market_portfolio_telegram_command_center import start_new, MarketPortfolioTelegramCommandCenter

class TestMarketPortfolioTelegramCommandCenter(unittest.TestCase):

    def test_start_new_success(self):
        token = uuid.uuid4().hex
        chat_id = str(random.randint(10000, 99999))
        message = uuid.uuid4().hex

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            mock_post.return_value = mock_response

            result = start_new(token, chat_id, message)
            self.assertTrue(result)
            mock_post.assert_called_once()

    def test_start_new_invalid_inputs(self):
        token = uuid.uuid4().hex
        chat_id = str(random.randint(10000, 99999))
        message = uuid.uuid4().hex

        self.assertFalse(start_new("", chat_id, message))
        self.assertFalse(start_new(token, "", message))
        self.assertFalse(start_new(token, chat_id, ""))

    def test_start_new_bad_status(self):
        token = uuid.uuid4().hex
        chat_id = str(random.randint(10000, 99999))
        message = uuid.uuid4().hex

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_post.return_value = mock_response

            result = start_new(token, chat_id, message)
            self.assertFalse(result)

    def test_start_new_request_exception(self):
        token = uuid.uuid4().hex
        chat_id = str(random.randint(10000, 99999))
        message = uuid.uuid4().hex

        with patch('requests.post', side_effect=requests.RequestException):
            result = start_new(token, chat_id, message)
            self.assertFalse(result)

    def test_command_center_unknown_command(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        center = MarketPortfolioTelegramCommandCenter(storage_file)
        cmd = f"/{uuid.uuid4().hex}"
        chat_id = random.randint(1000, 9999)

        res = center.handle_command(cmd, chat_id)
        self.assertIn("Unknown command", res)

    def test_command_center_empty_command(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        center = MarketPortfolioTelegramCommandCenter(storage_file)
        chat_id = random.randint(1000, 9999)

        res = center.handle_command("   ", chat_id)
        self.assertIn("Unknown command", res)

    def test_command_center_start_help(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        center = MarketPortfolioTelegramCommandCenter(storage_file)
        chat_id = random.randint(1000, 9999)

        for cmd in ("/start", "/help"):
            res = center.handle_command(cmd, chat_id)
            self.assertIn("Welcome to Market Portfolio Telegram Command Center!", res)

    def test_command_center_portfolio(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        center = MarketPortfolioTelegramCommandCenter(storage_file)
        chat_id = random.randint(1000, 9999)

        res = center.handle_command("/portfolio", chat_id)
        self.assertIn("Portfolio summary", res)

    def test_command_center_report_missing_symbol(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        center = MarketPortfolioTelegramCommandCenter(storage_file)
        chat_id = random.randint(1000, 9999)

        res = center.handle_command("/report", chat_id)
        self.assertIn("Please specify a symbol", res)

    def test_command_center_report_with_data(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = uuid.uuid4().hex[:5].upper()
        prices = [random.randint(10, 100), random.randint(100, 200)]

        data = {symbol: prices}
        with open(storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        try:
            center = MarketPortfolioTelegramCommandCenter(storage_file)
            chat_id = random.randint(1000, 9999)
            res = center.handle_command(f"/report {symbol}", chat_id)
            self.assertIn(f"Report for {symbol}", res)
            self.assertIn(str(prices), res)
        finally:
            if os.path.exists(storage_file):
                os.remove(storage_file)

    def test_command_center_backtest_missing_symbol(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        center = MarketPortfolioTelegramCommandCenter(storage_file)
        chat_id = random.randint(1000, 9999)

        res = center.handle_command("/backtest", chat_id)
        self.assertIn("Please specify a symbol for backtest", res)

    def test_command_center_backtest_with_data(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = uuid.uuid4().hex[:5].upper()
        prices = [random.randint(10, 50) for _ in range(3)]

        data = {symbol: prices}
        with open(storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        try:
            center = MarketPortfolioTelegramCommandCenter(storage_file)
            chat_id = random.randint(1000, 9999)
            res = center.handle_command(f"/backtest {symbol}", chat_id)
            self.assertIn(f"Backtest executed for {symbol}", res)
            self.assertIn(f"Historical data points: {len(prices)}", res)
        finally:
            if os.path.exists(storage_file):
                os.remove(storage_file)

    def test_command_center_aliases(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        center = MarketPortfolioTelegramCommandCenter(storage_file)
        chat_id = random.randint(1000, 9999)

        cmd = f"/{uuid.uuid4().hex}"
        self.assertEqual(center.process_command(cmd, chat_id), center.handle_command(cmd, chat_id))
        self.assertEqual(center.execute_command(cmd, chat_id), center.handle_command(cmd, chat_id))

if __name__ == '__main__':
    unittest.main()