import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_telegram_pipeline import (
    send_telegram_notification,
    run_pipeline,
    run_market_telegram_pipeline
)

class TestMarketTelegramPipeline(unittest.TestCase):

    def setUp(self):
        self.token = f"{random.randint(100000, 999999)}:{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex[:8]}.com/{uuid.uuid4().hex[:6]}"
        self.storage_file = f"{uuid.uuid4().hex[:10]}.json"
        self.price = round(random.uniform(1.0, 1000.0), 2)

    @patch("skills.market_telegram_pipeline.requests.post")
    def test_send_telegram_notification_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = random.choice([200, 201])
        mock_post.return_value = mock_response

        message = f"Test message {uuid.uuid4().hex[:6]}"
        response = send_telegram_notification(self.token, self.chat_id, message)

        self.assertEqual(response.status_code, mock_response.status_code)
        mock_post.assert_called_once()
        called_url = mock_post.call_args[0][0]
        self.assertIn(self.token, called_url)
        called_json = mock_post.call_args[1]["json"]
        self.assertEqual(called_json["chat_id"], self.chat_id)
        self.assertEqual(called_json["text"], message)

    @patch("skills.market_telegram_pipeline.db_storage")
    @patch("skills.market_telegram_pipeline.MarketParser")
    @patch("skills.market_telegram_pipeline.send_telegram_notification")
    def test_run_pipeline_success(self, mock_send_notification, mock_parser_cls, mock_db_storage):
        mock_parser = mock_parser_cls.return_value
        mock_parser.fetch_price.return_value = self.price
        mock_parser.load_data.return_value = {self.symbol: self.price}

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_send_notification.return_value = mock_resp

        result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertTrue(result)
        mock_parser.fetch_price.assert_called_once_with(self.url)
        mock_parser.fetch_and_store.assert_called_once_with(self.symbol, self.price)
        mock_send_notification.assert_called_once()

    @patch("skills.market_telegram_pipeline.db_storage")
    @patch("skills.market_telegram_pipeline.MarketParser")
    @patch("skills.market_telegram_pipeline.send_telegram_notification")
    def test_run_pipeline_failure(self, mock_send_notification, mock_parser_cls, mock_db_storage):
        mock_parser = mock_parser_cls.return_value
        mock_parser.fetch_price.return_value = self.price
        mock_parser.load_data.side_effect = TypeError("Unexpected signature")

        if hasattr(mock_db_storage, "load_data"):
            mock_db_storage.load_data.return_value = {self.symbol: self.price}
        elif hasattr(mock_db_storage, "get_data"):
            mock_db_storage.get_data.return_value = {self.symbol: self.price}

        mock_resp = MagicMock()
        mock_resp.status_code = random.choice([400, 401, 403, 404, 500])
        mock_send_notification.return_value = mock_resp

        result = run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertFalse(result)
        mock_send_notification.assert_called_once()

    @patch("skills.market_telegram_pipeline.db_storage")
    @patch("skills.market_telegram_pipeline.MarketParser")
    @patch("skills.market_telegram_pipeline.send_telegram_notification")
    def test_run_market_telegram_pipeline(self, mock_send_notification, mock_parser_cls, mock_db_storage):
        mock_parser = mock_parser_cls.return_value
        mock_parser.load_data.return_value = {self.symbol: self.price}

        result = run_market_telegram_pipeline(
            storage_file=self.storage_file,
            symbol=self.symbol,
            chat_id=self.chat_id,
            url=self.url,
            telegram_token=self.token
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["sent_symbol"], self.symbol)
        self.assertEqual(result["sent_price"], self.price)
        mock_send_notification.assert_called_once()
        called_args = mock_send_notification.call_args[0]
        self.assertEqual(called_args[0], self.token)
        self.assertEqual(called_args[1], self.chat_id)
        self.assertIn(self.symbol, called_args[2])

if __name__ == "__main__":
    unittest.main()