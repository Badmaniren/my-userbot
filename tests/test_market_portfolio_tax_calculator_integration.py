import unittest
import uuid
import random
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator, calculate_portfolio_taxes

class TestMarketPortfolioTaxCalculatorIntegration(unittest.TestCase):
    def test_var_cvar_and_tax_calculation_integration(self):
        random_portfolio_id = str(uuid.uuid4())
        random_user_id = str(uuid.uuid4())
        
        purchase_price = round(random.uniform(50.0, 150.0), 2)
        sell_price = round(purchase_price + random.uniform(10.0, 50.0), 2)
        shares_count = random.randint(10, 100)
        
        class RealDBStorage:
            def __init__(self, p_id, p_price, s_price, shares):
                self.p_id = p_id
                self.data = {
                    "portfolio_id": self.p_id,
                    "purchase_price": p_price,
                    "sell_price": s_price,
                    "shares": shares
                }
            def get_portfolio(self, portfolio_id):
                if portfolio_id == self.p_id:
                    return self.data
                return None

        db = RealDBStorage(random_portfolio_id, purchase_price, sell_price, shares_count)
        
        calculator = MarketPortfolioTaxCalculator(db_storage=db)
        calculated_tax = calculator.calculate_tax(random_portfolio_id)
        
        expected_profit = (sell_price - purchase_price) * shares_count
        expected_tax = round(expected_profit * 0.13, 2)
        
        self.assertEqual(calculated_tax, expected_tax)

        deals = [
            {
                "type": "SELL",
                "price": sell_price,
                "shares": shares_count
            }
        ]
        dividends = round(random.uniform(0.0, 500.0), 2)
        holding_period = random.randint(30, 365)

        batch_result = calculate_portfolio_taxes(
            portfolio_id=random_portfolio_id,
            user_id=random_user_id,
            deals=deals,
            holding_period=holding_period,
            dividends=dividends
        )

        self.assertIsInstance(batch_result, dict)
        self.assertEqual(batch_result["portfolio_id"], random_portfolio_id)
        self.assertEqual(batch_result["user_id"], random_user_id)
        
        expected_total_profit = (sell_price - 100.0) * shares_count
        expected_total_tax_due = round(max(0.0, expected_total_profit * 0.13 + dividends * 0.13), 2)
        self.assertEqual(batch_result["total_tax_due"], expected_total_tax_due)

if __name__ == "__main__":
    unittest.main()