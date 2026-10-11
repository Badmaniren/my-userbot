import unittest
import uuid
import random
from skills.db_storage import DbStorage
from skills.market_parser import MarketParser
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator, calculate_portfolio_taxes

class TestMarketPortfolioTaxCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.db = DbStorage()
        self.parser = MarketParser()
        self.calculator = MarketPortfolioTaxCalculator(
            db_storage=self.db,
            market_parser=self.parser
        )

    def test_end_to_end_tax_calculation_and_stream_processing(self):
        portfolio_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        buy_price = round(random.uniform(50.0, 90.0), 2)
        sell_price = round(random.uniform(100.0, 200.0), 2)
        shares = random.randint(10, 100)
        
        self.db.portfolios = getattr(self.db, "portfolios", {})
        self.db.portfolios[portfolio_id] = {
            "purchase_price": buy_price,
            "sell_price": sell_price,
            "shares": shares
        }
        
        calculated_tax = self.calculator.calculate_tax(portfolio_id)
        expected_profit = (sell_price - buy_price) * shares
        expected_tax = round(expected_profit * 0.13, 2)
        self.assertEqual(calculated_tax, expected_tax)

        stream_id_val = str(uuid.uuid4())
        test_stream = {"stream_id": stream_id_val, "data": random.randint(1000, 9999)}
        processed_stream_id = self.calculator.process_dividend_stream(test_stream)
        self.assertEqual(processed_stream_id, stream_id_val)

        deals = [
            {"type": "BUY", "price": buy_price, "shares": shares},
            {"type": "SELL", "price": sell_price, "shares": shares}
        ]
        dividends = round(random.uniform(10.0, 500.0), 2)
        
        tax_result = calculate_portfolio_taxes(
            portfolio_id=portfolio_id,
            user_id=user_id,
            deals=deals,
            holding_period=random.randint(30, 400),
            dividends=dividends
        )

        self.assertIsInstance(tax_result, dict)
        self.assertEqual(tax_result["portfolio_id"], portfolio_id)
        self.assertEqual(tax_result["user_id"], user_id)
        self.assertIn("total_tax_due", tax_result)
        
        expected_total_profit = (sell_price - 100.0) * shares
        expected_total_tax = round(max(0.0, expected_total_profit * 0.13 + dividends * 0.13), 2)
        self.assertEqual(tax_result["total_tax_due"], expected_total_tax)

if __name__ == "__main__":
    unittest.main()