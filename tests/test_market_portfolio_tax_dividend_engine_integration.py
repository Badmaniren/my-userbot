import unittest
import uuid
import random
from skills.market_portfolio_tax_dividend_engine import MarketPortfolioTaxDividendEngine
from skills.market_portfolio_dividend_tracker import market_portfolio_dividend_tracker
from skills.market_portfolio_tax_calculator import market_portfolio_tax_calculator
from skills.db_storage import db_storage
from skills.market_portfolio_integration_hub import market_portfolio_integration_hub

class TestMarketPortfolioTaxDividendEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.engine = MarketPortfolioTaxDividendEngine(
            db_storage=db_storage,
            market_portfolio_dividend_tracker=market_portfolio_dividend_tracker,
            market_portfolio_tax_calculator=market_portfolio_tax_calculator,
            market_portfolio_integration_hub=market_portfolio_integration_hub
        )
        self.portfolio_id = str(uuid.uuid4())
        self.ticker = f"TICK_{random.randint(1000, 9999)}"
        self.anomaly_id = str(uuid.uuid4())
        self.impact_multiplier = round(random.uniform(1.1, 2.5), 2)

    def test_aggregate_tax_and_dividends_integration(self):
        result = self.engine.aggregate_tax_and_dividends(portfolio_id=self.portfolio_id)

        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("dividends", result)
        self.assertIn("taxes", result)
        self.assertIn("net_income", result)
        self.assertIsInstance(result["net_income"], float)

    def test_verify_consistency_integration(self):
        consistency_result = self.engine.verify_consistency(portfolio_id=self.portfolio_id)

        self.assertIn("is_consistent", consistency_result)
        self.assertIn("tracker_basis", consistency_result)
        self.assertIn("calculator_basis", consistency_result)
        self.assertIn("discrepancy", consistency_result)
        self.assertIn("incident_id", consistency_result)
        self.assertIsInstance(consistency_result["is_consistent"], bool)

    def test_process_market_anomaly_event_integration(self):
        payload = {
            "ticker": self.ticker,
            "impact_multiplier": self.impact_multiplier,
            "anomaly_id": self.anomaly_id
        }

        response = self.engine.process_market_anomaly_event(anomaly_payload=payload)

        self.assertEqual(response.get("status"), "success")
        self.assertEqual(response.get("anomaly_id"), self.anomaly_id)

if __name__ == "__main__":
    unittest.main()