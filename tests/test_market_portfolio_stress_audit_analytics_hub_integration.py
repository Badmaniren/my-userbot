import unittest
import uuid
import random

from skills.db_storage import db_storage
from skills.market_portfolio_stress_audit_analytics_hub import (
    MarketPortfolioStressAuditAnalyticsHub,
    market_portfolio_stress_audit_analytics_hub
)


class TestMarketPortfolioStressAuditAnalyticsHubIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:10]}"
        self.trend_id = f"trend_{uuid.uuid4().hex[:10]}"
        self.scale = random.randint(10, 100)
        self.payload = {
            "portfolio_id": self.portfolio_id,
            "metric_type": "stress_test",
            "risk_tolerance": random.uniform(0.01, 0.5)
        }

    def test_aggregate_stress_metrics_integration(self):
        hub = MarketPortfolioStressAuditAnalyticsHub(db_storage=db_storage)
        result = hub.aggregate_stress_metrics(self.portfolio_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("stress_metrics", result)
        self.assertIn("stream_size", result)
        self.assertGreater(result["stream_size"], 0)

    def test_build_predictive_trends_integration(self):
        hub = MarketPortfolioStressAuditAnalyticsHub(db_storage=db_storage)
        trends = hub.build_predictive_trends(self.trend_id, self.scale)

        self.assertIsInstance(trends, list)
        self.assertTrue(len(trends) > 0)
        trend_item = trends[0]
        self.assertEqual(trend_item.get("trend_id"), self.trend_id)
        self.assertEqual(trend_item.get("scale"), self.scale)

    def test_process_analytics_payload_and_storage(self):
        hub = MarketPortfolioStressAuditAnalyticsHub(db_storage=db_storage)
        result = hub.process_analytics_payload(self.payload)

        self.assertIsInstance(result, dict)
        analytics_id = result.get("analytics_id")
        self.assertIsNotNone(analytics_id)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("payload_received"), self.payload)

        stored_data = db_storage.get(f"audit_analytics_{analytics_id}")
        self.assertIsNotNone(stored_data)
        self.assertEqual(stored_data.get("analytics_id"), analytics_id)
        self.assertEqual(stored_data.get("portfolio_id"), self.portfolio_id)

    def test_functional_adapter_integration(self):
        result = market_portfolio_stress_audit_analytics_hub(self.payload)

        self.assertIsInstance(result, dict)
        analytics_id = result.get("analytics_id")
        self.assertIsNotNone(analytics_id)
        self.assertEqual(result.get("portfolio_id"), self.payload["portfolio_id"])

        retrieved = db_storage.get(f"audit_analytics_{analytics_id}")
        self.assertEqual(retrieved.get("status"), "success")


if __name__ == "__main__":
    unittest.main()