import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_performance_tracker import start_new

class TestMarketPortfolioPerformanceTracker(unittest.TestCase):

    def test_start_new_success_execution(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        rand_url = f"https://{uuid.uuid4().hex}.com/market"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        
        mock_performance_data = {
            "symbol": rand_symbol,
            "return": round(random.uniform(-50.0, 100.0), 2),
            "volatility": round(random.uniform(1.0, 25.0), 2),
            "sharpe_ratio": round(random.uniform(0.1, 3.5), 2)
        }

        with patch('skills.market_portfolio_performance_tracker.MarketParser') as mock_parser_cls, \
             patch('skills.market_portfolio_performance_tracker.send_telegram_notification') as mock_notify:
            
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.load_data.return_value = mock_performance_data

            result = start_new(
                symbol=rand_symbol,
                url=rand_url,
                telegram_token=rand_token,
                chat_id=rand_chat,
                storage_file=rand_storage
            )

            mock_parser_cls.assert_called_once_with(rand_storage)
            mock_parser_instance.load_data.assert_called_once()
            mock_notify.assert_called_once()
            
            called_args = mock_notify.call_args[0]
            self.assertEqual(called_args[0], rand_token)
            self.assertEqual(called_args[1], rand_chat)
            self.assertIn(rand_symbol, called_args[2])
            self.assertEqual(result, mock_performance_data)

    def test_start_new_handles_exceptions_gracefully(self):
        rand_storage = f"db_{uuid.uuid4().hex}.dat"
        rand_symbol = f"TICK_{uuid.uuid4().hex[:5]}"
        rand_url = f"http://{uuid.uuid4().hex}.net/api"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(1000000, 9999999))

        error_msg = f"Database corrupted: {uuid.uuid4().hex}"

        with patch('skills.market_portfolio_performance_tracker.MarketParser') as mock_parser_cls, \
             patch('skills.market_portfolio_performance_tracker.send_telegram_notification') as mock_notify:
            
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.load_data.side_effect = Exception(error_msg)

            result = start_new(
                symbol=rand_symbol,
                url=rand_url,
                telegram_token=rand_token,
                chat_id=rand_chat,
                storage_file=rand_storage
            )

            mock_parser_cls.assert_called_once_with(rand_storage)
            mock_notify.assert_called()
            
            notification_message = mock_notify.call_args[0][2]
            self.assertIn(error_msg, notification_message)
            self.assertIsNone(result)

    def test_start_new_with_stream_mock_io(self):
        rand_storage = f"store_{uuid.uuid4().hex}"
        rand_symbol = f"AST_{uuid.uuid4().hex[:4]}"
        rand_url = f"https://{uuid.uuid4().hex}.org/stream"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100, 999))

        raw_stream_bytes = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))

        with patch('skills.market_portfolio_performance_tracker.MarketParser') as mock_parser_cls, \
             patch('skills.market_portfolio_performance_tracker.send_telegram_notification'):
            
            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.load_data.return_value = {"stream_dump": raw_stream_bytes.read()}

            res = start_new(
                symbol=rand_symbol,
                url=rand_url,
                telegram_token=rand_token,
                chat_id=rand_chat,
                storage_file=rand_storage
            )

            self.assertIn("stream_dump", res)
            self.assertIsInstance(res["stream_dump"], bytes)

if __name__ == '__main__':
    unittest.main()