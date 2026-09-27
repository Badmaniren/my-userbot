import unittest
import uuid
import random
import os
from skills.market_portfolio_liquidity_analyzer import (
    market_portfolio_liquidity_analyzer,
    market_portfolio_collector_agent,
    db_storage,
    market_portfolio_api_gateway
)

class TestMarketPortfolioLiquidityAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.asset_ticker = f"TEST_{random.randint(1000, 9999)}"
        self.position_volume = float(random.randint(100, 10000))
        self.output_report_path = f"liquidity_report_{self.portfolio_id}.json"

    def tearDown(self):
        if os.path.exists(self.output_report_path):
            os.remove(self.output_report_path)

    def test_liquidity_analyzer_end_to_end_pipeline(self):
        collector_payload = {
            "portfolio_id": self.portfolio_id,
            "ticker": self.asset_ticker,
            "volume": self.position_volume,
            "timestamp": random.randint(1600000000, 1700000000)
        }

        ingestion_result = market_portfolio_collector_agent(collector_payload)
        self.assertIsNotNone(ingestion_result, "Collector agent must return execution result")

        stored_data = db_storage({
            "action": "get_position",
            "portfolio_id": self.portfolio_id,
            "ticker": self.asset_ticker
        })
        self.assertIsNotNone(stored_data, "Data must be successfully persisted in database storage")

        analysis_result = market_portfolio_liquidity_analyzer({
            "portfolio_id": self.portfolio_id,
            "calculation_method": "ADV_v2",
            "threshold": random.uniform(0.01, 0.5)
        })

        self.assertIsInstance(analysis_result, dict, "Analyzer must return a dictionary payload")
        self.assertIn("risk_score", analysis_result, "Result must contain liquidity risk score")
        self.assertIn("liquidation_time_days", analysis_result, "Result must calculate liquidation time")
        self.assertEqual(analysis_result.get("portfolio_id"), self.portfolio_id)

        gateway_response = market_portfolio_api_gateway({
            "endpoint": "liquidity_summary",
            "portfolio_id": self.portfolio_id,
            "report_path": self.output_report_path
        })

        self.assertTrue(gateway_response.get("success"), "API Gateway must process liquidity summary successfully")
        self.assertTrue(os.path.exists(self.output_report_path), "Integration must physically generate the output report file")

if __name__ == "__main__":
    unittest.main()