import unittest
import os
import uuid
import random
from skills.market_portfolio_hedge_execution_bridge import MarketPortfolioHedgeExecutionBridge
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline

class TestMarketPortfolioHedgeExecutionBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_hedge_state_{uuid.uuid4().hex[:8]}.json"
        self.sync_engine = MarketPortfolioStressAutoHedgeSync()
        self.pipeline = MarketPortfolioExecutionPipeline()
        self.bridge = MarketPortfolioHedgeExecutionBridge(
            sync_engine=self.sync_engine,
            pipeline=self.pipeline,
            storage_file=self.storage_file,
            max_hedge_volume=500000.0,
            max_hedge_percentage=0.8
        )

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_integration_execute_hedge_success(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        symbol = random.choice(["BTCUSD", "ETHUSD", "EURUSD", "AAPL"])
        percentage = round(random.uniform(0.1, 0.7), 2)
        volume = round(random.uniform(1000.0, 100000.0), 2)
        shifts = {"market_shift": random.choice([-0.05, -0.1, -0.15])}

        result = self.bridge.execute_hedge(
            portfolio_id=portfolio_id,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts,
            volume=volume
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("request_id"), request_id)
        self.assertEqual(result.get("symbol"), symbol)
        self.assertEqual(result.get("volume"), volume)
        self.assertEqual(result.get("percentage"), percentage)
        self.assertIn("execution_id", result)

        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r", encoding="utf-8") as f:
            state_data = json.load(f)
            self.assertIn("executions", state_data)
            self.assertTrue(len(state_data["executions"]) > 0)
            last_exec = state_data["executions"][-1]
            self.assertEqual(last_exec.get("request_id"), request_id)

    def test_integration_validate_limits_exceeded(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        symbol = "BTCUSD"
        percentage = 0.9  
        volume = 600000.0 
        shifts = {"drop": -0.2}

        with self.assertRaises(ValueError):
            self.bridge.validate_limits(volume=volume, percentage=percentage)

        with self.assertRaises(ValueError):
            self.bridge.execute_hedge(
                portfolio_id=portfolio_id,
                request_id=request_id,
                symbol=symbol,
                percentage=percentage,
                shifts=shifts,
                volume=volume
            )

    def test_integration_build_hedge_transactions(self):
        num_positions = random.randint(1, 5)
        positions = []
        for _ in range(num_positions):
            positions.append({
                "symbol": f"SYM_{uuid.uuid4().hex[:4]}",
                "volume": random.uniform(100.0, 10000.0),
                "price": random.uniform(10.0, 500.0)
            })
        percentage = round(random.uniform(0.1, 0.5), 2)

        transactions = self.bridge.build_hedge_transactions(positions, percentage)
        self.assertIsInstance(transactions, list)
        self.assertEqual(len(transactions), len(positions))
        for tx in transactions:
            self.assertIn("transaction_id", tx)
            self.assertIn("symbol", tx)
            self.assertIn("volume", tx)
            self.assertIn("price", tx)
            self.assertIn("action", tx)
            self.assertEqual(tx["percentage"], percentage)