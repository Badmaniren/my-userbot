import unittest
import uuid
import random
from skills.market_portfolio_tax_dividend_sync import (
    sync_portfolio_tax_and_dividends,
    PortfolioTaxDividendSyncManager
)
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator
from skills.market_portfolio_dividend_tracker import DividendTracker

class TestMarketPortfolioTaxDividendSyncIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.owner_uuid = str(uuid.uuid4())
        self.asset_ticker = f"TICKER_{random.randint(1000, 9999)}"
        self.shares_count = random.randint(10, 500)
        self.tax_rate = round(random.uniform(0.13, 0.25), 2)
        self.db_storage = f"sqlite:///test_db_{uuid.uuid4()}.db"

        self.tax_calculator = MarketPortfolioTaxCalculator()
        self.dividend_tracker = DividendTracker(
            db_storage=self.db_storage,
            tax_calculator=self.tax_calculator,
            api_gateway=None
        )

        self.sync_manager = PortfolioTaxDividendSyncManager(
            db_storage=self.db_storage,
            tax_calculator=self.tax_calculator,
            dividend_tracker=self.dividend_tracker
        )

    def test_sync_composition_and_net_yield_calculation(self):
        dividend_stream = [
            {
                "ticker": self.asset_ticker,
                "amount": round(random.uniform(50.0, 500.0), 2),
                "date": "2023-11-01"
            },
            {
                "ticker": self.asset_ticker,
                "amount": round(random.uniform(50.0, 500.0), 2),
                "date": "2023-12-01"
            }
        ]

        sync_result = sync_portfolio_tax_and_dividends(
            portfolio_id=self.portfolio_id,
            owner_uuid=self.owner_uuid,
            asset_ticker=self.asset_ticker,
            shares_count=self.shares_count,
            tax_rate=self.tax_rate,
            dividend_stream=dividend_stream,
            db_storage=self.db_storage
        )

        self.assertIsInstance(sync_result, dict)
        self.assertIn("net_yield", sync_result)
        self.assertIn("total_dividends", sync_result)
        self.assertIn("total_tax", sync_result)
        self.assertEqual(sync_result.get("portfolio_id"), self.portfolio_id)

        projected = self.dividend_tracker.calculate_projected_dividends(
            asset_ticker=self.asset_ticker,
            shares_count=self.shares_count,
            tax_rate=self.tax_rate
        )
        self.assertIsNotNone(projected)

        manager_result = self.sync_manager.process_sync_cycle(
            portfolio_id=self.portfolio_id,
            dividend_stream=dividend_stream
        )
        self.assertIsInstance(manager_result, dict)
        self.assertTrue(manager_result.get("synchronized", False))

if __name__ == "__main__":
    unittest.main()