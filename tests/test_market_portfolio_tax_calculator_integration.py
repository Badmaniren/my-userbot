import unittest
import uuid
import random
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator, calculate_portfolio_taxes

class RealDbStorageStub:
    def __init__(self, portfolio_data):
        self.portfolio_data = portfolio_data

    def get_portfolio(self, portfolio_id):
        if portfolio_id in self.portfolio_data:
            return self.portfolio_data[portfolio_id]
        return None

class RealMarketParserStub:
    def parse_stream(self, stream):
        if isinstance(stream, dict) and "raw_data" in stream:
            return {"stream_id": stream["raw_data"]}
        return {"stream_id": str(uuid.uuid4())}

class TestMarketPortfolioTaxCalculatorIntegration(unittest.TestCase):
    def test_end_to_end_tax_calculation_and_stream(self):
        portfolio_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        purchase_price = round(random.uniform(10.0, 90.0), 2)
        sell_price = round(purchase_price + random.uniform(20.0, 150.0), 2)
        shares = random.randint(1, 100)
        
        mock_db = RealDbStorageStub({
            portfolio_id: {
                "purchase_price": purchase_price,
                "sell_price": sell_price,
                "shares": shares
            }
        })
        
        mock_parser = RealMarketParserStub()
        
        calc = MarketPortfolioTaxCalculator(db_storage=mock_db, market_parser=mock_parser)
        
        calculated_tax = calc.calculate_tax(portfolio_id)
        expected_profit = (sell_price - purchase_price) * shares
        expected_tax = round(expected_profit * 0.13, 2)
        self.assertEqual(calculated_tax, expected_tax)
        
        stream_token = str(uuid.uuid4())
        stream_payload = {"raw_data": stream_token}
        processed_stream_id = calc.process_dividend_stream(stream_payload)
        self.assertEqual(processed_stream_id, stream_token)
        
        deal_price = round(random.uniform(150.0, 300.0), 2)
        deal_shares = random.randint(5, 50)
        deals = [
            {"type": "SELL", "price": deal_price, "shares": deal_shares}
        ]
        dividends = round(random.uniform(0.0, 500.0), 2)
        
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
        
        total_profit = (deal_price - 100.0) * deal_shares
        expected_total_tax = round(max(0.0, total_profit * 0.13 + dividends * 0.13), 2)
        self.assertEqual(tax_result["total_tax_due"], expected_total_tax)

if __name__ == "__main__":
    unittest.main()