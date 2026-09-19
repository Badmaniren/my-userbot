import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills import market_telegram_pipeline

class TestMarketTelegramPipeline(unittest.TestCase):

    def test_send_telegram_notification(self):
        token = uuid.uuid4().hex
        chat_id = str(random.randint(100000, 999999))
        message = "".join(random.choices(string.ascii_letters + " ", k=15))
        
        with patch("skills.market_telegram_pipeline.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            response = market_telegram_pipeline.send_telegram_notification(token, chat_id, message)
            
            self.assertEqual(response.status_code, 200)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertIn(token, args[0])
            self.assertEqual(kwargs["json"]["chat_id"], chat_id)
            self.assertEqual(kwargs["json"]["text"], message)

    def test_run_pipeline_success(self):
        symbol = uuid.uuid4().hex[:6].upper()
        url = f"https://{uuid.uuid4().hex}.com"
        token = uuid.uuid4().hex
        chat_id = str(random.randint(1000, 9999))
        storage_file = f"{uuid.uuid4().hex}.json"
        random_price = round(random.uniform(1.0, 1000.0), 2)

        with patch("skills.market_telegram_pipeline.MarketParser") as MockParser, \
             patch("skills.market_telegram_pipeline.send_telegram_notification") as mock_send:
            
            parser_instance = MockParser.return_value
            parser_instance.fetch_price.return_value = random_price
            parser_instance.load_data.return_value = {symbol: random_price}
            
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_send.return_value = mock_resp

            result = market_telegram_pipeline.run_pipeline(
                symbol=symbol,
                url=url,
                telegram_token=token,
                chat_id=chat_id,
                storage_file=storage_file
            )

            self.assertTrue(result)
            parser_instance.fetch_price.assert_called_once_with(url)
            parser_instance.fetch_and_store.assert_called_once_with(symbol, random_price)
            mock_send.assert_called_once()
            called_message = mock_send.call_args[0][2]
            self.assertIn(symbol, called_message)
            self.assertIn(str(random_price), called_message)

    def test_run_pipeline_parser_failure(self):
        symbol = uuid.uuid4().hex[:6].upper()
        url = f"https://{uuid.uuid4().hex}.org"
        token = uuid.uuid4().hex
        chat_id = str(random.randint(1000, 9999))
        storage_file = f"{uuid.uuid4().hex}.json"
        exception_message = uuid.uuid4().hex

        with patch("skills.market_telegram_pipeline.MarketParser") as MockParser, \
             patch("skills.market_telegram_pipeline.send_telegram_notification") as mock_send:
            
            parser_instance = MockParser.return_value
            parser_instance.fetch_price.side_effect = Exception(exception_message)

            with self.assertRaises(Exception) as ctx:
                market_telegram_pipeline.run_pipeline(
                    symbol=symbol,
                    url=url,
                    telegram_token=token,
                    chat_id=chat_id,
                    storage_file=storage_file
                )
            
            self.assertEqual(str(ctx.exception), exception_message)
            mock_send.assert_not_called()

    def test_run_market_telegram_pipeline(self):
        storage_file = f"{uuid.uuid4().hex}.json"
        symbol = uuid.uuid4().hex[:5].upper()
        chat_id = str(random.randint(100, 999))
        url = f"https://{uuid.uuid4().hex}.net"
        token = uuid.uuid4().hex
        random_price = round(random.uniform(10.0, 500.0), 2)

        with patch("skills.market_telegram_pipeline.MarketParser") as MockParser, \
             patch("skills.market_telegram_pipeline.send_telegram_notification") as mock_send:
            
            parser_instance = MockParser.return_value
            parser_instance.load_data.return_value = {symbol: random_price}

            result = market_telegram_pipeline.run_market_telegram_pipeline(
                storage_file=storage_file,
                symbol=symbol,
                chat_id=chat_id,
                url=url,
                telegram_token=token
            )

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["sent_symbol"], symbol)
            self.assertEqual(result["sent_price"], random_price)
            mock_send.assert_called_once()
            args = mock_send.call_args[0]
            self.assertEqual(args[0], token)
            self.assertEqual(args[1], chat_id)
            self.assertIn(symbol, args[2])
            self.assertIn(str(random_price), args[2])