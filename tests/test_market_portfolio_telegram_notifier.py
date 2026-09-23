import unittest
from unittest.mock import patch, MagicMock
import requests
import uuid
import random
import string
from skills.market_portfolio_telegram_notifier import start_new

class TestTelegramNotifier(unittest.TestCase):

    def setUp(self):
        self.token = f"{uuid.uuid4().hex}:{uuid.uuid4().hex[:16]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.message = ''.join(random.choices(string.ascii_letters, k=20))

    def test_start_new_success(self):
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True, "result": {"message_id": random.randint(1, 1000)}}
            mock_post.return_value = mock_response

            result = start_new(self.token, self.chat_id, self.message)

            self.assertTrue(result)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(kwargs['json']['chat_id'], self.chat_id)
            self.assertEqual(kwargs['json']['text'], self.message)

    def test_start_new_invalid_inputs(self):
        invalid_data = [None, "", "   ", 123]
        for val in invalid_data:
            with self.subTest(val=val):
                self.assertFalse(start_new(val, self.chat_id, self.message))
                self.assertFalse(start_new(self.token, val, self.message))
                self.assertFalse(start_new(self.token, self.chat_id, val))

    def test_start_new_api_error(self):
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
            mock_post.return_value = mock_response

            result = start_new(self.token, self.chat_id, self.message)
            self.assertFalse(result)

    def test_start_new_connection_failure(self):
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError()

            result = start_new(self.token, self.chat_id, self.message)
            self.assertFalse(result)

    def test_start_new_malformed_json(self):
        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_post.return_value = mock_response

            result = start_new(self.token, self.chat_id, self.message)
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
