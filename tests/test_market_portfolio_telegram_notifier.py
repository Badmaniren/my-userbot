import unittest
from unittest.mock import patch, Mock
import uuid
import random
import requests
from skills.market_portfolio_telegram_notifier import start_new, send_telegram_notification, send_telegram_notifier


class TestMarketPortfolioTelegramNotifier(unittest.TestCase):

    def test_start_new_success_case(self):
        rand_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        rand_chat_id = str(random.randint(10000, 99999999))
        rand_message = f"Digest update: {uuid.uuid4().hex}"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "result": {"message_id": random.randint(1, 1000)}}

        with patch("skills.market_portfolio_telegram_notifier.requests.post", return_value=mock_response) as mock_post:
            result = start_new(rand_token, rand_chat_id, rand_message)
            self.assertTrue(result)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertIn(rand_token, args[0])
            self.assertEqual(kwargs["json"]["chat_id"], rand_chat_id)
            self.assertEqual(kwargs["json"]["text"], rand_message)

    def test_send_telegram_notification_alias_success(self):
        rand_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        rand_chat_id = random.randint(10000, 99999999)
        rand_message = f"Seamless digest: {uuid.uuid4().hex}"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True}

        with patch("skills.market_portfolio_telegram_notifier.requests.post", return_value=mock_response) as mock_post:
            result = send_telegram_notification(rand_token, rand_chat_id, rand_message)
            self.assertTrue(result)
            mock_post.assert_called_once()

    def test_telegram_notifier_invalid_inputs(self):
        self.assertFalse(start_new("", "", ""))
        self.assertFalse(start_new("   ", f"{random.randint(1, 100)}", f"{uuid.uuid4().hex}"))
        self.assertFalse(start_new(f"{uuid.uuid4().hex}", "", f"{uuid.uuid4().hex}"))
        self.assertFalse(start_new(f"{uuid.uuid4().hex}", f"{random.randint(1, 100)}", "   "))
        self.assertFalse(send_telegram_notifier("", "", ""))

    def test_telegram_notifier_api_failure_response(self):
        rand_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        rand_chat_id = str(random.randint(10000, 99999999))
        rand_message = f"Failed payload: {uuid.uuid4().hex}"

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"ok": False, "description": f"Bad Request: {uuid.uuid4().hex}"}

        with patch("skills.market_portfolio_telegram_notifier.requests.post", return_value=mock_response):
            result = start_new(rand_token, rand_chat_id, rand_message)
            self.assertFalse(result)

    def test_telegram_notifier_request_exception(self):
        rand_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        rand_chat_id = str(random.randint(10000, 99999999))
        rand_message = f"Exception payload: {uuid.uuid4().hex}"

        with patch("skills.market_portfolio_telegram_notifier.requests.post", side_effect=requests.exceptions.RequestException("Network down")):
            result = start_new(rand_token, rand_chat_id, rand_message)
            self.assertFalse(result)

    def test_telegram_notifier_json_value_error(self):
        rand_token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:16]}"
        rand_chat_id = str(random.randint(10000, 99999999))
        rand_message = f"Malformed payload: {uuid.uuid4().hex}"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch("skills.market_portfolio_telegram_notifier.requests.post", return_value=mock_response):
            result = start_new(rand_token, rand_chat_id, rand_message)
            self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()