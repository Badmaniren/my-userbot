import unittest
import uuid
import random
import os
import time

from skills.market_portfolio_rebalance_engine import market_portfolio_rebalance_engine
from skills.db_storage import db_storage
from skills.market_portfolio_monitor import market_portfolio_monitor
from skills.market_news_sentiment_analyzer import market_news_sentiment_analyzer
from skills.market_anomaly_detector import market_anomaly_detector

class TestMarketPortfolioRebalanceEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.user_id = f"user_{uuid.uuid4().hex[:8]}"
        self.initial_budget = round(random.uniform(10000.0, 1000000.0), 2)
        self.risk_tolerance = random.choice(["LOW", "MEDIUM", "HIGH", "AGGRESSIVE"])
        
        # Initialize test data in real DB storage to avoid mocks
        db_storage.save_portfolio({
            "portfolio_id": self.portfolio_id,
            "user_id": self.user_id,
            "budget": self.initial_budget,
            "risk_tolerance": self.risk_tolerance,
            "assets": {
                "BTC": {"allocation": 0.5, "amount": random.uniform(0.1, 2.0)},
                "ETH": {"allocation": 0.3, "amount": random.uniform(1.0, 10.0)},
                "USDT": {"allocation": 0.2, "amount": random.uniform(500.0, 5000.0)}
            }
        })

    def test_rebalance_engine_end_to_end_integration(self):
        # 1. Generate dynamic market conditions via real dependent modules
        sentiment_score = round(random.uniform(-1.0, 1.0), 4)
        anomaly_threshold = round(random.uniform(0.5, 0.99), 4)
        
        market_news_sentiment_analyzer.ingest_sentiment_data({
            "source_id": uuid.uuid4().hex,
            "score": sentiment_score,
            "timestamp": time.time()
        })
        
        market_anomaly_detector.configure_threshold({
            "portfolio_id": self.portfolio_id,
            "threshold": anomaly_threshold
        })

        # 2. Trigger portfolio monitoring to register current state
        monitor_status = market_portfolio_monitor.evaluate_portfolio_state({
            "portfolio_id": self.portfolio_id
        })
        self.assertIsNotNone(monitor_status)

        # 3. Execute the target module: market_portfolio_rebalance_engine
        rebalance_job_id = f"job_{uuid.uuid4().hex}"
        rebalance_result = market_portfolio_rebalance_engine.execute_rebalance({
            "job_id": rebalance_job_id,
            "portfolio_id": self.portfolio_id,
            "strategy": "RISK_ADJUSTED_SENTIMENT",
            "force_execution": True
        })

        # 4. Verify real outputs and state changes
        self.assertEqual(rebalance_result.get("status"), "SUCCESS")
        self.assertEqual(rebalance_result.get("job_id"), rebalance_job_id)
        self.assertIn("executed_trades", rebalance_result)
        self.assertIsInstance(rebalance_result["executed_trades"], list)

        # 5. Verify persistence in real DB storage
        stored_portfolio = db_storage.get_portfolio(self.portfolio_id)
        self.assertIsNotNone(stored_portfolio)
        self.assertIn("last_rebalance_timestamp", stored_portfolio)
        self.assertNotEqual(stored_portfolio.get("assets"), {})

        # 6. Check if audit logs or export files were generated as a side effect
        export_path = f"./audit_logs/rebalance_{self.portfolio_id}.json"
        if os.path.exists(export_path):
            self.assertTrue(os.path.getsize(export_path) > 0)
            os.remove(export_path)

if __name__ == "__main__":
    unittest.main()