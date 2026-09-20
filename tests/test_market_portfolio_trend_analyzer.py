import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_trend_analyzer import (
    analyze_portfolio_trends,
    PortfolioTrendAnalyzer
)

class TestMarketPortfoliotrendAnalyzer(unittest.TestCase):

    def setUp(self):
        self.rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.rand_url = f"https://{uuid.uuid4().hex}.com/market"
        self.rand_storage = f"{uuid.uuid4().hex}.json"
        self.rand_pnl = round(random.uniform(-5000.0, 5000.0), 2)
        self.rand_valuation = round(random.uniform(100.0, 50000.0), 2)

    @patch('skills.market_portfolio_trend_analyzer.market_portfolio_monitor')
    @patch('skills.market_portfolio_trend_analyzer.market_portfolio_valuation')
    def test_portfolio_trend_analyzer_class(self, mock_valuation_module, mock_monitor_module):
        mock_monitor_instance = mock_monitor_module.MarketReportGenerator.return_value
        mock_monitor_instance.generate_symbol_report.return_value = {
            "symbol": self.rand_symbol,
            "trend_marker": uuid.uuid4().hex
        }

        mock_val_instance = mock_valuation_module.PortfolioValuation.return_value
        mock_val_instance.calculate_portfolio_pnl.return_value = self.rand_pnl
        mock_val_instance.get_total_summary.return_value = {
            "total_valuation": self.rand_valuation
        }

        analyzer = PortfolioTrendAnalyzer(self.rand_storage)
        result = analyzer.analyze_trends(self.rand_symbol, self.rand_url)

        self.assertIn("symbol", result)
        self.assertEqual(result["symbol"], self.rand_symbol)
        self.assertEqual(result["pnl"], self.rand_pnl)
        self.assertEqual(result["valuation"], self.rand_valuation)

        mock_monitor_module.MarketReportGenerator.assert_called_once_with(self.rand_storage)
        mock_valuation_module.PortfolioValuation.assert_called_once_with(self.rand_storage)
        mock_monitor_instance.generate_symbol_report.assert_called_once_with(self.rand_symbol)
        mock_val_instance.calculate_portfolio_pnl.assert_called_once_with(self.rand_url)

    @patch('skills.market_portfolio_trend_analyzer.market_portfolio_monitor')
    @patch('skills.market_portfolio_trend_analyzer.market_portfolio_valuation')
    def test_analyze_portfolio_trends_function(self, mock_valuation_module, mock_monitor_module):
        mock_monitor_instance = mock_monitor_module.MarketReportGenerator.return_value
        mock_monitor_report = {
            "history": [uuid.uuid4().hex, uuid.uuid4().hex]
        }
        mock_monitor_instance.get_raw_stream_dump.return_value = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        mock_monitor_instance.generate_symbol_report.return_value = mock_monitor_report

        mock_val_instance = mock_valuation_module.PortfolioValuation.return_value
        mock_val_instance.evaluate_portfolio.return_value = {
            "status": uuid.uuid4().hex
        }

        trends = analyze_portfolio_trends(self.rand_storage, self.rand_symbol, self.rand_url)

        self.assertIsInstance(trends, dict)
        self.assertIn("report", trends)
        self.assertEqual(trends["report"], mock_monitor_report)
        mock_val_instance.evaluate_portfolio.assert_called_once_with(self.rand_url)

    @patch('skills.market_portfolio_trend_analyzer.market_portfolio_monitor')
    @patch('skills.market_portfolio_trend_analyzer.market_portfolio_valuation')
    def test_trend_analyzer_error_handling(self, mock_valuation_module, mock_monitor_module):
        mock_monitor_module.MarketReportGenerator.side_effect = Exception(uuid.uuid4().hex)

        analyzer = PortfolioTrendAnalyzer(self.rand_storage)
        with self.assertRaises(Exception):
            analyzer.analyze_trends(self.rand_symbol, self.rand_url)

if __name__ == '__main__':
    unittest.main()