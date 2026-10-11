import unittest
from unittest.mock import patch
import random
import uuid
import string

from skills.market_portfolio_net_dividend_calculator import (
    NetDividendCalculator,
    NetDividendCalculatorException
)

class TestMarketPortfolioNetDividendCalculator(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.asset_ticker = "".join(random.choices(string.ascii_uppercase, k=4))
        self.shares_count = random.randint(10, 1000)
        self.tax_rate = round(random.uniform(0.05, 0.30), 2)
        self.gross_dividend = round(random.uniform(100.0, 5000.0), 2)
        self.net_dividend = round(self.gross_dividend * (1.0 - self.tax_rate), 2)
        self.asset_price = round(random.uniform(10.0, 500.0), 2)

    def test_calculate_net_dividend_yield_success(self):
        with patch('skills.market_portfolio_dividend_tracker.DividendTracker') as mock_dividend_tracker_cls, \
             patch('skills.market_portfolio_tax_calculator.MarketPortfolioTaxCalculator') as mock_tax_calc_cls:

            mock_tracker_instance = mock_dividend_tracker_cls.return_value
            mock_tracker_instance.calculate_projected_dividends.return_value = {
                'gross_dividend': self.gross_dividend,
                'ticker': self.asset_ticker,
                'shares': self.shares_count
            }

            mock_tax_instance = mock_tax_calc_cls.return_value
            mock_tax_instance.calculate_tax.return_value = {
                'tax_amount': round(self.gross_dividend * self.tax_rate, 2),
                'effective_rate': self.tax_rate
            }

            calculator = NetDividendCalculator(
                db_storage=uuid.uuid4().hex,
                dividend_tracker=mock_tracker_instance,
                tax_calculator=mock_tax_instance
            )

            result = calculator.calculate_net_dividend_yield(
                portfolio_id=self.portfolio_id,
                asset_ticker=self.asset_ticker,
                shares_count=self.shares_count,
                asset_price=self.asset_price
            )

            self.assertIn('net_dividend_amount', result)
            self.assertIn('net_dividend_yield', result)
            self.assertEqual(result['ticker'], self.asset_ticker)
            self.assertEqual(result['shares'], self.shares_count)

            expected_net = self.gross_dividend * (1.0 - self.tax_rate)
            self.assertAlmostEqual(result['net_dividend_amount'], expected_net, places=2)

            expected_yield = expected_net / (self.shares_count * self.asset_price)
            self.assertAlmostEqual(result['net_dividend_yield'], expected_yield, places=4)

            mock_tracker_instance.calculate_projected_dividends.assert_called_once()
            mock_tax_instance.calculate_tax.assert_called_once()

    def test_calculate_net_dividend_yield_tracker_exception(self):
        with patch('skills.market_portfolio_dividend_tracker.DividendTracker') as mock_dividend_tracker_cls, \
             patch('skills.market_portfolio_tax_calculator.MarketPortfolioTaxCalculator') as mock_tax_calc_cls:

            from skills.market_portfolio_dividend_tracker import DividendTrackerException
            mock_tracker_instance = mock_dividend_tracker_cls.return_value
            mock_tracker_instance.calculate_projected_dividends.side_effect = DividendTrackerException(uuid.uuid4().hex)

            mock_tax_instance = mock_tax_calc_cls.return_value

            calculator = NetDividendCalculator(
                db_storage=uuid.uuid4().hex,
                dividend_tracker=mock_tracker_instance,
                tax_calculator=mock_tax_instance
            )

            with self.assertRaises(NetDividendCalculatorException):
                calculator.calculate_net_dividend_yield(
                    portfolio_id=self.portfolio_id,
                    asset_ticker=self.asset_ticker,
                    shares_count=self.shares_count,
                    asset_price=self.asset_price
                )

    def test_aggregate_portfolio_net_dividends(self):
        with patch('skills.market_portfolio_dividend_tracker.DividendTracker') as mock_dividend_tracker_cls, \
             patch('skills.market_portfolio_tax_calculator.MarketPortfolioTaxCalculator') as mock_tax_calc_cls:

            mock_tracker_instance = mock_dividend_tracker_cls.return_value
            mock_tracker_instance.aggregate_portfolio_dividends.return_value = [
                {'ticker': self.asset_ticker, 'gross_amount': self.gross_dividend}
            ]

            mock_tax_instance = mock_tax_calc_cls.return_value
            mock_tax_instance.process_dividend_stream.return_value = {
                'total_gross': self.gross_dividend,
                'total_tax': round(self.gross_dividend * self.tax_rate, 2),
                'total_net': self.net_dividend
            }

            calculator = NetDividendCalculator(
                db_storage=uuid.uuid4().hex,
                dividend_tracker=mock_tracker_instance,
                tax_calculator=mock_tax_instance
            )

            portfolio_summary = calculator.aggregate_net_dividends_for_portfolio(self.portfolio_id)

            self.assertIn('portfolio_id', portfolio_summary)
            self.assertEqual(portfolio_summary['portfolio_id'], self.portfolio_id)
            self.assertEqual(portfolio_summary['total_net_dividends'], self.net_dividend)

            mock_tracker_instance.aggregate_portfolio_dividends.assert_called_once_with(self.portfolio_id)
            mock_tax_instance.process_dividend_stream.assert_called_once()

if __name__ == '__main__':
    unittest.main()