import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.market_portfolio_tax_calculator import (
    MarketPortfolioTaxCalculator,
    calculate_portfolio_taxes,
)


class TestMarketPortfolioTaxCalculator(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_parser = MagicMock()
        self.calc_kwargs = {
            "db_storage": self.mock_db,
            "market_parser": self.mock_parser,
            str(uuid.uuid4().hex): random.randint(1, 100)
        }
        self.calculator = MarketPortfolioTaxCalculator(**self.calc_kwargs)

    def test_init_sets_attributes(self):
        for k, v in self.calc_kwargs.items():
            self.assertEqual(getattr(self.calculator, k), v)

    def test_calculate_tax_no_db(self):
        calc_no_db = MarketPortfolioTaxCalculator(db_storage=None)
        portfolio_id = str(uuid.uuid4().hex)
        res = calc_no_db.calculate_tax(portfolio_id)
        self.assertEqual(res, 0.0)

    def test_calculate_tax_portfolio_found(self):
        portfolio_id = str(uuid.uuid4().hex)
        purchase_price = float(random.randint(10, 50))
        sell_price = float(random.randint(60, 100))
        shares = random.randint(1, 10)

        self.mock_db.get_portfolio.return_value = {
            "purchase_price": purchase_price,
            "sell_price": sell_price,
            "shares": shares
        }

        expected_profit = (sell_price - purchase_price) * shares
        expected_tax = round(expected_profit * 0.13, 2)

        res = self.calculator.calculate_tax(portfolio_id)
        self.assertEqual(res, expected_tax)
        self.mock_db.get_portfolio.assert_called_once_with(portfolio_id)

    def test_calculate_tax_portfolio_not_found(self):
        portfolio_id = str(uuid.uuid4().hex)
        self.mock_db.get_portfolio.return_value = None
        res = self.calculator.calculate_tax(portfolio_id)
        self.assertEqual(res, 0.0)

    def test_process_dividend_stream_success(self):
        stream_id = str(uuid.uuid4().hex)
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        self.mock_parser.parse_stream.return_value = {"stream_id": stream_id}

        res = self.calculator.process_dividend_stream(stream_data)
        self.assertEqual(res, stream_id)
        self.mock_parser.parse_stream.assert_called_once_with(stream_data)

    def test_process_dividend_stream_invalid_parser(self):
        calc_bad_parser = MarketPortfolioTaxCalculator()
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        res = calc_bad_parser.process_dividend_stream(stream_data)
        self.assertIsNone(res)

    def test_calculate_portfolio_taxes_dicts_and_objects(self):
        portfolio_id = str(uuid.uuid4().hex)
        user_id = str(uuid.uuid4().hex)
        dividends = float(random.randint(0, 500))

        class DealObj:
            def __init__(self, d_type, price, shares):
                self.type = d_type
                self.price = price
                self.shares = shares

        price1 = float(random.randint(150, 200))
        shares1 = random.randint(1, 5)
        deal_dict = {
            "type": "SELL",
            "price": price1,
            "shares": shares1
        }

        price2 = float(random.randint(200, 250))
        shares2 = random.randint(1, 5)
        deal_obj = DealObj("SELL", price2, shares2)

        deal_ignored = {
            "type": "BUY",
            "price": float(random.randint(50, 90)),
            "shares": random.randint(1, 5)
        }

        deals = [deal_dict, deal_obj, deal_ignored, None, {"type": "SELL", "price": None, "shares": None}]

        profit1 = (price1 - 100.0) * shares1
        profit2 = (price2 - 100.0) * shares2
        total_profit = profit1 + profit2

        expected_tax = round(max(0.0, total_profit * 0.13 + dividends * 0.13), 2)

        res = calculate_portfolio_taxes(portfolio_id, user_id, deals, random.randint(1, 365), dividends)

        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["user_id"], user_id)
        self.assertEqual(res["total_tax_due"], expected_tax)