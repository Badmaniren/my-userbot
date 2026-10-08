import unittest
from unittest.mock import patch
import uuid
import random
import io

from skills.market_portfolio_stress_audit_analytics_hub import (
    MarketPortfolioStressAuditAnalyticsHub,
    market_portfolio_stress_audit_analytics_hub
)


class TestMarketPortfolioStressAuditAnalyticsHub(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:10]}"
        self.trend_id = f"trend_{uuid.uuid4().hex[:10]}"
        self.scale = random.randint(1, 100)
        self.mock_db = unittest.mock.MagicMock()
        self.mock_aggregator = unittest.mock.MagicMock()

    def test_aggregate_stress_metrics_default(self):
        hub = MarketPortfolioStressAuditAnalyticsHub()
        result = hub.aggregate_stress_metrics(self.portfolio_id)

        self.assertIn("portfolio_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertIn("stress_metrics", result)
        self.assertIn("stream_size", result)
        self.assertGreater(result["stream_size"], 0)

    def test_aggregate_stress_metrics_with_db(self):
        expected_stress = {"portfolio_id": self.portfolio_id, "stress_value": random.uniform(10.0, 99.9)}
        self.mock_db.fetch_stress_data.return_value = expected_stress

        hub = MarketPortfolioStressAuditAnalyticsHub(db_storage=self.mock_db)
        result = hub.aggregate_stress_metrics(self.portfolio_id)

        self.mock_db.fetch_stress_data.assert_called_once_with(self.portfolio_id)
        self.assertEqual(result["stress_metrics"], expected_stress)

    def test_build_predictive_trends_default(self):
        hub = MarketPortfolioStressAuditAnalyticsHub()
        trends = hub.build_predictive_trends(self.trend_id, self.scale)

        self.assertIsInstance(trends, list)
        self.assertTrue(len(trends) > 0)
        self.assertEqual(trends[0]["trend_id"], self.trend_id)
        self.assertEqual(trends[0]["scale"], self.scale)

    def test_build_predictive_trends_with_aggregator(self):
        expected_trend = [{"trend_id": self.trend_id, "scale": self.scale, "prediction": "stable"}]
        self.mock_aggregator.calculate_trend.return_value = expected_trend

        hub = MarketPortfolioStressAuditAnalyticsHub(market_portfolio_predictive_aggregator=self.mock_aggregator)
        trends = hub.build_predictive_trends(self.trend_id, self.scale)

        self.mock_aggregator.calculate_trend.assert_called_once_with(self.trend_id, self.scale)
        self.assertEqual(trends, [expected_trend])

    def test_process_analytics_payload_without_db(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "metric_type": uuid.uuid4().hex,
            "value": random.randint(100, 500)
        }

        with patch('skills.market_portfolio_stress_audit_analytics_hub.db_storage') as mock_fallback_db:
            hub = MarketPortfolioStressAuditAnalyticsHub()
            result = hub.process_analytics_payload(payload)

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["payload_received"], payload)
            self.assertIn("analytics_id", result)
            mock_fallback_db.set.assert_called_once()

    def test_process_analytics_payload_with_db(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "custom_key": uuid.uuid4().hex
        }

        hub = MarketPortfolioStressAuditAnalyticsHub(db_storage=self.mock_db)
        result = hub.process_analytics_payload(payload)

        self.mock_db.set.assert_called_once()
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["status"], "success")

    def test_functional_adapter_wrapper(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "adapter_test_token": uuid.uuid4().hex
        }

        with patch('skills.market_portfolio_stress_audit_analytics_hub.db_storage') as mock_fallback_db:
            result = market_portfolio_stress_audit_analytics_hub(payload)

            self.assertIsInstance(result, dict)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["payload_received"], payload)
            mock_fallback_db.set.assert_called_once()


if __name__ == "__main__":
    unittest.main()