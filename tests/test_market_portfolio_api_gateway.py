import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_portfolio_api_gateway import (
    send_telegram_notification,
    run_pipeline,
    MarketPortfolioAPIGateway,
    start_new
)

class TestMarketPortfolioAPIGateway(unittest.TestCase):

    def setUp(self):
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/{random.choice(['api', 'market', 'feed'])}"
        self.telegram_token = f"{random.randint(1000, 9999)}:{uuid.uuid4().hex[:10]}"
        self.chat_id = f"-{random.randint(1000000, 99999999)}"
        self.storage_file = f"{uuid.uuid4().hex}.json"

    def test_send_telegram_notification(self):
        result = send_telegram_notification(self.telegram_token, self.chat_id, uuid.uuid4().hex)
        self.assertIsNone(result)

    def test_run_pipeline_success(self):
        expected_summary = {uuid.uuid4().hex: random.uniform(1.0, 1000.0)}
        expected_price = random.uniform(50.0, 500.0)

        with patch('skills.market_portfolio_api_gateway.MarketParser') as mock_parser_cls, \
             patch('skills.market_portfolio_api_gateway.PortfolioValuation') as mock_valuation_cls:

            mock_valuation = mock_valuation_cls.return_value
            mock_valuation.get_total_summary.return_value = expected_summary
            mock_valuation.get_price.return_value = expected_price

            result = run_pipeline(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["symbol"], self.symbol)
            self.assertEqual(result["price"], expected_price)
            self.assertEqual(result["timestamp"], "active")

    def test_run_pipeline_empty_summary(self):
        with patch('skills.market_portfolio_api_gateway.MarketParser'), \
             patch('skills.market_portfolio_api_gateway.PortfolioValuation') as mock_valuation_cls:

            mock_valuation = mock_valuation_cls.return_value
            mock_valuation.get_total_summary.return_value = None

            result = run_pipeline(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertIsNone(result)

    def test_market_portfolio_api_gateway_export(self):
        expected_export_data = {uuid.uuid4().hex: random.randint(10, 100)}

        with patch('skills.market_portfolio_api_gateway.MarketParser'), \
             patch('skills.market_portfolio_api_gateway.PortfolioValuation') as mock_valuation_cls, \
             patch('skills.market_portfolio_api_gateway.MarketReportGenerator'):

            mock_valuation = mock_valuation_cls.return_value
            mock_valuation.get_total_summary.return_value = expected_export_data

            gateway = MarketPortfolioAPIGateway(self.storage_file)
            summary = gateway.export_portfolio_summary(self.url)

            self.assertEqual(summary, expected_export_data)
            mock_valuation.get_total_summary.assert_called_once_with(self.url)

    def test_start_new_completed_empty(self):
        with patch('skills.market_portfolio_api_gateway.run_pipeline', return_value=None):
            result = start_new(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)
            self.assertEqual(result, {"status": "completed_empty"})

    def test_start_new_success(self):
        expected_result = {
            "status": "success",
            "symbol": self.symbol,
            "price": random.uniform(10.0, 999.0),
            "timestamp": "active"
        }
        with patch('skills.market_portfolio_api_gateway.run_pipeline', return_value=expected_result):
            result = start_new(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)
            self.assertEqual(result, expected_result)

    def test_start_new_exception_handling(self):
        error_message = uuid.uuid4().hex

        with patch('skills.market_portfolio_api_gateway.run_pipeline', side_effect=Exception(error_message)), \
             patch('skills.market_portfolio_api_gateway.send_telegram_notification') as mock_send_tg:
            
            result = start_new(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

            self.assertEqual(result["status"], "error")
            self.assertEqual(result["message"], error_message)
            mock_send_tg.assert_called_once_with(self.telegram_token, self.chat_id, error_message)

if __name__ == '__main__':
    unittest.main()