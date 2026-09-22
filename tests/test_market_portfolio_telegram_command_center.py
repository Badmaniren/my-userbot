import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from skills.market_portfolio_telegram_command_center import start_new

class TestMarketPortfolioTelegramCommandCenter(unittest.TestCase):

    def setUp(self):
        self.random_token = f"{random.randint(1000, 9999)}:{uuid.uuid4().hex}"
        self.random_chat_id = str(random.randint(10000000, 99999999))
        self.random_message = "".join(random.choices(string.ascii_letters + string.digits, k=32))

    @patch('skills.market_portfolio_telegram_command_center.requests.post')
    def test_start_new_success_flow(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "result": {}}
        mock_post.return_value = mock_response

        result = start_new(self.random_token, self.random_chat_id, self.random_message)
        
        self.assertTrue(result)
        mock_post.assert_called_once()
        called_args, called_kwargs = mock_post.call_args
        self.assertIn(self.random_token, called_args[0])
        
        request_json = called_kwargs.get('json', {})
        self.assertEqual(request_json.get('chat_id'), self.random_chat_id)
        self.assertEqual(request_json.get('text'), self.random_message)

    @patch('skills.market_portfolio_telegram_command_center.requests.post')
    def test_start_new_api_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"ok": False, "description": f"Bad Request: {uuid.uuid4().hex}"}
        mock_post.return_value = mock_response

        result = start_new(self.random_token, self.random_chat_id, self.random_message)
        
        self.assertFalse(result)
        mock_post.assert_called_once()

    @patch('skills.market_portfolio_telegram_command_center.requests.post')
    def test_start_new_network_exception(self, mock_post):
        mock_post.side_effect = Exception(f"Network error {uuid.uuid4().hex}")

        result = start_new(self.random_token, self.random_chat_id, self.random_message)
        
        self.assertFalse(result)
        mock_post.assert_called_once()

    @patch('skills.market_portfolio_telegram_command_center.requests.post')
    def test_start_new_empty_inputs(self, mock_post):
        empty_token = ""
        empty_chat = ""
        empty_msg = ""
        
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        result = start_new(empty_token, empty_chat, empty_msg)
        self.assertFalse(result)

    @patch('skills.market_portfolio_telegram_command_center.requests.post')
    def test_start_new_malformed_json_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError(f"Invalid json {uuid.uuid4().hex}")
        mock_post.return_value = mock_response

        result = start_new(self.random_token, self.random_chat_id, self.random_message)
        
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()