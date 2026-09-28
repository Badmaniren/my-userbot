import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.market_portfolio_tax_calculator import (
    MarketPortfolioTaxCalculator,
    calculate_portfolio_taxes,
    market_portfolio_tax_calculator
)


class TestMarketPortfolioTaxCalculator(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.market_parser = MagicMock()
        self.calculator = MarketPortfolioTaxCalculator(
            db_storage=self.db_storage,
            market_parser=self.market_parser
        )

    def test_init_sets_attributes(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        calc = MarketPortfolioTaxCalculator(**{rand_key: rand_val})
        self.assertEqual(getattr(calc, rand_key), rand_val)

    def test_calculate_tax_no_db_storage(self):
        calc_no_db = MarketPortfolioTaxCalculator()
        portfolio_id = uuid.uuid4().hex
        result = calc_no_db.calculate_tax(portfolio_id)
        self.assertEqual(result, 0.0)

    def test_calculate_tax_portfolio_found(self):
        portfolio_id = uuid.uuid4().hex
        sell_price = round(random.uniform(150.0, 500.0), 2)
        purchase_price = round(random.uniform(50.0, 140.0), 2)
        shares = random.randint(1, 100)

        self.db_storage.get_portfolio.return_value = {
            "sell_price": sell_price,
            "purchase_price": purchase_price,
            "shares": shares
        }

        expected_profit = (sell_price - purchase_price) * shares
        expected_tax = round(expected_profit * 0.13, 2)

        result = self.calculator.calculate_tax(portfolio_id)
        self.assertEqual(result, expected_tax)
        self.db_storage.get_portfolio.assert_called_once_with(portfolio_id)

    def test_calculate_tax_portfolio_not_found(self):
        portfolio_id = uuid.uuid4().hex
        self.db_storage.get_portfolio.return_value = None
        result = self.calculator.calculate_tax(portfolio_id)
        self.assertEqual(result, 0.0)

    def test_process_dividend_stream_success(self):
        stream_id = uuid.uuid4().hex
        stream = io.BytesIO(uuid.uuid4().bytes)
        self.market_parser.parse_stream.return_value = {"stream_id": stream_id}

        result = self.calculator.process_dividend_stream(stream)
        self.assertEqual(result, stream_id)
        self.market_parser.parse_stream.assert_called_once_with(stream)

    def test_process_dividend_stream_invalid_parser_output(self):
        stream = io.BytesIO(uuid.uuid4().bytes)
        self.market_parser.parse_stream.return_value = uuid.uuid4().hex

        result = self.calculator.process_dividend_stream(stream)
        self.assertIsNone(result)

    def test_process_dividend_stream_no_parser(self):
        calc_no_parser = MarketPortfolioTaxCalculator()
        stream = io.BytesIO(uuid.uuid4().bytes)
        result = calc_no_parser.process_dividend_stream(stream)
        self.assertIsNone(result)

    def test_calculate_portfolio_taxes_function(self):
        portfolio_id = uuid.uuid4().hex
        user_id = uuid.uuid4().hex
        dividends = round(random.uniform(10.0, 1000.0), 2)
        
        price1 = round(random.uniform(110.0, 200.0), 2)
        shares1 = random.randint(1, 10)
        
        deal_dict = {"type": "SELL", "price": price1, "shares": shares1}
        
        class DealObj:
            def __init__(self, t, p, s):
                self.type = t
                self.price = p
                self.shares = s
                
        price2 = round(random.uniform(110.0, 200.0), 2)
        shares2 = random.randint(1, 10)
        deal_obj = DealObj("SELL", price2, shares2)
        
        deals = [deal_dict, deal_obj, {"type": "BUY", "price": price1, "shares": shares1}]

        profit1 = (price1 - 100.0) * shares1
        profit2 = (price2 - 100.0) * shares2
        total_profit = profit1 + profit2
        expected_tax = round(max(0.0, total_profit * 0.13 + dividends * 0.13), 2)

        res = calculate_portfolio_taxes(portfolio_id, user_id, deals, random.randint(1, 365), dividends)

        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["user_id"], user_id)
        self.assertEqual(res["total_tax_due"], expected_tax)

    def test_market_portfolio_tax_calculator_dict_payload(self):
        payload = {
            "portfolio_id": "TEST-PF-100",
            "assets": [
                {"ticker": "ABC", "weight": 0.5, "historical_returns": [-0.02, 0.01, 0.03]},
                {"ticker": "XYZ", "weight": 0.5, "historical_returns": [-0.04, 0.02, 0.01]}
            ],
            "confidence_level": 0.95,
            "tax_rate": 0.20,
            "realized_gains": 10000.0
        }
        res = market_portfolio_tax_calculator(payload)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["portfolio_id"], "TEST-PF-100")
        self.assertIn("var", res)
        self.assertIn("cvar", res)
        self.assertEqual(res["tax_liability"], 2000.0)

    def test_market_portfolio_tax_calculator_str_payload(self):
        res = market_portfolio_tax_calculator("NON_EXISTENT_ID")
        self.assertEqual(res, 0.0)


if __name__ == '__main__':
    unittest.main()
