import unittest
import uuid
import random
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator, calculate_portfolio_taxes

class TestMarketPortfolioTaxCalculatorIntegration(unittest.TestCase):
    def test_calculate_portfolio_taxes_integration(self):
        portfolio_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        buy_price = round(random.uniform(50.0, 90.0), 2)
        sell_price = round(random.uniform(110.0, 200.0), 2)
        shares = random.randint(10, 100)
        dividends = round(random.uniform(0.0, 500.0), 2)
        
        deals = [
            {"type": "BUY", "price": buy_price, "shares": shares},
            {"type": "SELL", "price": sell_price, "shares": shares}
        ]
        
        result = calculate_portfolio_taxes(
            portfolio_id=portfolio_id,
            user_id=user_id,
            deals=deals,
            holding_period=random.randint(30, 400),
            dividends=dividends
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("user_id"), user_id)
        self.assertIn("total_tax_due", result)
        self.assertGreaterEqual(result["total_tax_due"], 0.0)

    def test_market_portfolio_tax_calculator_methods(self):
        portfolio_id = str(uuid.uuid4())
        purchase_price = round(random.uniform(10.0, 50.0), 2)
        sell_price = round(random.uniform(60.0, 100.0), 2)
        shares = random.randint(1, 50)
        
        mock_db = type("MockDB", (), {
            "get_portfolio": lambda self, pid: {
                "portfolio_id": pid,
                "purchase_price": purchase_price,
                "sell_price": sell_price,
                "shares": shares
            } if pid == portfolio_id else None
        })()
        
        calc = MarketPortfolioTaxCalculator(db_storage=mock_db)
        tax = calc.calculate_tax(portfolio_id)
        
        expected_profit = (sell_price - purchase_price) * shares
        expected_tax = round(expected_profit * 0.13, 2)
        
        self.assertAlmostEqual(tax, expected_tax, places=2)

    def test_process_dividend_stream_integration(self):
        stream_id = str(uuid.uuid4())
        mock_parser = type("MockParser", (), {
            "parse_stream": lambda self, stream: {"stream_id": stream_id, "data": stream}
        })()
        
        calc = MarketPortfolioTaxCalculator(market_parser=mock_parser)
        test_stream = f"stream_data_{random.randint(1000, 9999)}"
        res = calc.process_dividend_stream(test_stream)
        
        self.assertEqual(res, stream_id)

if __name__ == "__main__":
    unittest.main()