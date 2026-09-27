import unittest
import uuid
import random
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator, calculate_portfolio_taxes

class RealMarketParser:
    def parse_stream(self, stream):
        if isinstance(stream, dict) and "stream_id" in stream:
            return {"stream_id": stream["stream_id"]}
        return None

class RealDbStorage:
    def __init__(self, portfolio_data):
        self.portfolio_data = portfolio_data

    def get_portfolio(self, portfolio_id):
        return self.portfolio_data.get(portfolio_id)

class TestMarketPortfolioTaxCalculatorIntegration(unittest.TestCase):
    def test_calculate_tax_integration_real(self):
        rand_id = str(uuid.uuid4())
        sell_price = float(randint_val := random.randint(150, 300))
        purchase_price = float(random.randint(50, 100))
        shares = float(random.randint(10, 50))
        
        expected_profit = (sell_price - purchase_price) * shares
        expected_tax = round(expected_profit * 0.13, 2)

        portfolio_data = {
            rand_id: {
                "sell_price": sell_price,
                "purchase_price": purchase_price,
                "shares": shares
            }
        }

        db = RealDbStorage(portfolio_data)
        calc = MarketPortfolioTaxCalculator(db_storage=db)
        
        result = calc.calculate_tax(rand_id)
        self.assertEqual(result, expected_tax)

    def test_process_dividend_stream_integration_real(self):
        stream_id = str(uuid.uuid4())
        stream_data = {"stream_id": stream_id, "payload": random.randint(1000, 9999)}
        
        parser = RealMarketParser()
        calc = MarketPortfolioTaxCalculator(market_parser=parser)
        
        result = calc.process_dividend_stream(stream_data)
        self.assertEqual(result, stream_id)

    def test_calculate_portfolio_taxes_standalone_real(self):
        portfolio_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        price = float(random.randint(120, 200))
        shares = float(random.randint(5, 20))
        dividends = float(random.randint(100, 500))

        deals = [{"type": "SELL", "price": price, "shares": shares}]
        
        total_profit = (price - 100.0) * shares
        expected_total_tax = round(max(0.0, total_profit * 0.13 + dividends * 0.13), 2)

        res = calculate_portfolio_taxes(portfolio_id, user_id, deals, 365, dividends)
        
        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["user_id"], user_id)
        self.assertEqual(res["total_tax_due"], expected_total_tax)

if __name__ == "__main__":
    unittest.main()