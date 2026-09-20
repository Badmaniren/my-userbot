import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_analytics import start_new, PortfolioAnalytics

class TestMarketPortfolioAnalytics(unittest.TestCase):

    def test_portfolio_analytics_calculation_success(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        p1 = round(random.uniform(10.0, 50.0), 2)
        p2 = round(random.uniform(51.0, 100.0), 2)
        mock_data = [{rand_symbol: p1}, {rand_symbol: p2}]

        with patch('skills.db_storage.MarketParser') as mock_parser_cls:
            instance = mock_parser_cls.return_value
            instance.load_data.return_value = mock_data

            analyzer = PortfolioAnalytics(storage_file=f"{uuid.uuid4().hex}.json")
            result = analyzer.calculate_metrics(rand_symbol)

            self.assertEqual(result["symbol"], rand_symbol)
            self.assertEqual(result["prices"], [p1, p2])
            expected_return = (p2 - p1) / p1
            self.assertAlmostEqual(result["return"], expected_return)

    def test_portfolio_analytics_fallback_history(self):
        rand_symbol = f"SYM_{uuid.uuid4().hex[:6]}"
        p_list = [round(random.uniform(1.0, 10.0), 2), round(random.uniform(11.0, 20.0), 2)]

        with patch('skills.db_storage.MarketParser') as mock_parser_cls:
            instance = mock_parser_cls.return_value
            instance.load_data.side_effect = Exception("Storage error")
            instance.get_history.return_value = p_list

            analyzer = PortfolioAnalytics(storage_file=f"{uuid.uuid4().hex}.json")
            result = analyzer.calculate_metrics(rand_symbol)

            self.assertEqual(result["symbol"], rand_symbol)
            self.assertEqual(result["prices"], p_list)

    def test_start_new_pipeline_execution(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = f"COIN_{uuid.uuid4().hex[:4]}"
        rand_url = f"https://{uuid.uuid4().hex}.com/api"
        rand_token = uuid.uuid4().hex
        rand_chat = str(random.randint(100000, 999999))
        rand_price = round(random.uniform(100.0, 1000.0), 2)
        rand_report = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_portfolio_analytics.MarketParser') as mock_parser_cls, \
             patch('skills.market_portfolio_analytics.MarketReportGenerator') as mock_gen_cls, \
             patch('skills.market_portfolio_analytics.run_market_telegram_pipeline') as mock_pipeline:

            parser_instance = mock_parser_cls.return_value
            parser_instance.fetch_price.return_value = rand_price

            gen_instance = mock_gen_cls.return_value
            gen_instance.generate_symbol_report.return_value = rand_report

            result = start_new(
                storage_file=rand_storage,
                symbol=rand_symbol,
                url=rand_url,
                telegram_token=rand_token,
                chat_id=rand_chat
            )

            self.assertEqual(result, rand_report)
            parser_instance.fetch_price.assert_called_once_with(rand_url)
            parser_instance.fetch_and_store.assert_called_once_with(rand_symbol, rand_price)
            gen_instance.generate_symbol_report.assert_called_once_with(rand_symbol)
            gen_instance.get_raw_stream_dump.assert_called_once()
            mock_pipeline.assert_called_once_with(
                symbol=rand_symbol,
                price=rand_price,
                chat_id=rand_chat,
                token=rand_token
            )

    def test_start_new_unicode_decode_error_resilience(self):
        rand_storage = f"{uuid.uuid4().hex}.json"
        rand_symbol = f"TOKEN_{uuid.uuid4().hex[:4]}"

        with patch('skills.market_portfolio_analytics.MarketParser') as mock_parser_cls, \
             patch('skills.market_portfolio_analytics.MarketReportGenerator') as mock_gen_cls, \
             patch('skills.market_portfolio_analytics.run_market_telegram_pipeline'):

            parser_instance = mock_parser_cls.return_value
            parser_instance.fetch_price.return_value = None

            gen_instance = mock_gen_cls.return_value
            gen_instance.generate_symbol_report.side_effect = UnicodeDecodeError('utf-8', b'\x89', 0, 1, "invalid start byte")

            with self.assertRaises(UnicodeDecodeError):
                start_new(storage_file=rand_storage, symbol=rand_symbol)

if __name__ == '__main__':
    unittest.main()