import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import requests
from skills.market_telegram_pipeline import (
    send_telegram_notification,
    _load_parser_or_db_data,
    run_pipeline,
    run_market_telegram_pipeline
)

class TestMarketTelegramPipeline(unittest.TestCase):

    def test_send_telegram_notification_success(self):
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(10000, 99999))
        rand_message = f"msg_{uuid.uuid4().hex}"
        expected_url = f"https://api.telegram.org/bot{rand_token}/sendMessage"
        expected_payload = {
            "chat_id": rand_chat_id,
            "text": rand_message
        }

        with patch('skills.market_telegram_pipeline.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            response = send_telegram_notification(rand_token, rand_chat_id, rand_message)

            mock_post.assert_called_once_with(expected_url, json=expected_payload)
            self.assertEqual(response.status_code, 200)

    def test_load_parser_or_db_data_parser_with_storage(self):
        rand_symbol = uuid.uuid4().hex
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_price = round(random.uniform(1.0, 1000.0), 2)

        mock_parser = MagicMock()
        mock_parser.load_data.return_value = {rand_symbol: rand_price}

        result = _load_parser_or_db_data(mock_parser, rand_storage, rand_symbol, 0.0)

        mock_parser.load_data.assert_called_once_with(rand_storage)
        self.assertEqual(result, rand_price)

    def test_load_parser_or_db_data_parser_fallback_no_args(self):
        rand_symbol = uuid.uuid4().hex
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_price = round(random.uniform(1.0, 1000.0), 2)

        mock_parser = MagicMock()
        mock_parser.load_data.side_effect = [TypeError("Unexpected argument"), {rand_symbol: rand_price}]

        result = _load_parser_or_db_data(mock_parser, rand_storage, rand_symbol, 0.0)

        self.assertEqual(mock_parser.load_data.call_count, 2)
        self.assertEqual(result, rand_price)

    def test_load_parser_or_db_data_db_storage_fallback(self):
        rand_symbol = uuid.uuid4().hex
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_price = round(random.uniform(1.0, 1000.0), 2)

        mock_parser = object()

        with patch('skills.market_telegram_pipeline.db_storage') as mock_db:
            mock_db.load_data.side_effect = AttributeError("No load_data")
            mock_db.get_data.return_value = {rand_symbol: rand_price}

            result = _load_parser_or_db_data(mock_parser, rand_storage, rand_symbol, 0.0)

            mock_db.get_data.assert_called_once_with(rand_storage)
            self.assertEqual(result, rand_price)

    def test_run_pipeline_success(self):
        rand_symbol = uuid.uuid4().hex
        rand_url = f"https://{uuid.uuid4().hex}.com"
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(100, 999))
        rand_storage = f"{uuid.uuid4().hex}.db"
        rand_price = round(random.uniform(10.0, 500.0), 2)

        with patch('skills.market_telegram_pipeline.MarketParser') as MockParserClass, \
             patch('skills.market_telegram_pipeline._load_parser_or_db_data') as mock_load, \
             patch('skills.market_telegram_pipeline.send_telegram_notification') as mock_send:

            mock_parser_instance = MockParserClass.return_value
            mock_parser_instance.fetch_price.return_value = rand_price
            mock_load.return_value = rand_price

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_send.return_value = mock_resp

            success = run_pipeline(rand_symbol, rand_url, rand_token, rand_chat_id, rand_storage)

            MockParserClass.assert_called_once_with(rand_storage)
            mock_parser_instance.fetch_price.assert_called_once_with(rand_url)
            mock_parser_instance.fetch_and_store.assert_called_once_with(rand_symbol, rand_price)
            mock_load.assert_called_once_with(mock_parser_instance, rand_storage, rand_symbol, rand_price)
            mock_send.assert_called_once_with(
                rand_token,
                rand_chat_id,
                f"Market Update: {rand_symbol} = {rand_price}"
            )
            self.assertTrue(success)

    def test_run_market_telegram_pipeline_success(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = uuid.uuid4().hex
        rand_chat_id = str(random.randint(1000, 9999))
        rand_url = f"https://{uuid.uuid4().hex}.org"
        rand_token = uuid.uuid4().hex
        rand_price = round(random.uniform(50.0, 1500.0), 2)

        with patch('skills.market_telegram_pipeline.MarketParser') as MockParserClass, \
             patch('skills.market_telegram_pipeline._load_parser_or_db_data') as mock_load, \
             patch('skills.market_telegram_pipeline.send_telegram_notification') as mock_send:

            mock_parser_instance = MockParserClass.return_value
            mock_load.return_value = rand_price

            result = run_market_telegram_pipeline(
                storage_file=rand_storage,
                symbol=rand_symbol,
                chat_id=rand_chat_id,
                url=rand_url,
                telegram_token=rand_token
            )

            MockParserClass.assert_called_once_with(rand_storage)
            mock_load.assert_called_once_with(mock_parser_instance, rand_storage, rand_symbol, 0.0)
            mock_send.assert_called_once_with(
                rand_token,
                rand_chat_id,
                f"Integration Market Update: {rand_symbol} = {rand_price}"
            )
            self.assertEqual(result, {
                "status": "success",
                "sent_symbol": rand_symbol,
                "sent_price": rand_price
            })

if __name__ == '__main__':
    unittest.main()