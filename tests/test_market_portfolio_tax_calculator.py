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
        self.portfolio_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        self.purchase_price = round(random.uniform(10.0, 90.0), 2)
        self.sell_price = round(random.uniform(100.0, 500.0), 2)
        self.shares = random.randint(1, 1000)
        self.dividends = round(random.uniform(0.0, 5000.0), 2)
        self.holding_period = random.randint(10, 2000)

    def test_market_portfolio_tax_calculator_init(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        calc = MarketPortfolioTaxCalculator(**{rand_key: rand_val})
        self.assertEqual(getattr(calc, rand_key), rand_val)

    def test_calculate_tax_success(self):
        mock_db = MagicMock()
        portfolio_data = {
            "purchase_price": self.purchase_price,
            "sell_price": self.sell_price,
            "shares": self.shares
        }
        mock_db.get_portfolio.return_value = portfolio_data
        
        calc = MarketPortfolioTaxCalculator(db_storage=mock_db)
        tax = calc.calculate_tax(self.portfolio_id)
        
        expected_profit = (self.sell_price - self.purchase_price) * self.shares
        expected_tax = round(expected_profit * 0.13, 2)
        
        self.assertEqual(tax, expected_tax)
        mock_db.get_portfolio.assert_called_once_with(self.portfolio_id)

    def test_calculate_tax_not_found(self):
        mock_db = MagicMock()
        mock_db.get_portfolio.return_value = None
        
        calc = MarketPortfolioTaxCalculator(db_storage=mock_db)
        tax = calc.calculate_tax(self.portfolio_id)
        
        self.assertEqual(tax, 0.0)

    def test_process_dividend_stream(self):
        stream_id_val = uuid.uuid4().hex
        mock_parser = MagicMock()
        mock_parser.parse_stream.return_value = {"stream_id": stream_id_val}
        
        calc = MarketPortfolioTaxCalculator(market_parser=mock_parser)
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        
        res = calc.process_dividend_stream(stream_data)
        self.assertEqual(res, stream_id_val)
        mock_parser.parse_stream.assert_called_once_with(stream_data)

    def test_process_dividend_stream_invalid_parser(self):
        calc = MarketPortfolioTaxCalculator()
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        res = calc.process_dividend_stream(stream_data)
        self.assertIsNone(res)

    def test_calculate_portfolio_taxes_function(self):
        deal_price = round(random.uniform(150.0, 1000.0), 2)
        deal_shares = random.randint(1, 50)
        
        deal_dict = {
            "type": "SELL",
            "price": deal_price,
            "shares": deal_shares
        }
        
        class DealObj:
            def __init__(self, t, p, s):
                self.type = t
                self.price = p
                self.shares = s
                
        deal_object = DealObj("SELL", deal_price, deal_shares)
        deals = [deal_dict, deal_object, {"type": "BUY", "price": 50.0, "shares": 10}]
        
        res = calculate_portfolio_taxes(
            portfolio_id=self.portfolio_id,
            user_id=self.user_id,
            deals=deals,
            holding_period=self.holding_period,
            dividends=self.dividends
        )
        
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["user_id"], self.user_id)
        
        profit_per_deal = (deal_price - 100.0) * deal_shares
        total_profit = profit_per_deal * 2
        expected_tax = round(max(0.0, total_profit * 0.13 + self.dividends * 0.13), 2)
        
        self.assertEqual(res["total_tax_due"], expected_tax)

    def test_calculate_portfolio_taxes_negative_profit(self):
        deal_dict = {
            "type": "SELL",
            "price": 50.0,
            "shares": 10
        }
        deals = [deal_dict]
        res = calculate_portfolio_taxes(
            portfolio_id=self.portfolio_id,
            user_id=self.user_id,
            deals=deals,
            holding_period=self.holding_period,
            dividends=0.0
        )
        self.assertEqual(res["total_tax_due"], 0.0)


if __name__ == "__main__":
    unittest.main()