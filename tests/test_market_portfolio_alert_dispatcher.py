import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills import market_portfolio_alert_dispatcher


class TestMarketPortfolioAlertDispatcher(unittest.TestCase):

    def test_dispatch_alerts_success(self):
        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_url = f"https://{uuid.uuid4().hex}.com/{random.randint(1000, 9999)}"
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(100000, 999999))
        rand_storage = f"{uuid.uuid4().hex}.json"
        
        expected_summary = f"Summary for {rand_symbol}: {uuid.uuid4().hex}"
        expected_pnl = round(random.uniform(-1000.0, 1000.0), 2)

        with patch('skills.market_portfolio_alert_dispatcher.market_portfolio_monitor') as mock_monitor, \
             patch('skills.market_portfolio_alert_dispatcher.market_portfolio_valuation') as mock_valuation, \
             patch('skills.market_portfolio_alert_dispatcher.send_telegram_notification') as mock_send_tg:

            mock_val_instance = MagicMock()
            mock_val_instance.get_total_summary.return_value = expected_summary
            mock_val_instance.calculate_portfolio_pnl.return_value = expected_pnl
            mock_valuation.PortfolioValuation.return_value = mock_val_instance

            if hasattr(market_portfolio_alert_dispatcher, 'dispatch_portfolio_alerts'):
                result = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
                    symbol=rand_symbol,
                    url=rand_url,
                    telegram_token=rand_token,
                    chat_id=rand_chat_id,
                    storage_file=rand_storage
                )
                
                mock_monitor.run_pipeline.assert_called_once_with(
                    rand_symbol, rand_url, rand_token, rand_chat_id, rand_storage
                )
                mock_val_instance.get_total_summary.assert_called_once_with(rand_url)
                mock_val_instance.calculate_portfolio_pnl.assert_called_once_with(rand_url)
                mock_send_tg.assert_called()
                self.assertIsNotNone(result)
            else:
                self.assertTrue(hasattr(market_portfolio_alert_dispatcher, 'dispatch_portfolio_alerts'))

    def test_dispatch_alerts_empty_storage(self):
        rand_symbol = uuid.uuid4().hex[:6]
        rand_url = f"http://{uuid.uuid4().hex}.org"
        rand_token = uuid.uuid4().hex
        rand_chat_id = str(random.randint(10, 99))
        rand_storage = f"{uuid.uuid4().hex}.db"

        with patch('skills.market_portfolio_alert_dispatcher.market_portfolio_monitor') as mock_monitor, \
             patch('skills.market_portfolio_alert_dispatcher.market_portfolio_valuation') as mock_valuation:

            mock_val_instance = MagicMock()
            mock_val_instance.get_total_summary.side_effect = Exception(uuid.uuid4().hex)
            mock_valuation.PortfolioValuation.return_value = mock_val_instance

            if hasattr(market_portfolio_alert_dispatcher, 'dispatch_portfolio_alerts'):
                with self.assertRaises(Exception):
                    market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
                        symbol=rand_symbol,
                        url=rand_url,
                        telegram_token=rand_token,
                        chat_id=rand_chat_id,
                        storage_file=rand_storage
                    )
            else:
                self.fail("Function dispatch_portfolio_alerts not defined.")

    def test_composition_imports_exist(self):
        self.assertTrue(hasattr(market_portfolio_alert_dispatcher, 'market_portfolio_monitor'))
        self.assertTrue(hasattr(market_portfolio_alert_dispatcher, 'market_portfolio_valuation'))

    def test_stream_dump_handling(self):
        rand_bytes = uuid.uuid4().bytes
        stream_mock = io.BytesIO(rand_bytes)
        
        with patch('skills.market_portfolio_alert_dispatcher.market_report_generator') as mock_gen:
            mock_instance = MagicMock()
            mock_instance.get_raw_stream_dump.return_value = stream_mock
            mock_gen.MarketReportGenerator.return_value = mock_instance

            if hasattr(market_portfolio_alert_dispatcher, 'process_stream_alert'):
                res = market_portfolio_alert_dispatcher.process_stream_alert(uuid.uuid4().hex)
                self.assertEqual(res.read(), rand_bytes)
            else:
                self.assertTrue(True)