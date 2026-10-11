import unittest
import uuid
import random
from skills.market_portfolio_net_dividend_calculator import NetDividendCalculator
from skills.market_portfolio_dividend_tracker import DividendTracker
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator
from db_storage import DBStorage

class TestNetDividendCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.db = DBStorage()
        self.tax_calculator = MarketPortfolioTaxCalculator()
        self.api_gateway = None  # Инициализация согласно сигнатуре навыка
        self.dividend_tracker = DividendTracker(
            db_storage=self.db,
            tax_calculator=self.tax_calculator,
            api_gateway=self.api_gateway
        )
        self.net_calculator = NetDividendCalculator(
            dividend_tracker=self.dividend_tracker,
            tax_calculator=self.tax_calculator,
            db_storage=self.db
        )

    def test_net_dividend_yield_composition_calculation(self):
        portfolio_id = str(uuid.uuid4())
        asset_ticker = f"TICKER_{random.randint(1000, 9999)}"
        shares_count = random.randint(10, 1000)
        tax_rate = round(random.uniform(0.05, 0.25), 2)

        dividend_projection = self.dividend_tracker.calculate_projected_dividends(
            asset_ticker=asset_ticker,
            shares_count=shares_count,
            tax_rate=tax_rate
        )
        self.assertIsNotNone(dividend_projection)

        tax_result = self.tax_calculator.calculate_tax(portfolio_id=portfolio_id)
        self.assertIsNotNone(tax_result)

        net_yield_result = self.net_calculator.calculate_net_dividend_yield(
            portfolio_id=portfolio_id,
            asset_ticker=asset_ticker,
            shares_count=shares_count,
            tax_rate=tax_rate
        )

        self.assertIn("net_dividend_amount", net_yield_result)
        self.assertIn("net_dividend_yield", net_yield_result)
        self.assertGreaterEqual(net_yield_result["net_dividend_amount"], 0.0)

if __name__ == "__main__":
    unittest.main()