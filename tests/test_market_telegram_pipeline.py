import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
from skills.market_telegram_pipeline import (
    send_telegram_notification,
    run_pipeline,
    run_market_telegram_pipeline
)

class TestMarketTelegramPipeline(unittest.TestCase):

    def test_send_telegram_notification_success(self):
        rand_token = f"{random.randint(100000, 999999)}:ABC-{uuid.uuid4().hex[:8]}"
        rand_chat_id = str(random.randint(10000, 99999))
        rand_message = f"Alert: {uuid.uuid4().hex}"

        with patch('skills.market_telegram_pipeline.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            response = send_telegram_notification(rand_token, rand_chat_id, rand_message)

            self.assertEqual(response.status_code, 200)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertIn(rand_token, args[0])
            self.assertEqual(kwargs['json']['chat_id'], rand_chat_id)
            self.assertEqual(kwargs['json']['text'], rand_message)

    def test_run_pipeline_success(self):
        rand_symbol = uuid.uuid4().hex[:5].upper()
        rand_url = f"https://{uuid.uuid4().hex[:8]}.com/market"
        rand_token = f"{random.randint(100000, 999999)}:XYZ-{uuid.uuid4().hex[:8]}"
        rand_chat_id = str(random.randint(10000, 99999))
        rand_file = f"{uuid.uuid4().hex}.json"
        rand_price = round(random.uniform(10.0, 1000.0), 2)

        with patch('skills.market_telegram_pipeline.MarketParser') as MockParserClass, \
             patch('skills.market_telegram_pipeline.send_telegram_notification') as mock_notify:
            
            parser_instance = MockParserClass.return_value
            parser_instance.fetch_price.return_value = rand_price
            parser_instance.load_data.return_value = {rand_symbol: rand_price}

            mock_notify_response = MagicMock()
            mock_notify_response.status_code = 200
            mock_notify.return_value = mock_notify_response

            result = run_pipeline(rand_symbol, rand_url, rand_token, rand_chat_id, rand_file)

            self.assertTrue(result)
            parser_instance.fetch_price.assert_called_once_with(rand_url)
            parser_instance.fetch_and_store.assert_called_once_with(rand_symbol, rand_price)
            mock_notify.assert_called_once()
            
            called_args = mock_notify.call_args[0]
            self.assertEqual(called_args[0], rand_token)
            self.assertEqual(called_args[1], rand_chat_id)
            self.assertIn(rand_symbol, called_args[2])
            self.assertIn(str(rand_price), called_args[2])

    def test_run_pipeline_fallback_load_data_type_error(self):
        rand_symbol = uuid.uuid4().hex[:5].upper()
        rand_url = f"https://{uuid.uuid4().hex[:8]}.net/api"
        rand_token = f"{random.randint(100000, 999999)}:DEF-{uuid.uuid4().hex[:8]}"
        rand_chat_id = str(random.randint(10000, 99999))
        rand_file = f"{uuid.uuid4().hex}.db"
        rand_price = round(random.uniform(1.0, 50.0), 2)

        with patch('skills.market_telegram_pipeline.MarketParser') as MockParserClass, \
             patch('skills.market_telegram_pipeline.send_telegram_notification') as mock_notify:
            
            parser_instance = MockParserClass.return_value
            parser_instance.fetch_price.return_value = rand_price
            
            def load_data_side_effect(filename=None):
                if filename is not None:
                    raise TypeError("Unexpected argument")
                return {rand_symbol: rand_price}

            parser_instance.load_data.side_effect = load_data_side_effect

            mock_notify_response = MagicMock()
            mock_notify_response.status_code = 200
            mock_notify.return_value = mock_notify_response

            result = run_pipeline(rand_symbol, rand_url, rand_token, rand_chat_id, rand_file)

            self.assertTrue(result)
            self.assertEqual(parser_instance.load_data.call_count, 2)

    def test_run_market_telegram_pipeline(self):
        rand_symbol = uuid.uuid4().hex[:4].upper()
        rand_chat_id = str(random.randint(1000, 99999))
        rand_file = f"{uuid.uuid4().hex}.json"
        rand_url = f"https://{uuid.uuid4().hex[:6]}.org/feed"
        rand_token = f"{random.randint(100, 999)}:TKN-{uuid.uuid4().hex[:6]}"
        rand_price = round(random.uniform(500.0, 5000.0), 2)

        with patch('skills.market_telegram_pipeline.MarketParser') as MockParserClass, \
             patch('skills.market_telegram_pipeline.send_telegram_notification') as mock_notify:
            
            parser_instance = MockParserClass.return_value
            parser_instance.load_data.return_value = {rand_symbol: rand_price}

            result = run_market_telegram_pipeline(
                storage_file=rand_file,
                symbol=rand_symbol,
                chat_id=rand_chat_id,
                url=rand_url,
                telegram_token=rand_token
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["sent_symbol"], rand_symbol)
            self.assertEqual(result["sent_price"], rand_price)
            mock_notify.assert_called_once()
            
            called_args = mock_notify.call_args[0]
            self.assertEqual(called_args[0], rand_token)
            self.assertEqual(called_args[1], rand_chat_id)
            self.assertIn(rand_symbol, called_args[2])

if __name__ == '__main__':
    unittest.main()