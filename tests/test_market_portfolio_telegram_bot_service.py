import unittest
from unittest.mock import patch
import random
import uuid
import string
import io
from skills.market_portfolio_telegram_bot_service import (
    TelegramBotService,
    handle_telegram_webhook,
    process_telegram_command
)

class TestMarketPortfolioTelegramBotService(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.service = TelegramBotService(self.storage_file, self.token)

    def test_init_and_properties(self):
        random_suffix = uuid.uuid4().hex
        custom_file = f"storage_{random_suffix}.json"
        custom_token = f"{random.randint(100,999)}:{random_suffix}"

        service = TelegramBotService(custom_file, custom_token)
        self.assertEqual(service.storage_file, custom_file)
        self.assertEqual(service.token, custom_token)

    def test_handle_webhook_success(self):
        symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        price = round(random.uniform(10.0, 5000.0), 2)

        payload = {
            "message": {
                "chat": {"id": int(self.chat_id)},
                "text": f"/update {symbol} {price}"
            }
        }

        mock_response_data = {"ok": True, "result": {"message_id": random.randint(1, 10000)}}

        with patch('skills.market_portfolio_telegram_bot_service.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response_data

            result = handle_telegram_webhook(self.token, payload, self.storage_file)

            self.assertTrue(result)
            mock_post.assert_called_once()
            called_url = mock_post.call_args[0][0]
            self.assertIn(self.token, called_url)

    def service_process_command_unrecognized(self):
        garbage_cmd = f"/{uuid.uuid4().hex[:6]}"
        with patch('skills.market_portfolio_telegram_bot_service.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"ok": True}

            res = process_telegram_command(self.token, self.chat_id, garbage_cmd, self.storage_file)
            self.assertFalse(res)

    def test_service_send_message_io_error_handling(self):
        msg = uuid.uuid4().hex
        with patch('skills.market_portfolio_telegram_bot_service.requests.post') as mock_post:
            mock_post.side_effect = Exception(uuid.uuid4().hex)

            success = self.service.send_message(self.chat_id, msg)
            self.assertFalse(success)

    def test_bot_service_portfolio_summary_command(self):
        command = "/portfolio"
        expected_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        expected_price = round(random.uniform(1.0, 100.0), 2)

        mock_stream_data = f"{expected_symbol},{expected_price}\n".encode('utf-8')

        with patch('skills.market_portfolio_telegram_bot_service.open', create=True) as mock_open, \
             patch('skills.market_portfolio_telegram_bot_service.requests.post') as mock_post:

            mock_open.return_value.__enter__.return_value = io.BytesIO(mock_stream_data)
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"ok": True}

            response = self.service.execute_command(self.chat_id, command)
            self.assertTrue(response)

            called_args, called_kwargs = mock_post.call_args
            sent_payload = called_kwargs.get('json', {})
            self.assertIn(expected_symbol, sent_payload.get('text', ''))

    def test_bot_service_unknown_webhook_format(self):
        malformed_payload = {
            uuid.uuid4().hex: uuid.uuid4().hex
        }

        result = handle_telegram_webhook(self.token, malformed_payload, self.storage_file)
        self.assertFalse(result)

    def test_service_buy_command_execution(self):
        symbol = ''.join(random.choices(string.ascii_uppercase, k=3))
        quantity = random.randint(1, 50)
        command = f"/buy {symbol} {quantity}"

        with patch('skills.market_portfolio_telegram_bot_service.requests.post') as mock_post, \
             patch('skills.market_portfolio_telegram_bot_service.open', create=True) as mock_open:

            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"ok": True}
            mock_open.return_value.__enter__.return_value = io.BytesIO(b"")

            res = self.service.execute_command(self.chat_id, command)
            self.assertTrue(res)

if __name__ == '__main__':
    unittest.main()