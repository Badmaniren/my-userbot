import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
from skills.market_portfolio_api_gateway import start_new, MarketPortfolioAPIGateway, run_pipeline

class TestMarketPortfolioAPIGateway(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        self.url = f"https://example.com/market/{uuid.uuid4().hex[:8]}"
        self.telegram_token = f"token_{uuid.uuid4().hex[:10]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"storage_{uuid.uuid4().hex[:8]}.json"

    @patch('skills.market_portfolio_api_gateway.run_pipeline')
    def test_start_new_success(self, mock_run_pipeline):
        expected_price = round(random.uniform(10.0, 1000.0), 2)
        mock_run_pipeline.return_value = {
            "status": "success",
            "symbol": self.symbol,
            "price": expected_price,
            "timestamp": "active"
        }

        result = start_new(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], self.symbol)
        self.assertEqual(result["price"], expected_price)
        mock_run_pipeline.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

    @patch('skills.market_portfolio_api_gateway.run_pipeline')
    def test_start_new_completed_empty(self, mock_run_pipeline):
        mock_run_pipeline.return_value = None

        result = start_new(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

        self.assertEqual(result, {"status": "completed_empty"})
        mock_run_pipeline.assert_called_once_with(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

    @patch('skills.market_portfolio_api_gateway.send_telegram_notification')
    @patch('skills.market_portfolio_api_gateway.run_pipeline')
    def test_start_new_exception_handling(self, mock_run_pipeline, mock_send_telegram):
        error_message = f"Critical error {uuid.uuid4().hex[:6]}"
        mock_run_pipeline.side_effect = Exception(error_message)

        result = start_new(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], error_message)
        mock_send_telegram.assert_called_once_with(self.telegram_token, self.chat_id, error_message)

    @patch('skills.market_portfolio_api_gateway.PortfolioValuation')
    def test_gateway_export_portfolio_summary(self, mock_portfolio_valuation_cls):
        mock_valuation_instance = mock_portfolio_valuation_cls.return_value
        expected_summary = {
            f"metric_{uuid.uuid4().hex[:4]}": random.randint(100, 5000),
            "status": "ok"
        }
        mock_valuation_instance.get_total_summary.return_value = expected_summary

        gateway = MarketPortfolioAPIGateway(self.storage_file)
        summary = gateway.export_portfolio_summary(self.url)

        self.assertEqual(summary, expected_summary)
        mock_valuation_instance.get_total_summary.assert_called_once_with(self.url)

    @patch('skills.market_portfolio_api_gateway.PortfolioValuation')
    @patch('skills.market_portfolio_api_gateway.MarketParser')
    def test_run_pipeline_success(self, mock_parser_cls, mock_valuation_cls):
        mock_valuation_instance = mock_valuation_cls.return_value
        expected_summary = {"total_value": random.uniform(500.0, 5000.0)}
        mock_valuation_instance.get_total_summary.return_value = expected_summary
        mock_valuation_instance.get_price.return_value = round(random.uniform(50.0, 500.0), 2)

        result = run_pipeline(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], self.symbol)
        self.assertIn("price", result)
        self.assertEqual(result["timestamp"], "active")

    @patch('skills.market_portfolio_api_gateway.PortfolioValuation')
    @patch('skills.market_portfolio_api_gateway.MarketParser')
    def test_run_pipeline_empty_summary(self, mock_parser_cls, mock_valuation_cls):
        mock_valuation_instance = mock_valuation_cls.return_value
        mock_valuation_instance.get_total_summary.return_value = None

        result = run_pipeline(self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file)

        self.assertIsNone(result)

    def test_market_parser_load_data_unicode_resilience(self):
        with patch('skills.db_storage.open', create=True) as mock_open:
            corrupted_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
            mock_open.return_value.__enter__.return_value = io.BytesIO(corrupted_bytes)
            
            from skills.db_storage import MarketParser
            parser = MarketParser(self.storage_file)
            
            with self.assertRaises(Exception):
                parser.load_data(self.storage_file)

if __name__ == '__main__':
    unittest.main()