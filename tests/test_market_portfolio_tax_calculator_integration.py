import unittest
import uuid
import random
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator, calculate_portfolio_taxes

class RealDbStorage:
    def __init__(self):
        self.portfolios = {}

    def get_portfolio(self, portfolio_id):
        return self.portfolios.get(portfolio_id)

class RealMarketParser:
    def parse_stream(self, stream):
        if isinstance(stream, dict) and "stream_id" in stream:
            return {"stream_id": stream["stream_id"]}
        return None

class TestMarketPortfolioTaxCalculatorIntegration(unittest.TestCase):
    def test_end_to_end_tax_calculation_and_stream(self):
        db = RealDbStorage()
        parser = RealMarketParser()
        
        portfolio_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        purchase_price = round(random.uniform(50.0, 90.0), 2)
        sell_price = round(random.uniform(110.0, 200.0), 2)
        shares = random.randint(10, 100)
        
        db.portfolios[portfolio_id] = {
            "purchase_price": purchase_price,
            "sell_price": sell_price,
            "shares": shares
        }
        
        calculator = MarketPortfolioTaxCalculator(db_storage=db, market_parser=parser)
        
        calculated_tax = calculator.calculate_tax(portfolio_id)
        expected_profit = (sell_price - purchase_price) * shares
        expected_tax = round(expected_profit * 0.13, 2)
        self.assertEqual(calculated_tax, expected_tax)
        
        stream_id = str(uuid.uuid4())
        stream_data = {"stream_id": stream_id}
        processed_stream = calculator.process_dividend_stream(stream_data)
        self.assertEqual(processed_stream, stream_id)
        
        deals = [
            {"type": "SELL", "price": sell_price, "shares": shares}
        ]
        dividends = round(random.uniform(10.0, 500.0), 2)
        holding_period = random.randint(30, 365)
        
        result = calculate_portfolio_taxes(
            portfolio_id=portfolio_id,
            user_id=user_id,
            deals=deals,
            holding_period=holding_period,
            dividends=dividends
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["user_id"], user_id)
        
        deal_profit = (sell_price - 100.0) * shares
        expected_total_tax = round(max(0.0, deal_profit * 0.13 + dividends * 0.13), 2)
        self.assertEqual(result["total_tax_due"], expected_total_tax)

if __name__ == "__main__":
    unittest.main()