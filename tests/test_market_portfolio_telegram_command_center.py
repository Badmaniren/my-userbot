import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import json
import os
import requests
from skills.market_portfolio_telegram_command_center import start_new, MarketPortfolioTelegramCommandCenter


class TestMarketPortfolioTelegramCommandCenter(unittest.TestCase):

    def setUp(self):
        self.token = f"bot{uuid.uuid4().hex}:{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(1000000, 999999999))
        self.message = f"Msg_{uuid.uuid4().hex}"
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.symbol = f"SYM{random.randint(10, 99)}"
        self.command_center = MarketPortfolioTelegramCommandCenter(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_start_new_success(self):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        expected_payload = {
            "chat_id": self.chat_id,
            "text": self.message
        }

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True, "result": {uuid.uuid4().hex: uuid.uuid4().hex}}
            mock_post.return_value = mock_response

            result = start_new(self.token, self.chat_id, self.message)

            self.assertTrue(result)
            mock_post.assert_called_once_with(url, json=expected_payload)

    def test_start_new_failure_status(self):
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = random.choice([400, 401, 404, 500])
            mock_response.json.return_value = {"ok": False}
            mock_post.return_value = mock_response

            result = start_new(self.token, self.chat_id, self.message)

            self.assertFalse(result)

    def test_start_new_invalid_json(self):
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError(uuid.uuid4().hex)
            mock_post.return_value = mock_response

            result = start_new(self.token, self.chat_id, self.message)

            self.assertFalse(result)

    def test_start_new_request_exception(self):
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.RequestException(uuid.uuid4().hex)

            result = start_new(self.token, self.chat_id, self.message)

            self.assertFalse(result)

    def test_start_new_missing_arguments(self):
        self.assertFalse(start_new("", self.chat_id, self.message))
        self.assertFalse(start_new(self.token, "", self.message))
        self.assertFalse(start_new(self.token, self.chat_id, ""))

    def test_handle_command_empty(self):
        response = self.command_center.handle_command("   ", self.chat_id)
        self.assertIn("Unknown command", response)

    def test_handle_command_start_help(self):
        for cmd in ["/start", "/help", f"/start {uuid.uuid4().hex}", f"/help {uuid.uuid4().hex}"]:
            response = self.command_center.handle_command(cmd, self.chat_id)
            self.assertIn("Welcome to Market Portfolio Telegram Command Center", response)
            self.assertIn("/report", response)
            self.assertIn("/backtest", response)
            self.assertIn("/portfolio", response)

    def test_handle_command_portfolio(self):
        response = self.command_center.handle_command("/portfolio", self.chat_id)
        self.assertIn("Portfolio summary", response)

    def test_handle_command_report_missing_symbol(self):
        response = self.command_center.handle_command("/report", self.chat_id)
        self.assertIn("Please specify a symbol", response)

    def test_handle_command_report_with_data(self):
        random_price = round(random.uniform(10.0, 1000.0), 2)
        test_data = {self.symbol: [random_price]}
        
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        response = self.command_center.handle_command(f"/report {self.symbol.lower()}", self.chat_id)
        self.assertIn(self.symbol, response)
        self.assertIn(str(random_price), response)

    def test_handle_command_backtest_missing_symbol(self):
        response = self.command_center.handle_command("/backtest", self.chat_id)
        self.assertIn("Please specify a symbol for backtest", response)

    def test_handle_command_backtest_with_data(self):
        prices = [round(random.uniform(1.0, 500.0), 2) for _ in range(random.randint(3, 10))]
        test_data = {self.symbol: prices}
        
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f)

        response = self.command_center.handle_command(f"/backtest {self.symbol}", self.chat_id)
        self.assertIn(f"Backtest executed for {self.symbol}", response)
        self.assertIn(str(len(prices)), response)

    def test_handle_command_unknown_action(self):
        unknown_action = f"/{uuid.uuid4().hex}"
        response = self.command_center.handle_command(unknown_action, self.chat_id)
        self.assertIn("Unknown command", response)
        self.assertIn(unknown_action[1:], response)

    def test_process_and_execute_aliases(self):
        cmd = f"/report {self.symbol}"
        res1 = self.command_center.process_command(cmd, self.chat_id)
        res2 = self.command_center.execute_command(cmd, self.chat_id)
        self.assertEqual(res1, res2)


if __name__ == '__main__':
    unittest.main()