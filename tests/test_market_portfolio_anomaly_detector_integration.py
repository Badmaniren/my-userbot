import unittest
import uuid
import random
import os
import time

from skills.market_portfolio_anomaly_detector import market_portfolio_anomaly_detector
from skills.db_storage import db_storage
from skills.market_parser import market_parser
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_monitor import market_portfolio_monitor
from skills.market_portfolio_alert_dispatcher import market_portfolio_alert_dispatcher


class TestMarketPortfolioAnomalyDetectorIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.asset_ticker = f"TICK_{random.randint(1000, 9999)}"
        self.transaction_id = str(uuid.uuid4())
        self.anomaly_threshold = round(random.uniform(0.05, 0.25), 2)

        self.test_data = {
            "portfolio_id": self.portfolio_id,
            "transaction_id": self.transaction_id,
            "ticker": self.asset_ticker,
            "amount": random.randint(10000, 1000000),
            "price": round(random.uniform(10.0, 500.0), 2),
            "volatility_index": self.anomaly_threshold + 0.05
        }

    def test_anomaly_detection_pipeline_end_to_end(self):
        parsed_market_data = market_parser.parse_market_feed({
            "ticker": self.asset_ticker,
            "historical_mean_price": self.test_data["price"] * 0.5,
            "current_spike": True
        })
        self.assertIsNotNone(parsed_market_data)

        collected_data = market_portfolio_collector_agent.collect_transaction(
            portfolio_id=self.portfolio_id,
            transaction_payload=self.test_data
        )
        self.assertEqual(collected_data.get("transaction_id"), self.transaction_id)

        db_storage.save_portfolio_snapshot({
            "portfolio_id": self.portfolio_id,
            "asset_data": collected_data,
            "market_context": parsed_market_data
        })

        monitoring_state = market_portfolio_monitor.evaluate_portfolio_health(self.portfolio_id)
        self.assertIn("status", monitoring_state)

        anomaly_result = market_portfolio_anomaly_detector.detect_anomalies({
            "portfolio_id": self.portfolio_id,
            "threshold": self.anomaly_threshold,
            "target_transaction": self.transaction_id
        })

        self.assertIsInstance(anomaly_result, dict)
        self.assertIn("anomaly_detected", anomaly_result)
        self.assertTrue(anomaly_result["anomaly_detected"])
        self.assertEqual(anomaly_result.get("checked_portfolio_id"), self.portfolio_id)

        dispatch_status = market_portfolio_alert_dispatcher.dispatch({
            "alert_type": "PORTFOLIO_ANOMALY",
            "portfolio_id": self.portfolio_id,
            "details": anomaly_result
        })

        self.assertTrue(dispatch_status.get("delivered", False))

        stored_anomaly_log = db_storage.get_anomaly_log(self.portfolio_id)
        self.assertIsNotNone(stored_anomaly_log)
        self.assertEqual(stored_anomaly_log.get("transaction_id"), self.transaction_id)


if __name__ == "__main__":
    unittest.main()