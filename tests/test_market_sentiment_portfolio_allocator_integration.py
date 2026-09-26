import unittest
import uuid
import random

from skills.market_sentiment_portfolio_allocator import (
    MarketSentimentPortfolioAllocator,
    market_sentiment_portfolio_allocator
)
from skills.db_storage import db_storage
from skills.market_news_sentiment_analyzer import market_news_sentiment_analyzer
from skills.market_sentiment_risk_hub import market_sentiment_risk_hub


class RealDbStorageStub:
    def __init__(self):
        self.store = {}

    def fetch_portfolio(self, portfolio_id):
        return self.store.get(portfolio_id, {"assets": []})

    def save_portfolio(self, portfolio_id, data):
        self.store[portfolio_id] = data


class RealStrategyOptimizerStub:
    def optimize(self, portfolio_id):
        return {f"asset_{random.randint(1, 100)}": 1.0}


class RealAnomalyDetectorStub:
    def __init__(self, has_anomaly=False):
        self.has_anomaly = has_anomaly

    def check_anomaly(self, portfolio):
        return self.has_anomaly


class RealAlertDispatcherStub:
    def dispatch(self, portfolio_id):
        return f"<div>Alert for portfolio {portfolio_id}</div>"


class IntegrationTestMarketSentimentPortfolioAllocator(unittest.TestCase):

    def setUp(self):
        self.db = RealDbStorageStub()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.asset_name = f"ASSET_{uuid.uuid4().hex[:4].upper()}"

        self.portfolio_data = {
            "assets": [self.asset_name]
        }
        self.db.save_portfolio(self.portfolio_id, self.portfolio_data)

    def test_recalculate_portfolio_weights_integration(self):
        allocator = MarketSentimentPortfolioAllocator(
            db_storage=self.db,
            market_news_sentiment_analyzer=market_news_sentiment_analyzer,
            market_sentiment_risk_hub=market_sentiment_risk_hub,
            market_portfolio_strategy_optimizer=RealStrategyOptimizerStub()
        )

        result = allocator.recalculate_portfolio_weights(self.portfolio_id)

        self.assertIsInstance(result, dict)
        self.assertTrue(len(result) > 0)

    def test_evaluate_portfolio_safety_integration(self):
        allocator = MarketSentimentPortfolioAllocator(
            db_storage=self.db,
            market_anomaly_detector=RealAnomalyDetectorStub(has_anomaly=True),
            market_portfolio_alert_dispatcher=RealAlertDispatcherStub()
        )

        is_safe = allocator.evaluate_portfolio_safety(self.portfolio_id)
        self.assertTrue(is_safe)

    def test_market_sentiment_portfolio_allocator_functional(self):
        random_sentiment = round(random.uniform(-0.5, 0.5), 2)
        random_risk = round(random.uniform(0.0, 0.3), 2)
        base_w = 0.2

        input_data = {
            "portfolio_id": self.portfolio_id,
            "asset": self.asset_name,
            "sentiment": random_sentiment,
            "risk": random_risk,
            "base_weight": base_w
        }

        output = market_sentiment_portfolio_allocator(input_data)

        self.assertIn("allocation_id", output)
        self.assertEqual(output["portfolio_id"], self.portfolio_id)

        expected_weight = round(base_w * (1.0 + random_sentiment - random_risk), 4)
        self.assertEqual(output["new_weight"], expected_weight)

        stored_record = db_storage({
            "action": "get",
            "table": "portfolio_allocations",
            "id": output["allocation_id"]
        })

        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record.get("asset"), self.asset_name)
        self.assertEqual(stored_record.get("new_weight"), expected_weight)


if __name__ == "__main__":
    unittest.main()