import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

from skills import market_telegram_pipeline

class TestMarketTelegramPipeline(unittest.TestCase):

    def setUp(self):
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_price = round(random.uniform(10.0, 1000.0), 2)
        self.random_url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.random_chat_id = str(random.randint(100000, 999999))
        self.random_filename = f"{uuid.uuid4().hex}.json"

    @patch('skills.market_telegram_pipeline.requests.post')
    def test_pipeline_execution_success(self, mock_requests_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_requests_post.return_value = mock_response

        with patch('skills.market_telegram_pipeline.MarketParser') as MockParserClass, \
             patch('skills.market_telegram_pipeline.db_storage') as mock_db_storage:
            
            instance = MockParserClass.return_value
            instance.fetch_price.return_value = self.random_price
            instance.load_data.return_value = {self.random_symbol: self.random_price}

            token = f"{random.randint(1000,9999)}:{uuid.uuid4().hex}"
            result = market_telegram_pipeline.run_pipeline(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=token,
                chat_id=self.random_chat_id,
                storage_file=self.random_filename
            )

            MockParserClass.assert_called_once_with(self.random_filename)
            instance.fetch_and_store.assert_called_once_with(self.random_symbol, self.random_price)
            mock_requests_post.assert_called_once()
            self.assertTrue(result)

    @patch('skills.market_telegram_pipeline.requests.post')
    def test_pipeline_parser_failure(self, mock_requests_post):
        with patch('skills.market_telegram_pipeline.MarketParser') as MockParserClass:
            instance = MockParserClass.return_value
            instance.fetch_price.side_effect = Exception(uuid.uuid4().hex)

            token = f"{random.randint(1000,9999)}:{uuid.uuid4().hex}"
            result = market_telegram_pipeline.run_pipeline(
                symbol=self.random_symbol,
                url=self.random_url,
                telegram_token=token,
                chat_id=self.random_chat_id,
                storage_file=self.random_filename
            )

            mock_requests_post.assert_not_called()
            self.assertFalse(result)

    def test_telegram_sender_payload(self):
        token = f"{random.randint(1000,9999)}:{uuid.uuid4().hex}"
        message = uuid.uuid4().hex

        with patch('skills.market_telegram_pipeline.requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_post.return_value = mock_resp

            market_telegram_pipeline.send_telegram_notification(
                token=token,
                chat_id=self.random_chat_id,
                message=message
            )

            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            self.assertIn(self.random_chat_id, str(kwargs))
            self.assertIn(message, str(kwargs))
            self.assertIn(token, mock_post.call_args[0][0])

    def test_pipeline_uses_correct_dependencies(self):
        self.assertTrue(hasattr(market_telegram_pipeline, 'MarketParser'))
        self.assertTrue(hasattr(market_telegram_pipeline, 'db_storage'))

if __name__ == '__main__':
    unittest.main()