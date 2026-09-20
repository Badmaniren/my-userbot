import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import string
import io
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from skills.market_portfolio_analytics import start_new


class TestStartNewMarketPortfolioAnalytics(unittest.TestCase):

    def test_start_new_execution_with_random_payload(self):
        rand_prefix = uuid.uuid4().hex[:8]
        rand_symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        rand_url = f"https://{rand_prefix}.com/market/{rand_symbol.lower()}"
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(1000000, 99999999))
        rand_storage = f"{uuid.uuid4().hex}.json"
        
        mock_price = round(random.uniform(10.0, 5000.0), 2)
        mock_html_content = f"<html><body><span class='price'>{mock_price}</span></body></html>"
        random_bytes = io.BytesIO(mock_html_content.encode('utf-8'))

        with patch('skills.market_portfolio_analytics.MarketParser') as mock_parser_cls, \
             patch('skills.market_portfolio_analytics.MarketReportGenerator') as mock_report_cls, \
             patch('skills.market_portfolio_analytics.run_market_telegram_pipeline') as mock_pipeline, \
             patch('requests.get') as mock_requests_get:

            mock_parser_instance = mock_parser_cls.return_value
            mock_parser_instance.fetch_price.return_value = mock_price
            mock_parser_instance.load_data.return_value = [{rand_symbol: mock_price}]

            mock_report_instance = mock_report_cls.return_value
            mock_report_instance.generate_symbol_report.return_value = {
                "symbol": rand_symbol, 
                "metrics": mock_price
            }
            mock_report_instance.get_raw_stream_dump.return_value = rand_prefix

            mock_response = mock_requests_get.return_value
            mock_response.status_code = 200
            mock_response.raw = random_bytes
            mock_response.text = mock_html_content

            try:
                result = start_new(
                    storage_file=rand_storage,
                    symbol=rand_symbol,
                    url=rand_url,
                    telegram_token=rand_token,
                    chat_id=rand_chat_id
                )
            except TypeError:
                try:
                    result = start_new(rand_storage, rand_symbol, rand_url)
                except TypeError:
                    result = start_new()

            mock_parser_cls.assert_called()
            mock_report_cls.assert_called()

            if mock_pipeline.called:
                mock_pipeline.assert_called_once()
                called_args, called_kwargs = mock_pipeline.call_args
                all_call_args = list(called_args) + list(called_kwargs.values())
                self.assertTrue(
                    any(rand_symbol in str(arg) for arg in all_call_args),
                    f"Случайный символ {rand_symbol} не найден в вызове пайплайна!"
                )


    def test_start_new_handles_exceptions_gracefully(self):
        rand_storage = f"{uuid.uuid4().hex}.db"
        rand_symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        rand_url = f"https://{uuid.uuid4().hex}.net/api"
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(100, 99999))

        with patch('skills.market_portfolio_analytics.MarketParser', side_effect=Exception(rand_storage)) as mock_parser_cls:
            with self.assertRaises(Exception):
                start_new(
                    storage_file=rand_storage,
                    symbol=rand_symbol,
                    url=rand_url,
                    telegram_token=rand_token,
                    chat_id=rand_chat_id
                )


if __name__ == '__main__':
    unittest.main()