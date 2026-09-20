import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_digest import (
    generate_portfolio_digest,
    PortfolioDigestManager
)


class TestMarketPortfolioDigest(unittest.TestCase):

    def setUp(self):
        self.rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.rand_url = f"https://{uuid.uuid4().hex}.com/api"
        self.rand_token = uuid.uuid4().hex
        self.rand_chat_id = str(random.randint(100000, 999999))
        self.rand_storage = f"{uuid.uuid4().hex}.json"
        
        self.mock_valuation_data = {
            "total_value": round(random.uniform(1000.0, 50000.0), 2),
            "pnl": round(random.uniform(-500.0, 1500.0), 2)
        }
        self.mock_chart_data = f"CHART-{uuid.uuid4().hex[:8]}"

    def test_digest_composition_and_execution(self):
        with patch('skills.market_portfolio_digest.PortfolioValuation') as mock_valuation_cls, \
             patch('skills.market_portfolio_digest.PortfolioVisualizer') as mock_visualizer_cls, \
             patch('skills.market_portfolio_digest.dispatch_portfolio_alerts') as mock_dispatch:

            mock_val_instance = mock_valuation_cls.return_value
            mock_val_instance.evaluate_portfolio.return_value = self.mock_valuation_data

            mock_vis_instance = mock_visualizer_cls.return_value
            mock_vis_instance.build_text_report.return_value = self.mock_chart_data

            result = generate_portfolio_digest(
                symbol=self.rand_symbol,
                url=self.rand_url,
                telegram_token=self.rand_token,
                chat_id=self.rand_chat_id,
                storage_file=self.rand_storage
            )

            mock_valuation_cls.assert_called_once_with(self.rand_storage)
            mock_val_instance.evaluate_portfolio.assert_called_once_with(self.rand_url)

            mock_visualizer_cls.assert_called_once_with(self.rand_storage)
            mock_vis_instance.build_text_report.assert_called_once_with(self.rand_symbol)

            mock_dispatch.assert_called_once()
            
            self.assertIn(self.rand_symbol, result.get("symbol", ""))
            self.assertEqual(result["valuation"], self.mock_valuation_data)
            self.assertEqual(result["report"], self.mock_chart_data)

    def test_portfolio_digest_manager_class(self):
        with patch('skills.market_portfolio_digest.PortfolioValuation') as mock_valuation_cls, \
             patch('skills.market_portfolio_digest.PortfolioVisualizer') as mock_visualizer_cls, \
             patch('skills.market_portfolio_digest.send_telegram_notification') as mock_send_tg:

            manager = PortfolioDigestManager(storage_file=self.rand_storage)
            self.assertEqual(manager.storage_file, self.rand_storage)

            mock_val_instance = mock_valuation_cls.return_value
            mock_val_instance.calculate_portfolio_pnl.return_value = self.mock_valuation_data

            mock_vis_instance = mock_visualizer_cls.return_value
            mock_vis_instance.generate_ascii_chart.return_value = self.mock_chart_data

            digest = manager.compile_digest(self.rand_symbol, self.rand_url)

            self.assertEqual(digest["symbol"], self.rand_symbol)
            self.assertEqual(digest["summary"], self.mock_valuation_data)
            self.assertEqual(digest["ascii_chart"], self.mock_chart_data)

            dispatch_res = manager.render_and_send(
                symbol=self.rand_symbol,
                token=self.rand_token,
                chat_id=self.rand_chat_id
            )

            mock_vis_instance.render_and_dispatch.assert_called_once_with(
                self.rand_symbol, self.rand_token, self.rand_chat_id
            )
            self.assertTrue(dispatch_res)

    def test_digest_with_io_stream_mocking(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        
        with patch('skills.market_portfolio_digest.PortfolioValuation') as mock_valuation_cls, \
             patch('skills.market_portfolio_digest.PortfolioVisualizer') as mock_visualizer_cls:

            mock_val_instance = mock_valuation_cls.return_value
            mock_val_instance.load_data.return_value = stream_data.read()

            digest_res = generate_portfolio_digest(
                symbol=self.rand_symbol,
                url=self.rand_url,
                telegram_token=self.rand_token,
                chat_id=self.rand_chat_id,
                storage_file=self.rand_storage
            )

            self.assertIsNotNone(digest_res)
            mock_val_instance.load_data.assert_called_once_with(self.rand_storage)


if __name__ == '__main__':
    unittest.main()