import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json

from skills.market_portfolio_api_gateway import start_new


class TestMarketPortfolioApiGateway(unittest.TestCase):

    def test_start_new_success(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_url = f"https://{uuid.uuid4().hex}.com/api"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_price = round(random.uniform(10.0, 1000.0), 2)

        mock_pipeline_result = {
            "status": "success",
            "symbol": rand_symbol,
            "price": rand_price,
            "timestamp": uuid.uuid4().hex
        }

        with patch('skills.market_portfolio_api_gateway.run_pipeline') as mock_run:
            mock_run.return_value = mock_pipeline_result
            
            result = start_new(
                symbol=rand_symbol,
                url=rand_url,
                telegram_token=rand_token,
                chat_id=rand_chat,
                storage_file=rand_storage
            )

            mock_run.assert_called_once_with(
                rand_symbol,
                rand_url,
                rand_token,
                rand_chat,
                rand_storage
            )
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("symbol"), rand_symbol)
            self.assertEqual(result.get("price"), rand_price)
            self.assertEqual(result.get("status"), "success")

    def test_start_new_failure_handling(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        rand_url = f"https://{uuid.uuid4().hex}.org/data"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(10000, 99999))
        rand_storage = f"{uuid.uuid4().hex}.db"

        err_msg = f"Connection timeout: {uuid.uuid4().hex}"

        with patch('skills.market_portfolio_api_gateway.run_pipeline', side_effect=Exception(err_msg)) as mock_run:
            with patch('skills.market_portfolio_api_gateway.send_telegram_notification') as mock_notify:
                result = start_new(
                    symbol=rand_symbol,
                    url=rand_url,
                    telegram_token=rand_token,
                    chat_id=rand_chat,
                    storage_file=rand_storage
                )

                mock_run.assert_called_once()
                mock_notify.assert_called_once()
                
                self.assertIsInstance(result, dict)
                self.assertEqual(result.get("status"), "error")
                self.assertIn(err_msg, result.get("message", ""))

    def test_start_new_empty_returns(self):
        rand_symbol = ''.join(random.choices(string.ascii_lowercase, k=6))
        rand_url = f"http://{uuid.uuid4().hex}.net"
        rand_token = uuid.uuid4().hex
        rand_chat = uuid.uuid4().hex
        rand_storage = f"{uuid.uuid4().hex}.dat"

        with patch('skills.market_portfolio_api_gateway.run_pipeline', return_value=None) as mock_run:
            result = start_new(
                symbol=rand_symbol,
                url=rand_url,
                telegram_token=rand_token,
                chat_id=rand_chat,
                storage_file=rand_storage
            )

            mock_run.assert_called_once()
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("status"), "completed_empty")


if __name__ == '__main__':
    unittest.main()