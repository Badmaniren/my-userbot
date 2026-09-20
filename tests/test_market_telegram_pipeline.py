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
        self.random_token = f"{random.randint(100, 999)}:{uuid.uuid4().hex[:10]}"
        self.random_chat_id = str(random.randint(100000, 999999))
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.random_url = f"https://{''.join(random.choices(string.ascii_lowercase, k=8))}.com/{uuid.uuid4().hex[:6]}"
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_price = round(random.uniform(10.0, 1500.0), 2)

    def test_send_telegram_notification_success(self):
        random_message = f"Report: {uuid.uuid4().hex}"
        expected_url = f"https://api.telegram.org/bot{self.random_token}/sendMessage"
        expected_payload = {
            "chat_id": self.random_chat_id,
            "text": random_message
        }

        with patch("skills.market_telegram_pipeline.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            response = send_telegram_notification(self.random_token, self.random_chat_id, random_message)

            mock_post.assert_called_once_with(expected_url, json=expected_payload)
            self.assertEqual(response.status_code, 200)

    def test_run_pipeline_success(self):
        with patch("skills.market_telegram_pipeline.MarketParser") as MockParser, \
             patch("skills.market_telegram_pipeline.send_telegram_notification") as mock_send:

            instance = MockParser.return_value
            instance.fetch_price.return_value = self.random_price
            instance.load_data.return_value = {self.random_symbol: self.random_price}

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_send.return_value = mock_resp

            result = run_pipeline(
                self.random_symbol,
                self.random_url,
                self.random_token,
                self.random_chat_id,
                self.random_storage
            )

            MockParser.assert_called_once_with(self.random_storage)
            instance.fetch_price.assert_called_once_with(self.random_url)
            instance.fetch_and_store.assert_called_once_with(self.random_symbol, self.random_price)
            
            expected_message = f"Market Update: {self.random_symbol} = {self.random_price}"
            mock_send.assert_called_once_with(self.random_token, self.random_chat_id, expected_message)
            self.assertTrue(result)

    def test_run_pipeline_failure(self):
        with patch("skills.market_telegram_pipeline.MarketParser") as MockParser, \
             patch("skills.market_telegram_pipeline.send_telegram_notification") as mock_send:

            instance = MockParser.return_value
            instance.fetch_price.return_value = self.random_price
            instance.load_data.return_value = {}

            mock_resp = MagicMock()
            mock_resp.status_code = 400
            mock_send.return_value = mock_resp

            result = run_pipeline(
                self.random_symbol,
                self.random_url,
                self.random_token,
                self.random_chat_id,
                self.random_storage
            )

            self.assertFalse(result)

    def test_run_market_telegram_pipeline(self):
        with patch("skills.market_telegram_pipeline.MarketParser") as MockParser, \
             patch("skills.market_telegram_pipeline.send_telegram_notification") as mock_send:

            instance = MockParser.return_value
            instance.load_data.return_value = {self.random_symbol: self.random_price}

            result = run_market_telegram_pipeline(
                storage_file=self.random_storage,
                symbol=self.random_symbol,
                chat_id=self.random_chat_id,
                url=self.random_url,
                telegram_token=self.random_token
            )

            MockParser.assert_called_once_with(self.random_storage)
            
            expected_message = f"Integration Market Update: {self.random_symbol} = {self.random_price}"
            mock_send.assert_called_once_with(self.random_token, self.random_chat_id, expected_message)

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["sent_symbol"], self.random_symbol)
            self.assertEqual(result["sent_price"], self.random_price)

if __name__ == "__main__":
    unittest.main()