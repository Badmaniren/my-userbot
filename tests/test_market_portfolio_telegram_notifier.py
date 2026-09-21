import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from skills.market_portfolio_telegram_notifier import start_new


class TestMarketPortfolioTelegramNotifier(unittest.TestCase):

    def test_start_new_success_execution(self):
        rand_token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        rand_chat_id = str(random.randint(100000, 99999999))
        rand_message = f"Inquisition report: {uuid.uuid4().hex}"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "result": {"message_id": random.randint(1, 1000)}}

        with patch('requests.post', return_value=mock_response) as mock_post:
            result = start_new(rand_token, rand_chat_id, rand_message)
            
            self.assertTrue(result)
            mock_post.assert_called_once()
            called_args, called_kwargs = mock_post.call_args
            self.assertIn(rand_token, called_args[0] if called_args else called_kwargs.get('url', ''))

    def test_start_new_request_exception_handling(self):
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(1000, 9999))
        rand_message = uuid.uuid4().hex

        with patch('requests.post', side_effect=Exception(uuid.uuid4().hex)) as mock_post:
            result = start_new(rand_token, rand_chat_id, rand_message)
            
            self.assertFalse(result)
            mock_post.assert_called_once()

    def test_start_new_http_error_status(self):
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(100, 999))
        rand_message = uuid.uuid4().hex

        mock_response = MagicMock()
        mock_response.status_code = random.choice([400, 401, 403, 404, 500, 502])
        mock_response.raise_for_status.side_effect = Exception("HTTP Error")

        with patch('requests.post', return_value=mock_response) as mock_post:
            result = start_new(rand_token, rand_chat_id, rand_message)
            
            self.assertFalse(result)
            mock_post.assert_called_once()


if __name__ == '__main__':
    unittest.main()