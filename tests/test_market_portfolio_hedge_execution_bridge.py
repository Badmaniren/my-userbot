import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import os
import tempfile
import json
from skills.market_portfolio_hedge_execution_bridge import MarketPortfolioHedgeExecutionBridge

class TestMarketPortfolioHedgeExecutionBridge(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.request_id = f"req_{uuid.uuid4().hex[:8]}"
        self.symbol = f"SYM{random.randint(100, 999)}"
        self.percentage = round(random.uniform(0.1, 0.9), 2)
        self.volume = round(random.uniform(100.0, 5000.0), 2)
        self.max_volume = 10000.0
        self.max_percentage = 1.0

        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_and_state_management(self):
        bridge = MarketPortfolioHedgeExecutionBridge(
            storage_file=self.storage_file,
            max_hedge_volume=self.max_volume,
            max_hedge_percentage=self.max_percentage
        )
        self.assertTrue(os.path.exists(self.storage_file))
        state = bridge._load_state()
        self.assertIn("executions", state)
        self.assertEqual(state.get("created"), True)

    def test_validate_limits_success(self):
        bridge = MarketPortfolioHedgeExecutionBridge(
            max_hedge_volume=self.max_volume,
            max_hedge_percentage=self.max_percentage
        )
        res = bridge.validate_limits(volume=self.volume, percentage=self.percentage)
        self.assertTrue(res)

    def test_validate_limits_volume_exceeded(self):
        bridge = MarketPortfolioHedgeExecutionBridge(
            max_hedge_volume=100.0,
            max_hedge_percentage=self.max_percentage
        )
        with self.assertRaises(ValueError):
            bridge.validate_limits(volume=500.0, percentage=0.5)

    def test_validate_limits_percentage_exceeded(self):
        bridge = MarketPortfolioHedgeExecutionBridge(
            max_hedge_volume=self.max_volume,
            max_hedge_percentage=0.5
        )
        with self.assertRaises(ValueError):
            bridge.validate_limits(volume=50.0, percentage=0.8)

    def test_build_hedge_transactions(self):
        bridge = MarketPortfolioHedgeExecutionBridge()
        pos_symbol = f"TICKER_{uuid.uuid4().hex[:4]}"
        pos_volume = random.randint(10, 1000)
        pos_price = round(random.uniform(10.0, 500.0), 2)
        positions = [
            {"symbol": pos_symbol, "volume": pos_volume, "price": pos_price}
        ]
        percentage = 0.5
        transactions = bridge.build_hedge_transactions(positions, percentage)
        self.assertEqual(len(transactions), 1)
        tx = transactions[0]
        self.assertEqual(tx["symbol"], pos_symbol)
        self.assertEqual(tx["volume"], pos_volume * percentage)
        self.assertEqual(tx["price"], pos_price)
        self.assertEqual(tx["percentage"], percentage)
        self.assertIn("transaction_id", tx)

    def test_execute_hedge_with_sync_and_pipeline(self):
        mock_sync = MagicMock()
        sync_result = {"sync_id": f"sync_{uuid.uuid4().hex[:6]}", "status": "synced"}
        mock_sync.synchronize.return_value = sync_result

        mock_pipeline = MagicMock()
        exec_id = f"exec_{uuid.uuid4().hex[:6]}"
        pipeline_result = {"execution_id": exec_id, "status": "success"}
        mock_pipeline.execute.return_value = pipeline_result

        bridge = MarketPortfolioHedgeExecutionBridge(
            sync_engine=mock_sync,
            pipeline=mock_pipeline,
            storage_file=self.storage_file,
            max_hedge_volume=self.max_volume,
            max_hedge_percentage=self.max_percentage
        )

        shifts_data = {"shift_val": random.random()}
        result = bridge.execute_hedge(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=shifts_data,
            volume=self.volume
        )

        self.assertEqual(result["execution_id"], exec_id)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["request_id"], self.request_id)
        self.assertEqual(result["symbol"], self.symbol)
        self.assertEqual(result["volume"], self.volume)
        self.assertEqual(result["sync"], sync_result)
        self.assertEqual(result["execution"], pipeline_result)

        state = bridge._load_state()
        self.assertEqual(len(state["executions"]), 1)
        self.assertEqual(state["executions"][0]["execution_id"], exec_id)

    def test_execute_portfolio_hedge_delegation(self):
        bridge = MarketPortfolioHedgeExecutionBridge(storage_file=self.storage_file)
        with patch.object(bridge, "execute_hedge", return_value={"mocked": True}) as mock_exec:
            res = bridge.execute_portfolio_hedge(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts={},
                volume=self.volume
            )
            mock_exec.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts={},
                volume=self.volume
            )
            self.assertTrue(res["mocked"])

    def test_execute_hedge_protection_delegation(self):
        bridge = MarketPortfolioHedgeExecutionBridge(storage_file=self.storage_file)
        with patch.object(bridge, "execute_hedge", return_value={"protected": True}) as mock_exec:
            res = bridge.execute_hedge_protection(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts={},
                volume=self.volume
            )
            mock_exec.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts={},
                volume=self.volume
            )
            self.assertTrue(res["protected"])