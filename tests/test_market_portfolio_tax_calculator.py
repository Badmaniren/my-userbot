import unittest
from unittest.mock import MagicMock, patch
import random
import uuid
import io

from skills.market_portfolio_tax_calculator import (
    MarketPortfolioTaxCalculator,
    calculate_portfolio_taxes
)


class TestMarketPortfolioTaxCalculator(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.market_parser = MagicMock()
        self.calculator = MarketPortfolioTaxCalculator(
            db_storage=self.db_storage,
            market_parser=self.market_parser
        )

    def test_calculate_tax_success(self):
        portfolio_id = str(uuid.uuid4())
        sell_price = round(random.uniform(200.0, 500.0), 2)
        purchase_price = round(random.uniform(50.0, 150.0), 2)
        shares = random.randint(1, 50)

        self.db_storage.get_portfolio.return_value = {
            "sell_price": sell_price,
            "purchase_price": purchase_price,
            "shares": shares
        }

        expected_profit = (sell_price - purchase_price) * shares
        expected_tax = round(expected_profit * 0.13, 2)

        tax = self.calculator.calculate_tax(portfolio_id)
        self.assertEqual(tax, expected_tax)
        self.db_storage.get_portfolio.assert_called_once_with(portfolio_id)

    def test_calculate_tax_portfolio_not_found(self):
        portfolio_id = str(uuid.uuid4())
        self.db_storage.get_portfolio.return_value = None

        tax = self.calculator.calculate_tax(portfolio_id)
        self.assertEqual(tax, 0.0)
        self.db_storage.get_portfolio.assert_called_once_with(portfolio_id)

    def test_process_dividend_stream_success(self):
        stream_id = str(uuid.uuid4())
        stream_data = io.BytesIO(uuid.uuid4().bytes)

        self.market_parser.parse_stream.return_value = {"stream_id": stream_id}

        result = self.calculator.process_dividend_stream(stream_data)
        self.assertEqual(result, stream_id)
        self.market_parser.parse_stream.assert_called_once_with(stream_data)

    def test_process_dividend_stream_invalid_parser_output(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        self.market_parser.parse_stream.return_value = random.choice([
            str(uuid.uuid4()),
            random.randint(1, 100),
            {"invalid_key": str(uuid.uuid4())},
            None
        ])

        result = self.calculator.process_dividend_stream(stream_data)
        self.assertIsNone(result)

    def test_process_dividend_stream_no_parser(self):
        calc_without_parser = MarketPortfolioTaxCalculator()
        stream_data = io.BytesIO(uuid.uuid4().bytes)

        result = calc_without_parser.process_dividend_stream(stream_data)
        self.assertIsNone(result)


class TestCalculatePortfolioTaxesFunction(unittest.TestCase):

    def test_calculate_portfolio_taxes_dict_deals(self):
        portfolio_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        price_1 = round(random.uniform(150.0, 300.0), 2)
        shares_1 = random.randint(1, 10)
        price_2 = round(random.uniform(150.0, 300.0), 2)
        shares_2 = random.randint(1, 10)

        deals = [
            {"type": "SELL", "price": price_1, "shares": shares_1},
            {"type": "BUY", "price": 50.0, "shares": 100},
            {"type": "SELL", "price": price_2, "shares": shares_2}
        ]
        dividends = round(random.uniform(10.0, 500.0), 2)

        profit_1 = (price_1 - 100.0) * shares_1
        profit_2 = (price_2 - 100.0) * shares_2
        total_profit = profit_1 + profit_2

        expected_tax = round(max(0.0, total_profit * 0.13 + dividends * 0.13), 2)

        result = calculate_portfolio_taxes(portfolio_id, user_id, deals, 365, dividends)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["user_id"], user_id)
        self.assertEqual(result["total_tax_due"], expected_tax)

    def test_calculate_portfolio_taxes_object_deals(self):
        portfolio_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        class DealMock:
            def __init__(self, dtype, price, shares):
                self.type = dtype
                self.price = price
                self.shares = shares

        price = round(random.uniform(200.0, 400.0), 2)
        shares = random.randint(5, 15)

        deals = [
            DealMock("SELL", price, shares),
            DealMock("HOLD", 120.0, 10)
        ]
        dividends = round(random.uniform(0.0, 100.0), 2)

        total_profit = (price - 100.0) * shares
        expected_tax = round(max(0.0, total_profit * 0.13 + dividends * 0.13), 2)

        result = calculate_portfolio_taxes(portfolio_id, user_id, deals, 180, dividends)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["user_id"], user_id)
        self.assertEqual(result["total_tax_due"], expected_tax)

    def test_calculate_portfolio_taxes_negative_profit_clamping(self):
        portfolio_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())

        deals = [
            {"type": "SELL", "price": 10.0, "shares": 1000}
        ]
        dividends = 0.0

        result = calculate_portfolio_taxes(portfolio_id, user_id, deals, 30, dividends)

        self.assertEqual(result["total_tax_due"], 0.0)