import unittest
from unittest.mock import MagicMock
import uuid
import random

from skills.market_portfolio_net_dividend_calculator import (
    NetDividendCalculator,
    NetDividendCalculatorException,
    market_portfolio_net_dividend_calculator
)


class TestMarketPortfolioNetDividendCalculator(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_tracker = MagicMock()
        self.mock_tax = MagicMock()
        self.calc = NetDividendCalculator(
            db_storage=self.mock_db,
            dividend_tracker=self.mock_tracker,
            tax_calculator=self.mock_tax
        )

    def test_init(self):
        self.assertEqual(self.calc.db_storage, self.mock_db)
        self.assertEqual(self.calc.dividend_tracker, self.mock_tracker)
        self.assertEqual(self.calc.tax_calculator, self.mock_tax)

    def test_calculate_net_dividend_yield(self):
        portfolio_id = str(uuid.uuid4())
        ticker = "AAPL"
        shares = 10
        price = 150.0

        self.mock_tracker.calculate_projected_dividends.return_value = {
            'ticker': ticker,
            'shares': shares,
            'gross_dividend': 100.0
        }
        self.mock_tax.calculate_tax.return_value = {'tax_amount': 13.0}

        res = self.calc.calculate_net_dividend_yield(portfolio_id, ticker, shares, asset_price=price)

        self.assertEqual(res['ticker'], ticker)
        self.assertEqual(res['shares'], shares)
        self.assertEqual(res['net_dividend_amount'], 87.0)
        self.assertAlmostEqual(res['net_dividend_yield'], 87.0 / (shares * price))

    def test_process_valid_portfolio_data(self):
        portfolio_data = {
            "portfolio_id": "TEST-123",
            "dividends": [
                {"gross_amount": 100.0, "withholding_tax_rate": 0.10},
                {"gross_amount": 200.0, "withholding_tax_rate": 0.15}
            ]
        }
        res = self.calc.process(portfolio_data)
        self.assertEqual(res["portfolio_id"], "TEST-123")
        self.assertEqual(res["total_gross_dividends"], 300.0)
        self.assertEqual(res["dividend_tax_withheld"], 40.0)
        self.assertEqual(res["total_net_dividends"], 260.0)

    def test_process_invalid_input(self):
        res = self.calc.process(None)
        self.assertEqual(res, {"total_net_dividends": 0.0})


if __name__ == "__main__":
    unittest.main()
