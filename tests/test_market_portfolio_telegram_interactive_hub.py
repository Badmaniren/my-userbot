import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import os

from skills.market_portfolio_telegram_interactive_hub import (
    TelegramInteractiveHub,
    handle_interactive_command,
    process_hub_request
)

class TestMarketPortfolioTelegramInteractiveHub(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.hub = TelegramInteractiveHub(self.storage_file)
        self.symbol = f"SYM_{random.choice(string.ascii_uppercase)}{random.randint(100, 999)}"
        self.chat_id = str(random.randint(100000, 999999))
        self.token = f"{random.randint(1000, 9999)}:BOT_{uuid.uuid4().hex[:6]}"
        self.command = random.choice(["/status", "/simulate", "/summary", "/help"])

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_hub_initialization(self):
        rand_file = f"init_{uuid.uuid4().hex}.json"
        hub = TelegramInteractiveHub(rand_file)
        self.assertEqual(hub.storage_file, rand_file)
        if os.path.exists(rand_file):
            os.remove(rand_file)

    def test_handle_interactive_command_success(self):
        with patch('skills.market_portfolio_telegram_interactive_hub.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True, "result": {}}
            mock_post.return_value = mock_response

            result = self.hub.handle_command(self.command, self.symbol, self.token, self.chat_id)
            self.assertTrue(result)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertIn(self.token, args[0] if args else kwargs.get('url', ''))

    def test_handle_interactive_command_failure(self):
        with patch('skills.market_portfolio_telegram_interactive_hub.requests.post') as mock_post:
            mock_post.side_effect = Exception(f"Network error {uuid.uuid4().hex}")

            result = self.hub.handle_command(self.command, self.symbol, self.token, self.chat_id)
            self.assertFalse(result)

    def test_process_interactive_hub_stream(self):
        random_price = round(random.uniform(10.0, 5000.0), 2)
        mock_data_stream = io.BytesIO(f'{{"symbol": "{self.symbol}", "price": {random_price}}}'.encode('utf-8'))

        with patch('skills.market_portfolio_telegram_interactive_hub.open', unittest.mock.mock_open(read_data=mock_data_stream.read())):
            with patch('skills.market_portfolio_telegram_interactive_hub.requests.post') as mock_post:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_post.return_value = mock_response

                summary = self.hub.process_hub_stream(self.symbol, self.token, self.chat_id)
                self.assertIsInstance(summary, dict)

    def test_module_level_handle_interactive_command(self):
        with patch('skills.market_portfolio_telegram_interactive_hub.TelegramInteractiveHub.handle_command') as mock_method:
            mock_method.return_value = True
            res = handle_interactive_command(self.command, self.symbol, self.token, self.chat_id)
            self.assertTrue(res)
            mock_method.assert_called_once()

    def test_module_level_process_hub_request(self):
        with patch('skills.market_portfolio_telegram_interactive_hub.TelegramInteractiveHub.process_hub_stream') as mock_method:
            expected_dict = {"status": "ok", "id": uuid.uuid4().hex}
            mock_method.return_value = expected_dict
            res = process_hub_request(self.symbol, self.token, self.chat_id, self.storage_file)
            self.assertEqual(res, expected_dict)
            mock_method.assert_called_once()

    def test_interactive_hub_invalid_payload(self):
        invalid_token = f"INVALID_{uuid.uuid4().hex}"
        with patch('skills.market_portfolio_telegram_interactive_hub.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {"ok": False, "description": "Bad Request"}
            mock_post.return_value = mock_response

            res = self.hub.handle_command(self.command, self.symbol, invalid_token, self.chat_id)
            self.assertFalse(res)

if __name__ == '__main__':
    unittest.main()