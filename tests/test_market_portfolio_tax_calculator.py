import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import string

from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator, calculate_portfolio_taxes


class TestMarketPortfolioTaxCalculator(unittest.TestCase):

    def setUp(self):
        self.random_kwargs = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            uuid.uuid4().hex: random.randint(1, 1000)
        }
        self.calculator = MarketPortfolioTaxCalculator(**self.random_kwargs)

    def test_init_sets_attributes(self):
        for k, v in self.random_kwargs.items():
            self.assertTrue(hasattr(self.calculator, k))
            self.assertEqual(getattr(self.calculator, k), v)

    def test_calculate_tax_no_db_storage(self):
        calc = MarketPortfolioTaxCalculator()
        portfolio_id = uuid.uuid4().hex
        result = calc.calculate_tax(portfolio_id)
        self.assertEqual(result, 0.0)

    def test_calculate_tax_with_db_storage_found(self):
        mock_db = MagicMock()
        portfolio_id = uuid.uuid4().hex
        sell_price = round(random.uniform(200.0, 500.0), 2)
        purchase_price = round(random.uniform(50.0, 150.0), 2)
        shares = random.randint(1, 50)
        
        mock_db.get_portfolio.return_value = {
            "sell_price": sell_price,
            "purchase_price": purchase_price,
            "shares": shares
        }
        
        calc = MarketPortfolioTaxCalculator(db_storage=mock_db)
        result = calc.calculate_tax(portfolio_id)
        
        expected_profit = (sell_price - purchase_price) * shares
        expected_tax = round(expected_profit * 0.13, 2)
        
        mock_db.get_portfolio.assert_called_once_with(portfolio_id)
        self.assertEqual(result, expected_tax)

    def test_calculate_tax_with_db_storage_not_found(self):
        mock_db = MagicMock()
        portfolio_id = uuid.uuid4().hex
        mock_db.get_portfolio.return_value = None
        
        calc = MarketPortfolioTaxCalculator(db_storage=mock_db)
        result = calc.calculate_tax(portfolio_id)
        
        mock_db.get_portfolio.assert_called_once_with(portfolio_id)
        self.assertEqual(result, 0.0)

    def test_process_dividend_stream_valid(self):
        mock_parser = MagicMock()
        stream_id = uuid.uuid4().hex
        mock_parser.parse_stream.return_value = {"stream_id": stream_id}
        
        calc = MarketPortfolioTaxCalculator(market_parser=mock_parser)
        random_stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        
        result = calc.process_dividend_stream(random_stream_data)
        
        mock_parser.parse_stream.assert_called_once_with(random_stream_data)
        self.assertEqual(result, stream_id)

    def test_process_dividend_stream_invalid_parser(self):
        calc = MarketPortfolioTaxCalculator()
        random_stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        result = calc.process_dividend_stream(random_stream_data)
        self.assertIsNone(result)

    def test_process_dividend_stream_parser_returns_non_dict(self):
        mock_parser = MagicMock()
        mock_parser.parse_stream.return_value = uuid.uuid4().hex
        
        calc = MarketPortfolioTaxCalculator(market_parser=mock_parser)
        random_stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        
        result = calc.process_dividend_stream(random_stream_data)
        self.assertIsNone(result)

    def test_calculate_portfolio_taxes_function(self):
        portfolio_id = uuid.uuid4().hex
        user_id = uuid.uuid4().hex
        
        price1 = round(random.uniform(150.0, 300.0), 2)
        shares1 = random.randint(1, 10)
        price2 = round(random.uniform(105.0, 200.0), 2)
        shares2 = random.randint(1, 10)
        
        deals = [
            {"type": "SELL", "price": price1, "shares": shares1},
            {"type": "BUY", "price": price2, "shares": shares2},
            MagicMock(type="SELL", price=price2, shares=shares2)
        ]
        
        dividends = round(random.uniform(10.0, 500.0), 2)
        
        profit1 = (price1 - 100.0) * shares1
        profit2 = (price2 - 100.0) * shares2
        total_profit = profit1 + profit2
        
        expected_tax = round(max(0.0, total_profit * 0.13 + dividends * 0.13), 2)
        
        result = calculate_portfolio_taxes(portfolio_id, user_id, deals, random.randint(30, 365), dividends)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["user_id"], user_id)
        self.assertEqual(result["total_tax_due"], expected_tax)

    def test_calculate_portfolio_taxes_negative_profit_handled(self):
        portfolio_id = uuid.uuid4().hex
        user_id = uuid.uuid4().hex
        
        deals = [
            {"type": "SELL", "price": 50.0, "shares": 10}
        ]
        dividends = 0.0
        
        result = calculate_portfolio_taxes(portfolio_id, user_id, deals, 30, dividends)
        self.assertEqual(result["total_tax_due"], 0.0)


if __name__ == '__main__':
    unittest.main()