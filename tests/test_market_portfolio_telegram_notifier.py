import unittest
from unittest.mock import patch, Mock
import uuid
import random
import requests
from skills.market_portfolio_telegram_notifier import start_new, send_telegram_notification

class TestMarketPortfolioTelegramNotifier(unittest.TestCase):

    def test_start_new_success_flow(self):
        token = f"bot{uuid.uuid4().hex}"
        chat_id = str(random.randint(100000, 999999999))
        message = f"report_success_{uuid.uuid4().hex}"

        mock_response = Mock()
        mock_response.json.return_value = {"ok": True, "result": {"message_id": random.randint(1, 10000)}}
        mock_response.raise_for_status.return_value = None

        with patch("skills.market_portfolio_telegram_notifier.requests.post", return_value=mock_response) as mock_post:
            result = start_new(token, chat_id, message)
            self.assertTrue(result)
            mock_post.assert_called_once()
            called_kwargs = mock_post.call_args[1]
            self.assertEqual(called_kwargs["json"]["chat_id"], chat_id)
            self.assertEqual(called_kwargs["json"]["text"], message)
            self.assertIn(token, mock_post.call_args[0][0])

    def test_start_new_failure_response(self):
        token = f"bot{uuid.uuid4().hex}"
        chat_id = str(random.randint(100000, 999999999))
        message = f"report_fail_{uuid.uuid4().hex}"

        mock_response = Mock()
        mock_response.json.return_value = {"ok": False, "description": "Unauthorized"}
        mock_response.raise_for_status.return_value = None

        with patch("skills.market_portfolio_telegram_notifier.requests.post", return_value=mock_response) as mock_post:
            result = start_new(token, chat_id, message)
            self.assertFalse(result)
            mock_post.assert_called_once()

    def test_start_new_request_exception(self):
        token = f"bot{uuid.uuid4().hex}"
        chat_id = str(random.randint(100000, 999999999))
        message = f"report_exception_{uuid.uuid4().hex}"

        with patch("skills.market_portfolio_telegram_notifier.requests.post", side_effect=requests.RequestException("Connection timeout")) as mock_post:
            result = start_new(token, chat_id, message)
            self.assertFalse(result)
            mock_post.assert_called_once()

    def test_send_telegram_notification_alias(self):
        token = f"bot{uuid.uuid4().hex}"
        chat_id = str(random.randint(100000, 999999999))
        message = f"alias_test_{uuid.uuid4().hex}"

        mock_response = Mock()
        mock_response.json.return_value = {"ok": True}
        mock_response.raise_for_status.return_value = None

        with patch("skills.market_portfolio_telegram_notifier.requests.post", return_value=mock_response) as mock_post:
            result = send_telegram_notification(token, chat_id, message)
            self.assertTrue(result)
            mock_post.assert_called_once()

    def test_start_new_json_decode_error(self):
        token = f"bot{uuid.uuid4().hex}"
        chat_id = str(random.randint(100000, 999999999))
        message = f"json_error_{uuid.uuid4().hex}"

        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None

        with patch("skills.market_portfolio_telegram_notifier.requests.post", return_value=mock_response) as mock_post:
            result = start_new(token, chat_id, message)
            self.assertFalse(result)
            mock_post.assert_called_once()

if __name__ == "__main__":
    unittest.main()