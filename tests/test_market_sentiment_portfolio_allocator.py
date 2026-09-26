import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_sentiment_portfolio_allocator import (
    MarketSentimentPortfolioAllocator,
    market_sentiment_portfolio_allocator
)

class TestMarketSentimentPortfolioAllocator(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.asset_name = f"ASSET_{uuid.uuid4().hex[:6]}"
        self.mock_db = MagicMock()
        self.mock_strategy_optimizer = MagicMock()
        self.mock_news_analyzer = MagicMock()
        self.mock_risk_hub = MagicMock()
        self.mock_anomaly_detector = MagicMock()
        self.mock_alert_dispatcher = MagicMock()
        self.mock_data_exporter = MagicMock()

        self.allocator = MarketSentimentPortfolioAllocator(
            db_storage=self.mock_db,
            market_strategy_optimizer=self.mock_strategy_optimizer,
            market_news_sentiment_analyzer=self.mock_news_analyzer,
            market_sentiment_risk_hub=self.mock_risk_hub,
            market_anomaly_detector=self.mock_anomaly_detector,
            market_portfolio_alert_dispatcher=self.mock_alert_dispatcher,
            market_portfolio_data_exporter=self.mock_data_exporter
        )

    def test_recalculate_portfolio_weights_success(self):
        expected_weights = {self.asset_name: round(random.uniform(0.1, 1.0), 4)}
        self.mock_db.fetch_portfolio.return_value = {"assets": [self.asset_name]}
        self.mock_strategy_optimizer.optimize.return_value = expected_weights

        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            result = self.allocator.recalculate_portfolio_weights(self.portfolio_id)

        self.mock_db.fetch_portfolio.assert_called_once_with(self.portfolio_id)
        self.mock_news_analyzer.analyze.assert_called_once_with(self.asset_name)
        self.mock_risk_hub.calculate_risk.assert_called_once_with(self.asset_name)
        self.mock_strategy_optimizer.optimize.assert_called_once_with(self.portfolio_id)
        mock_get.assert_called_once()
        self.assertEqual(result, expected_weights)

    def test_recalculate_portfolio_weights_fallback(self):
        self.mock_db.fetch_portfolio.return_value = {"assets": [self.asset_name]}
        allocator_no_opt = MarketSentimentPortfolioAllocator(
            db_storage=self.mock_db,
            market_news_sentiment_analyzer=self.mock_news_analyzer,
            market_sentiment_risk_hub=self.mock_risk_hub
        )

        with patch("requests.get") as mock_get:
            result = allocator_no_opt.recalculate_portfolio_weights(self.portfolio_id)

        self.assertEqual(result, {self.asset_name: 1.0})

    def test_evaluate_portfolio_safety_anomaly_true(self):
        portfolio_data = {"id": self.portfolio_id, "risk_level": random.randint(50, 100)}
        anomaly_msg = f"<div>Warning: {uuid.uuid4().hex}</div>"

        self.mock_db.fetch_portfolio.return_value = portfolio_data
        self.mock_anomaly_detector.check_anomaly.return_value = True
        self.mock_alert_dispatcher.dispatch.return_value = anomaly_msg

        is_safe = self.allocator.evaluate_portfolio_safety(self.portfolio_id)

        self.assertTrue(is_safe)
        self.mock_anomaly_detector.check_anomaly.assert_called_once_with(portfolio_data)
        self.mock_alert_dispatcher.dispatch.assert_called_once_with(self.portfolio_id)

    def test_evaluate_portfolio_safety_anomaly_false(self):
        portfolio_data = {"id": self.portfolio_id, "risk_level": random.randint(1, 10)}
        self.mock_db.fetch_portfolio.return_value = portfolio_data
        self.mock_anomaly_detector.check_anomaly.return_value = False

        is_safe = self.allocator.evaluate_portfolio_safety(self.portfolio_id)

        self.assertFalse(is_safe)
        self.mock_anomaly_detector.check_anomaly.assert_called_once_with(portfolio_data)
        self.mock_alert_dispatcher.dispatch.assert_not_called()

    def test_export_allocation_audit_trail_with_exporter(self):
        stream = io.BytesIO(uuid.uuid4().bytes)
        expected_export_result = f"export_{uuid.uuid4().hex[:8]}"
        self.mock_data_exporter.export.return_value = expected_export_result

        result = self.allocator.export_allocation_audit_trail(stream)

        self.assertEqual(result, expected_export_result)
        self.mock_data_exporter.export.assert_called_once_with(stream)

    def test_export_allocation_audit_trail_fallback(self):
        stream = io.BytesIO(uuid.uuid4().bytes)
        allocator_no_exporter = MarketSentimentPortfolioAllocator()

        result = allocator_no_exporter.export_allocation_audit_trail(stream)

        self.assertIsInstance(result, str)
        self.assertEqual(len(result), 32)

    def test_functional_market_sentiment_portfolio_allocator(self):
        sentiment_score = round(random.uniform(-0.5, 0.5), 2)
        risk_score = round(random.uniform(0.0, 0.3), 2)
        base_weight = round(random.uniform(0.1, 0.5), 2)

        allocation_input = {
            "portfolio_id": self.portfolio_id,
            "asset": self.asset_name,
            "sentiment": {"score": sentiment_score},
            "risk": {"risk_score": risk_score},
            "base_weight": base_weight
        }

        with patch("skills.market_sentiment_portfolio_allocator.db_storage") as mock_func_db:
            res = market_sentiment_portfolio_allocator(allocation_input)

        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertIn("allocation_id", res)
        self.assertIn("new_weight", res)
        expected_weight = round(base_weight * (1.0 + sentiment_score - risk_score), 4)
        self.assertEqual(res["new_weight"], expected_weight)
        mock_func_db.assert_called_once()