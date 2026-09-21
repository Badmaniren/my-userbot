import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.market_portfolio_digest import (
    send_telegram_notification,
    generate_portfolio_digest,
    generate_extended_digest,
    PortfolioDigestManager
)


class TestMarketPortfolioDigest(unittest.TestCase):

    def setUp(self):
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.url = f"https://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        self.token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"{uuid.uuid4().hex}.db"

    def test_send_telegram_notification_stub(self):
        result = send_telegram_notification()
        self.assertTrue(result)

    @patch('skills.market_portfolio_digest.PortfolioValuation')
    @patch('skills.market_portfolio_digest.PortfolioVisualizer')
    @patch('skills.market_portfolio_digest.dispatch_portfolio_alerts')
    def test_generate_portfolio_digest(self, mock_dispatch, mock_visualizer_cls, mock_valuation_cls):
        expected_valuation = {uuid.uuid4().hex: random.randint(100, 1000)}
        expected_report = uuid.uuid4().hex

        mock_valuation_instance = mock_valuation_cls.return_value
        mock_valuation_instance.evaluate_portfolio.return_value = expected_valuation

        mock_visualizer_instance = mock_visualizer_cls.return_value
        mock_visualizer_instance.build_text_report.return_value = expected_report

        result = generate_portfolio_digest(
            self.symbol,
            self.url,
            self.token,
            self.chat_id,
            self.storage_file
        )

        mock_valuation_cls.assert_called_once_with(self.storage_file)
        mock_valuation_instance.load_data.assert_called_once_with(self.storage_file)
        mock_valuation_instance.evaluate_portfolio.assert_called_once_with(self.url)

        mock_visualizer_cls.assert_called_once_with(self.storage_file)
        mock_visualizer_instance.build_text_report.assert_called_once_with(self.symbol)

        mock_dispatch.assert_called_once_with(
            self.symbol,
            self.url,
            self.token,
            self.chat_id,
            self.storage_file
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], self.symbol)
        self.assertEqual(result["valuation"], expected_valuation)
        self.assertEqual(result["report"], expected_report)

    @patch('skills.market_portfolio_digest.PortfolioValuation')
    @patch('skills.market_portfolio_digest.PortfolioVisualizer')
    def test_generate_extended_digest(self, mock_visualizer_cls, mock_valuation_cls):
        mock_valuation_instance = mock_valuation_cls.return_value
        mock_visualizer_instance = mock_visualizer_cls.return_value

        result = generate_extended_digest(
            self.storage_file,
            self.symbol,
            self.url,
            self.token,
            self.chat_id
        )

        mock_valuation_cls.assert_called_once_with(self.storage_file)
        mock_valuation_instance.get_total_summary.assert_called_once_with(self.url)

        mock_visualizer_cls.assert_called_once_with(self.storage_file)
        mock_visualizer_instance.build_text_report.assert_called_once_with(self.symbol)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbol"], self.symbol)

    @patch('skills.market_portfolio_digest.PortfolioValuation')
    @patch('skills.market_portfolio_digest.PortfolioVisualizer')
    def test_portfolio_digest_manager_compile_digest(self, mock_visualizer_cls, mock_valuation_cls):
        expected_summary = {uuid.uuid4().hex: float(random.randint(1, 100))}
        expected_chart = uuid.uuid4().hex

        mock_valuation_instance = mock_valuation_cls.return_value
        mock_valuation_instance.calculate_portfolio_pnl.return_value = expected_summary

        mock_visualizer_instance = mock_visualizer_cls.return_value
        mock_visualizer_instance.generate_ascii_chart.return_value = expected_chart

        manager = PortfolioDigestManager(self.storage_file)
        result = manager.compile_digest(self.symbol, self.url)

        mock_valuation_cls.assert_called_once_with(self.storage_file)
        mock_valuation_instance.calculate_portfolio_pnl.assert_called_once_with(self.url)

        mock_visualizer_cls.assert_called_once_with(self.storage_file)
        mock_visualizer_instance.generate_ascii_chart.assert_called_once_with(self.symbol)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["symbol"], self.symbol)
        self.assertEqual(result["summary"], expected_summary)
        self.assertEqual(result["ascii_chart"], expected_chart)

    @patch('skills.market_portfolio_digest.PortfolioVisualizer')
    def test_portfolio_digest_manager_render_and_send(self, mock_visualizer_cls):
        mock_visualizer_instance = mock_visualizer_cls.return_value

        manager = PortfolioDigestManager(self.storage_file)
        result = manager.render_and_send(self.symbol, self.token, self.chat_id)

        mock_visualizer_cls.assert_called_once_with(self.storage_file)
        mock_visualizer_instance.render_and_dispatch.assert_called_once_with(
            self.symbol,
            self.token,
            self.chat_id
        )
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()