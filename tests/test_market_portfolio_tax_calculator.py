import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.market_portfolio_tax_calculator import (
    MarketPortfolioTaxCalculator,
    calculate_portfolio_taxes
)


class TestMarketPortfolioTaxCalculator(unittest.TestCase):

    def setUp(self):
        self.random_storage_attr = uuid.uuid4().hex
        self.calculator = MarketPortfolioTaxCalculator(db_storage=None)

    def test_calculate_tax_without_storage(self):
        rand_id = uuid.uuid4().hex
        tax = self.calculator.calculate_tax(rand_id)
        self.assertEqual(tax, 0.0)

    def test_calculate_tax_with_storage_missing_portfolio(self):
        rand_id = uuid.uuid4().hex
        mock_db = MagicMock()
        mock_db.get_portfolio.return_value = None
        
        calc = MarketPortfolioTaxCalculator(db_storage=mock_db)
        tax = calc.calculate_tax(rand_id)
        
        mock_db.get_portfolio.assert_called_once_with(rand_id)
        self.assertEqual(tax, 0.0)

    def test_calculate_tax_success(self):
        rand_id = uuid.uuid4().hex
        purchase = round(random.uniform(10.0, 50.0), 2)
        sell = round(purchase + random.uniform(5.0, 100.0), 2)
        shares = random.randint(1, 1000)

        portfolio_data = {
            "purchase_price": purchase,
            "sell_price": sell,
            "shares": shares
        }

        mock_db = MagicMock()
        mock_db.get_portfolio.return_value = portfolio_data

        calc = MarketPortfolioTaxCalculator(db_storage=mock_db)
        tax = calc.calculate_tax(rand_id)

        expected_profit = (sell - purchase) * shares
        expected_tax = round(expected_profit * 0.13, 2)

        mock_db.get_portfolio.assert_called_once_with(rand_id)
        self.assertEqual(tax, expected_tax)

    def test_process_dividend_stream_no_parser(self):
        rand_stream = io.BytesIO(uuid.uuid4().bytes)
        calc = MarketPortfolioTaxCalculator()
        result = calc.process_dividend_stream(rand_stream)
        self.assertIsNone(result)

    def test_process_dividend_stream_valid(self):
        rand_stream_id = uuid.uuid4().hex
        rand_stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))

        mock_parser = MagicMock()
        mock_parser.parse_stream.return_value = {"stream_id": rand_stream_id}

        calc = MarketPortfolioTaxCalculator(market_parser=mock_parser)
        result = calc.process_dividend_stream(rand_stream_data)

        mock_parser.parse_stream.assert_called_once_with(rand_stream_data)
        self.assertEqual(result, rand_stream_id)

    def test_process_dividend_stream_invalid_parser_output(self):
        rand_stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        
        mock_parser = MagicMock()
        invalid_outputs = [
            uuid.uuid4().hex,
            random.randint(1, 100),
            {"invalid_key": uuid.uuid4().hex},
            None
        ]
        
        for invalid_out in invalid_outputs:
            mock_parser.parse_stream.return_value = invalid_out
            calc = MarketPortfolioTaxCalculator(market_parser=mock_parser)
            result = calc.process_dividend_stream(rand_stream_data)
            self.assertIsNone(result)


class TestCalculatePortfolioTaxesFunction(unittest.TestCase):

    def test_calculate_portfolio_taxes_empty_deals(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_user_id = uuid.uuid4().hex
        dividends = round(random.uniform(0.0, 5000.0), 2)

        result = calculate_portfolio_taxes(
            portfolio_id=rand_portfolio_id,
            user_id=rand_user_id,
            deals=[],
            holding_period=random.randint(1, 365),
            dividends=dividends
        )

        expected_tax = round(max(0.0, 0.0 + dividends * 0.13), 2)

        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertEqual(result["user_id"], rand_user_id)
        self.assertEqual(result["total_tax_due"], expected_tax)

    def test_calculate_portfolio_taxes_mixed_deals(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_user_id = uuid.uuid4().hex
        dividends = round(random.uniform(10.0, 1000.0), 2)

        sell_price_dict = round(random.uniform(120.0, 300.0), 2)
        shares_dict = random.randint(1, 50)
        
        sell_price_obj = round(random.uniform(120.0, 300.0), 2)
        shares_obj = random.randint(1, 50)

        deal_dict = {
            "type": "SELL",
            "price": sell_price_dict,
            "shares": shares_dict
        }

        class DealObject:
            def __init__(self, t, p, s):
                self.type = t
                self.price = p
                self.shares = s

        deal_obj = DealObject("SELL", sell_price_obj, shares_obj)
        deal_buy_ignored = {"type": "BUY", "price": 50.0, "shares": 100}

        deals = [deal_dict, deal_obj, deal_buy_ignored]

        result = calculate_portfolio_taxes(
            portfolio_id=rand_portfolio_id,
            user_id=rand_user_id,
            deals=deals,
            holding_period=random.randint(30, 730),
            dividends=dividends
        )

        profit_1 = (sell_price_dict - 100.0) * shares_dict
        profit_2 = (sell_price_obj - 100.0) * shares_obj
        total_profit = profit_1 + profit_2

        expected_tax = round(max(0.0, total_profit * 0.13 + dividends * 0.13), 2)

        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertEqual(result["user_id"], rand_user_id)
        self.assertAlmostEqual(result["total_tax_due"], expected_tax, places=2)


if __name__ == "__main__":
    unittest.main()