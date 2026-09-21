import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import requests
from skills.market_portfolio_telegram_notifier import start_new, send_telegram_notification

class TestMarketPortfolioTelegramNotifier(unittest.TestCase):

    def test_start_new_success_flow(self):
        rand_token = f"{random.randint(1000, 9999)}:{uuid.uuid4().hex[:16]}"
        rand_chat_id = str(random.randint(100000, 999999))
        rand_message = f"TEST_MSG_{uuid.uuid4().hex}"

        with patch('skills.market_portfolio_telegram_notifier.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"ok": True, "result": {}}
            mock_post.return_value = mock_response

            result = start_new(rand_token, rand_chat_id, rand_message)

            self.assertTrue(result)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertIn(rand_token, args[0])
            self.assertEqual(kwargs['json']['chat_id'], rand_chat_id)
            self.assertEqual(kwargs['json']['text'], rand_message)
            self.assertEqual(kwargs['timeout'], 10)

    def test_start_new_api_error_response(self):
        rand_token = uuid.uuid4().hex
        rand_chat_id = uuid.uuid4().hex[:8]
        rand_message = uuid.uuid4().hex

        with patch('skills.market_portfolio_telegram_notifier.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"ok": False, "description": "Unauthorized"}
            mock_post.return_value = mock_response

            result = start_new(rand_token, rand_chat_id, rand_message)

            self.assertFalse(result)
            mock_post.assert_called_once()

    def test_start_new_requests_exception_handling(self):
        rand_token = uuid.uuid4().hex
        rand_chat_id = uuid.uuid4().hex[:8]
        rand_message = uuid.uuid4().hex

        with patch('skills.market_portfolio_telegram_notifier.requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.RequestException(uuid.uuid4().hex)

            result = start_new(rand_token, rand_chat_id, rand_message)

            self.assertFalse(result)
            mock_post.assert_called_once()

    def test_start_new_invalid_input_validation(self):
        invalid_inputs = [
            ("", "", ""),
            (None, None, None),
            (12345, 67890, 111),
        ]
        
        for token, chat_id, message in invalid_inputs:
            with patch('skills.market_portfolio_telegram_notifier.requests.post') as mock_post:
                mock_response = MagicMock()
                mock_response.raise_for_status.side_effect = ValueError(uuid.uuid4().hex)
                mock_post.return_value = mock_response

                result = start_new(token, chat_id, message)
                self.assertFalse(result)

    def test_send_telegram_notification_alias(self):
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(100, 999))
        rand_message = uuid.uuid4().hex

        with patch('skills.market_portfolio_telegram_notifier.start_new') as mock_start_new:
            expected_return = random.choice([True, False])
            mock_start_new.return_value = expected_return

            result = send_telegram_notification(rand_token, rand_chat_id, rand_message)

            self.assertEqual(result, expected_return)
            mock_start_new.assert_called_once_with(rand_token, rand_chat_id, rand_message)

if __name__ == '__main__':
    unittest.main()