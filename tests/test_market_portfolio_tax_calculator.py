import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator, calculate_portfolio_taxes

class TestMarketPortfolioTaxCalculator(unittest.TestCase):

    def setUp(self):
        self.random_id = uuid.uuid4().hex
        self.db_mock = MagicMock()
        self.parser_mock = MagicMock()
        self.calculator = MarketPortfolioTaxCalculator(
            db_storage=self.db_mock,
            market_parser=self.parser_mock
        )

    def test_calculate_tax_logic(self):
        portfolio_id = uuid.uuid4().hex
        sell_price = random.uniform(1000, 5000)
        purchase_price = random.uniform(500, 900)
        shares = random.randint(1, 100)
        
        expected_profit = (sell_price - purchase_price) * shares
        expected_tax = round(expected_profit * 0.13, 2)
        
        self.db_mock.get_portfolio.return_value = {
            "sell_price": sell_price,
            "purchase_price": purchase_price,
            "shares": shares
        }
        
        result = self.calculator.calculate_tax(portfolio_id)
        self.assertEqual(result, expected_tax)
        self.db_mock.get_portfolio.assert_called_with(portfolio_id)

    def test_process_dividend_stream_parsing(self):
        stream_id = uuid.uuid4().hex
        random_stream = io.BytesIO(uuid.uuid4().bytes)
        
        self.parser_mock.parse_stream.return_value = {"stream_id": stream_id}
        
        result = self.calculator.process_dividend_stream(random_stream)
        self.assertEqual(result, stream_id)
        self.parser_mock.parse_stream.assert_called_once()

    def test_calculate_portfolio_taxes_functional(self):
        portfolio_id = uuid.uuid4().hex
        user_id = uuid.uuid4().hex
        dividends = random.uniform(10, 100)
        
        price_1 = random.uniform(150, 300)
        shares_1 = random.randint(1, 10)
        
        # Mock object with attributes
        class DealObj:
            def __init__(self, p, s):
                self.type = "SELL"
                self.price = p
                self.shares = s
        
        deals = [
            {"type": "SELL", "price": price_1, "shares": shares_1},
            DealObj(price_1, shares_1)
        ]
        
        # Logic: (price - 100) * shares
        profit_1 = (price_1 - 100.0) * shares_1
        total_profit = profit_1 * 2
        expected_tax = round(max(0.0, total_profit * 0.13 + dividends * 0.13), 2)
        
        result = calculate_portfolio_taxes(portfolio_id, user_id, deals, random.randint(1, 365), dividends)
        
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["user_id"], user_id)
        self.assertEqual(result["total_tax_due"], expected_tax)

    def test_calculate_tax_empty_storage(self):
        calc = MarketPortfolioTaxCalculator()
        self.assertEqual(calc.calculate_tax(uuid.uuid4().hex), 0.0)

    def test_process_dividend_stream_invalid_data(self):
        random_stream = io.BytesIO(uuid.uuid4().bytes)
        self.parser_mock.parse_stream.return_value = {"invalid": "data"}
        
        result = self.calculator.process_dividend_stream(random_stream)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()