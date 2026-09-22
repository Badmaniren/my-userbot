import unittest
import os
import uuid
import random
from skills.market_portfolio_valuation import PortfolioValuation
from skills.market_parser import MarketParser
import skills.db_storage as db_storage

class TestIntegrationPortfolioValuation(unittest.TestCase):
    def setUp(self):
        self.unique_suffix = str(uuid.uuid4())[:8]
        self.storage_file = f"test_portfolio_{self.unique_suffix}.json"
        self.symbol = f"TST_{self.unique_suffix}"

        self.quantity = round(random.uniform(1.0, 100.0), 2)
        self.buy_price = round(random.uniform(10.0, 500.0), 2)
        self.current_price = round(self.buy_price * random.uniform(0.8, 1.2), 2)

        portfolio_data = {
            self.symbol: {
                "quantity": self.quantity,
                "buy_price": self.buy_price
            }
        }

        if hasattr(db_storage, 'save_portfolio'):
            db_storage.save_portfolio(portfolio_data, self.storage_file)
        elif hasattr(db_storage, 'save_data'):
            db_storage.save_data(portfolio_data, self.storage_file)
        else:
            import json
            with open(self.storage_file, 'w') as f:
                json.dump(portfolio_data, f)

        self.market_parser = MarketParser(self.storage_file)
        self.market_parser.fetch_and_store(self.symbol, self.current_price)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_portfolio_valuation_integration(self):
        valuation = PortfolioValuation(storage_file=self.storage_file)
        
        dummy_url = f"http://localhost:8000/{self.unique_suffix}"

        evaluated = valuation.evaluate_portfolio(dummy_url)
        self.assertIn(self.symbol, evaluated)
        
        symbol_data = evaluated[self.symbol]
        self.assertNotIn("error", symbol_data)

        expected_current_value = round(self.quantity * self.current_price, 2)
        expected_invested = round(self.quantity * self.buy_price, 2)
        expected_pnl = round(expected_current_value - expected_invested, 2)

        self.assertEqual(symbol_data["current_price"], self.current_price)
        self.assertEqual(symbol_data["current_value"], expected_current_value)
        self.assertEqual(symbol_data["invested"], expected_invested)
        self.assertEqual(symbol_data["pnl"], expected_pnl)

        summary = valuation.get_total_summary(dummy_url)
        self.assertEqual(summary["total_value"], expected_current_value)
        self.assertEqual(summary["total_invested"], expected_invested)
        self.assertEqual(summary["total_pnl"], expected_pnl)

        pnl_calc = valuation.calculate_portfolio_pnl(dummy_url)
        self.assertEqual(pnl_calc["total_pnl"], expected_pnl)

if __name__ == "__main__":
    unittest.main()