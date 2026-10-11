import unittest
import uuid
import random
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator, calculate_portfolio_taxes

class TestMarketPortfolioTaxCalculatorIntegration(unittest.TestCase):
    def test_integration_tax_calculation_and_dividends(self):
        portfolio_id_val = str(uuid.uuid4())
        user_id_val = str(uuid.uuid4())
        
        sell_price = round(random.uniform(150.0, 300.0), 2)
        purchase_price = round(random.uniform(50.0, 100.0), 2)
        shares = random.randint(10, 100)
        dividends = round(random.uniform(100.0, 1000.0), 2)
        
        class MockDBStorage:
            def get_portfolio(self, p_id):
                if p_id == portfolio_id_val:
                    return {
                        "portfolio_id": p_id,
                        "sell_price": sell_price,
                        "purchase_price": purchase_price,
                        "shares": shares
                    }
                return None

        class MockMarketParser:
            def parse_stream(self, stream):
                return {"stream_id": stream}

        db = MockDBStorage()
        parser = MockMarketParser()

        calculator = MarketPortfolioTaxCalculator(db_storage=db, market_parser=parser)
        
        calc_tax_result = calculator.calculate_tax(portfolio_id_val)
        expected_profit = (sell_price - purchase_price) * shares
        expected_tax = round(expected_profit * 0.13, 2)
        self.assertEqual(calc_tax_result, expected_tax)

        test_stream_id = str(uuid.uuid4())
        stream_result = calculator.process_dividend_stream(test_stream_id)
        self.assertEqual(stream_result, test_stream_id)

        deals = [
            {
                "type": "SELL",
                "price": sell_price,
                "shares": shares
            }
        ]
        
        portfolio_taxes_result = calculate_portfolio_taxes(
            portfolio_id=portfolio_id_val,
            user_id=user_id_val,
            deals=deals,
            holding_period=random.randint(30, 730),
            dividends=dividends
        )

        self.assertIsInstance(portfolio_taxes_result, dict)
        self.assertEqual(portfolio_taxes_result["portfolio_id"], portfolio_id_val)
        self.assertEqual(portfolio_taxes_result["user_id"], user_id_val)
        
        expected_total_profit = (sell_price - 100.0) * shares
        expected_total_tax_due = round(max(0.0, expected_total_profit * 0.13 + dividends * 0.13), 2)
        self.assertEqual(portfolio_taxes_result["total_tax_due"], expected_total_tax_due)

if __name__ == "__main__":
    unittest.main()