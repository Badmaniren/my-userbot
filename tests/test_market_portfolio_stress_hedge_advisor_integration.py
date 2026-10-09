import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_hedge_advisor import MarketPortfolioStressHedgeAdvisor

class RealMemoryDB:
    def __init__(self):
        self.storage = {}
    def save_record(self, key, value):
        self.storage[key] = value

class RealMonitor:
    def __init__(self, drawdown, volatility):
        self.drawdown = drawdown
        self.volatility = volatility
    def get_portfolio_state(self, portfolio_id):
        return {"drawdown": self.drawdown, "volatility": self.volatility}

class RealEvaluator:
    def evaluate(self, state):
        return {"status": "ok"}

class RealRebalancer:
    def __init__(self):
        self.statuses = {}
    def set_trigger_status(self, portfolio_id, status_data):
        self.statuses[portfolio_id] = status_data

class TestMarketPortfolioStressHedgeAdvisorIntegration(unittest.TestCase):
    def test_stress_hedge_advisor_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        
        drawdown = round(random.uniform(0.12, 0.25), 2)
        volatility = round(random.uniform(16.0, 30.0), 2)
        
        db = RealMemoryDB()
        monitor = RealMonitor(drawdown=drawdown, volatility=volatility)
        evaluator = RealEvaluator()
        rebalancer = RealRebalancer()
        
        advisor = MarketPortfolioStressHedgeAdvisor(
            db_storage=db,
            monitor=monitor,
            evaluator=evaluator,
            rebalancer=rebalancer
        )
        
        result = advisor.analyze_and_recommend(portfolio_id, request_id)
        
        self.assertTrue(result.get("hedge_recommended"))
        rec_id = result.get("recommendation_id")
        self.assertIsNotNone(rec_id)
        
        self.assertIn(portfolio_id, db.storage)
        self.assertEqual(db.storage[portfolio_id]["last_stress_event_id"], rec_id)
        self.assertEqual(db.storage[portfolio_id]["drawdown"], drawdown)
        
        self.assertIn(portfolio_id, rebalancer.statuses)
        self.assertEqual(rebalancer.statuses[portfolio_id]["action"], "HEDGE_REQUIRED")
        self.assertEqual(rebalancer.statuses[portfolio_id]["recommendation_id"], rec_id)
        
        log_path = f"stress_audit_{portfolio_id}.log"
        self.assertTrue(os.path.exists(log_path))
        
        with open(log_path, "r") as f:
            content = f.read()
            self.assertIn(portfolio_id, content)
            self.assertIn(rec_id, content)
            
        if os.path.exists(log_path):
            os.remove(log_path)

if __name__ == "__main__":
    unittest.main()