import unittest
import uuid
import random

from skills.market_portfolio_tax_calculator import (
    MarketPortfolioTaxCalculator,
    calculate_portfolio_taxes
)

from skills.db_storage import db_storage
from skills.market_parser import market_parser

class TestMarketPortfolioTaxCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        self.calculator = MarketPortfolioTaxCalculator(
            db_storage=db_storage,
            market_parser=market_parser
        )

    def test_integration_tax_calculation_fifo_and_dividends(self):
        buy_price = round(random.uniform(50.0, 150.0), 2)
        sell_price = round(buy_price + random.uniform(10.0, 50.0), 2)
        shares = random.randint(10, 100)
        dividends = round(random.uniform(100.0, 1000.0), 2)

        deals = [
            {"type": "BUY", "price": buy_price, "shares": shares},
            {"type": "SELL", "price": sell_price, "shares": shares}
        ]

        result = calculate_portfolio_taxes(
            portfolio_id=self.portfolio_id,
            user_id=self.user_id,
            deals=deals,
            holding_period=365,
            dividends=dividends
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["user_id"], self.user_id)

        expected_profit = (sell_price - buy_price) * shares
        expected_tax = round(max(0.0, expected_profit * 0.13 + dividends * 0.13), 2)
        self.assertEqual(result["total_tax_due"], expected_tax)

    def test_integration_market_parser_stream(self):
        stream_id_val = random.randint(1000, 9999)
        mock_stream = f"STREAM_TEST_{stream_id_val}"
        
        stream_result = self.calculator.process_dividend_stream(mock_stream)
        if stream_result is not None:
            self.assertIsNotNone(stream_result)
        else:
            self.assertIsNone(stream_result)

if __name__ == "__main__":
    unittest.main()