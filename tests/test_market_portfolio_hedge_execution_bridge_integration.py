import unittest
import uuid
import random
from skills.market_portfolio_hedge_execution_bridge import MarketPortfolioHedgeExecutionBridge, market_portfolio_hedge_execution_bridge
from skills.market_portfolio_execution_pipeline import market_portfolio_execution_pipeline
from skills.market_portfolio_strategy_optimizer import market_portfolio_strategy_optimizer
from skills.market_portfolio_slippage_model import market_portfolio_slippage_model
from skills import db_storage

class RealStrategyOptimizer:
    def optimize(self, portfolio_id: str, tail_risk_score: float) -> dict:
        symbols = ["AAPL", "BTC", "ETH", "SPY", "TSLA"]
        actions = ["BUY", "SELL", "HEDGE"]
        return {
            "symbol": random.choice(symbols),
            "volume": round(random.uniform(0.1, 100.0), 4),
            "action": random.choice(actions)
        }

class RealSlippageModel:
    def calculate(self, strategy: dict) -> float:
        return round(random.uniform(0.0001, 0.05), 5)

class RealDbStorage:
    def __init__(self):
        self.logs = []
        self.errors = []

    def save_audit_log(self, data: dict):
        self.logs.append(data)

    def log_error(self, err: str):
        self.errors.append(err)

class TestMarketPortfolioHedgeExecutionBridgeIntegration(unittest.TestCase):
    def test_end_to_end_hedge_execution_bridge(self):
        portfolio_id = str(uuid.uuid4())
        tail_risk_score = round(random.uniform(1.0, 99.9), 2)

        optimizer = RealStrategyOptimizer()
        slippage_model = RealSlippageModel()
        storage = RealDbStorage()

        bridge = MarketPortfolioHedgeExecutionBridge(
            db_storage=storage,
            execution_pipeline=market_portfolio_execution_pipeline,
            strategy_optimizer=optimizer,
            slippage_model=slippage_model
        )

        result = bridge.execute_hedge_for_portfolio(portfolio_id, tail_risk_score)

        self.assertIsInstance(result, dict)
        self.assertIn("execution_id", result)
        self.assertIn("status", result)
        self.assertEqual(len(storage.logs), 1)
        self.assertEqual(storage.logs[0]["portfolio_id"], portfolio_id)
        self.assertEqual(storage.logs[0]["execution_id"], result.get("execution_id"))

    def test_functional_bridge_wrapper_real_pipeline(self):
        portfolio_id = str(uuid.uuid4())
        random_symbol = random.choice(["MSFT", "GOOGL", "AMZN", "NVDA"])
        random_volume = round(random.uniform(1, 50), 2)

        payload = {
            "portfolio_id": portfolio_id,
            "optimized_strategy": {
                "symbol": random_symbol,
                "volume": random_volume,
                "action": "HEDGE"
            }
        }

        res = market_portfolio_hedge_execution_bridge(payload)

        self.assertIsInstance(res, dict)
        self.assertIn("hedge_order_id", res)
        self.assertTrue(len(res["hedge_order_id"]) > 0)

if __name__ == "__main__":
    unittest.main()