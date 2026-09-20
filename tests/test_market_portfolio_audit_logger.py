import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json
from skills.market_portfolio_audit_logger import start_new

class TestMarketPortfolioAuditLogger(unittest.TestCase):

    def setUp(self):
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_url = f"https://{uuid.uuid4().hex}.com/{random.randint(100, 999)}"
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_token = uuid.uuid4().hex
        self.random_chat_id = str(random.randint(100000, 999999))
        self.random_price = round(random.uniform(10.0, 1000.0), 2)

    def test_start_new_success_audit_flow(self):
        mock_file_content = json.dumps({
            self.random_symbol: [
                {"price": self.random_price, "timestamp": uuid.uuid4().hex}
            ]
        }).encode('utf-8')

        with patch('skills.market_portfolio_audit_logger.open', create=True) as mock_open, \
             patch('skills.market_portfolio_audit_logger.requests.get') as mock_get, \
             patch('skills.market_portfolio_audit_logger.os.path.exists', return_value=True):

            mock_open.return_value.__enter__.return_value = io.BytesIO(mock_file_content)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = f"<html><body><span class='price'>{self.random_price}</span></body></html>"
            mock_get.return_value = mock_response

            result = start_new(
                symbol=self.random_symbol,
                url=self.random_url,
                storage_file=self.random_storage,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id
            )

            self.assertIsInstance(result, dict)
            self.assertIn("audit_status", result)
            self.assertEqual(result.get("symbol"), self.random_symbol)
            self.assertIn("risk_metrics", result)

    def test_start_new_handles_network_failure(self):
        with patch('skills.market_portfolio_audit_logger.requests.get', side_effect=Exception(uuid.uuid4().hex)):
            with self.assertRaises(Exception):
                start_new(
                    symbol=self.random_symbol,
                    url=self.random_url,
                    storage_file=self.random_storage,
                    telegram_token=self.random_token,
                    chat_id=self.random_chat_id
                )

    def test_start_new_empty_storage_handling(self):
        empty_stream = io.BytesIO(b"{}")

        with patch('skills.market_portfolio_audit_logger.open', create=True) as mock_open, \
             patch('skills.market_portfolio_audit_logger.requests.get') as mock_get, \
             patch('skills.market_portfolio_audit_logger.os.path.exists', return_value=False):

            mock_open.return_value.__enter__.return_value = empty_stream

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = f"<div>{random.randint(1, 100)}</div>"
            mock_get.return_value = mock_response

            res = start_new(
                symbol=self.random_symbol,
                url=self.random_url,
                storage_file=self.random_storage,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id
            )

            self.assertIsInstance(res, dict)
            self.assertEqual(res.get("risk_metrics", {}).get("volatility"), 0.0)

    def test_start_new_telegram_alert_trigger(self):
        high_risk_data = json.dumps({
            self.random_symbol: [
                {"price": 100.0, "timestamp": "t1"},
                {"price": 500.0, "timestamp": "t2"}
            ]
        }).encode('utf-8')

        with patch('skills.market_portfolio_audit_logger.open', create=True) as mock_open, \
             patch('skills.market_portfolio_audit_logger.requests.get') as mock_get, \
             patch('skills.market_portfolio_audit_logger.send_telegram_notification') as mock_send_tg:

            mock_open.return_value.__enter__.return_value = io.BytesIO(high_risk_data)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = "<span>999.9</span>"
            mock_get.return_value = mock_response

            start_new(
                symbol=self.random_symbol,
                url=self.random_url,
                storage_file=self.random_storage,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id
            )

            mock_send_tg.assert_called_once()
            called_args = mock_send_tg.call_args[0]
            self.assertEqual(called_args[0], self.random_token)
            self.assertEqual(called_args[1], self.random_chat_id)

    def test_start_new_file_write_export(self):
        mock_stream = io.BytesIO(b"{}")
        mock_writer = MagicMock()

        with patch('skills.market_portfolio_audit_logger.open', create=True) as mock_open, \
             patch('skills.market_portfolio_audit_logger.requests.get') as mock_get:

            mock_open.side_effect = [mock_stream, mock_writer]

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = f"<div>{self.random_price}</div>"
            mock_get.return_value = mock_response

            start_new(
                symbol=self.random_symbol,
                url=self.random_url,
                storage_file=self.random_storage,
                telegram_token=self.random_token,
                chat_id=self.random_chat_id
            )

            self.assertTrue(mock_open.called)

if __name__ == '__main__':
    unittest.main()