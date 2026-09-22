import unittest
from unittest.mock import patch, MagicMock
import os
import json
import uuid
import random
import requests
from skills.market_portfolio_telegram_command_center import start_new, MarketPortfolioTelegramCommandCenter


class TestMarketPortfolioTelegramCommandCenter(unittest.TestCase):

    def setUp(self):
        self.rand_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:10]}"
        self.rand_chat_id = str(random.randint(10000000, 99999999))
        self.rand_message = f"msg_{uuid.uuid4().hex[:8]}"
        self.rand_storage = f"{uuid.uuid4().hex[:10]}.json"

    def tearDown(self):
        if os.path.exists(self.rand_storage):
            try:
                os.remove(self.rand_storage)
            except OSError:
                pass

    def test_start_new_success(self):
        with patch('requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"ok": True}
            mock_post.return_value = mock_resp

            result = start_new(self.rand_token, self.rand_chat_id, self.rand_message)
            self.assertTrue(result)
            mock_post.assert_called_once()

    def test_start_new_invalid_arguments(self):
        self.assertFalse(start_new("", self.rand_chat_id, self.rand_message))
        self.assertFalse(start_new(self.rand_token, "", self.rand_message))
        self.assertFalse(start_new(self.rand_token, self.rand_chat_id, ""))

    def test_start_new_non_200_status(self):
        with patch('requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = random.choice([400, 401, 403, 404, 500])
            mock_post.return_value = mock_resp

            result = start_new(self.rand_token, self.rand_chat_id, self.rand_message)
            self.assertFalse(result)

    def test_start_new_request_exception(self):
        with patch('requests.post', side_effect=requests.RequestException("Network failure")):
            result = start_new(self.rand_token, self.rand_chat_id, self.rand_message)
            self.assertFalse(result)

    def test_start_new_value_error(self):
        with patch('requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.side_effect = ValueError("Malformed JSON")
            mock_post.return_value = mock_resp

            result = start_new(self.rand_token, self.rand_chat_id, self.rand_message)
            self.assertFalse(result)

    def test_command_center_start_help(self):
        center = MarketPortfolioTelegramCommandCenter(self.rand_storage)
        for cmd in ["/start", "/help", f"/START {uuid.uuid4().hex[:4]}"]:
            res = center.handle_command(cmd, self.rand_chat_id)
            self.assertIn("Welcome to Market Portfolio Telegram Command Center!", res)

    def test_command_center_unknown(self):
        center = MarketPortfolioTelegramCommandCenter(self.rand_storage)
        rand_cmd = f"/{uuid.uuid4().hex[:6]}"
        res = center.handle_command(rand_cmd, self.rand_chat_id)
        self.assertIn("Unknown command", res)

    def test_command_center_empty(self):
        center = MarketPortfolioTelegramCommandCenter(self.rand_storage)
        res = center.handle_command("   ", self.rand_chat_id)
        self.assertIn("Unknown command", res)

    def test_command_center_portfolio(self):
        center = MarketPortfolioTelegramCommandCenter(self.rand_storage)
        res = center.handle_command("/portfolio", self.rand_chat_id)
        self.assertIn("Portfolio summary", res)

    def test_command_center_report_missing_symbol(self):
        center = MarketPortfolioTelegramCommandCenter(self.rand_storage)
        res = center.handle_command("/report", self.rand_chat_id)
        self.assertIn("Please specify a symbol", res)

    def test_command_center_report_with_data_from_file(self):
        rand_symbol = uuid.uuid4().hex[:5].upper()
        rand_prices = [random.randint(10, 1000) for _ in range(3)]
        data = {rand_symbol: rand_prices}
        
        with open(self.rand_storage, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        center = MarketPortfolioTelegramCommandCenter(self.rand_storage)
        res = center.handle_command(f"/report {rand_symbol}", self.rand_chat_id)
        self.assertIn(f"Report for {rand_symbol}", res)
        self.assertIn(str(rand_prices), res)

    def test_command_center_backtest_missing_symbol(self):
        center = MarketPortfolioTelegramCommandCenter(self.rand_storage)
        res = center.handle_command("/backtest", self.rand_chat_id)
        self.assertIn("Please specify a symbol for backtest", res)

    def test_command_center_backtest_with_parser_load(self):
        rand_symbol = uuid.uuid4().hex[:5].upper()
        rand_prices = [random.randint(50, 500) for _ in range(4)]
        
        center = MarketPortfolioTelegramCommandCenter(self.rand_storage)
        center.parser = MagicMock()
        center.parser.load_data.return_value = {rand_symbol: rand_prices}

        res = center.handle_command(f"/backtest {rand_symbol}", self.rand_chat_id)
        self.assertIn(f"Backtest executed for {rand_symbol}", res)
        self.assertIn("Historical data points: 4", res)

    def test_command_center_aliases(self):
        center = MarketPortfolioTelegramCommandCenter(self.rand_storage)
        rand_symbol = uuid.uuid4().hex[:4].upper()
        
        with open(self.rand_storage, 'w', encoding='utf-8') as f:
            json.dump({rand_symbol: [100, 200]}, f)

        res_process = center.process_command(f"/report {rand_symbol}", self.rand_chat_id)
        res_execute = center.execute_command(f"/report {rand_symbol}", self.rand_chat_id)
        
        self.assertEqual(res_process, res_execute)
        self.assertIn(rand_symbol, res_process)


if __name__ == "__main__":
    unittest.main()