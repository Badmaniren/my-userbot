import json
import os
import random
import tempfile
import unittest
import uuid

from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline
from skills.market_portfolio_hedge_execution_bridge import (
    HedgeExecutionBridge,
    MarketPortfolioHedgeExecutionBridge,
)
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync


class TestMarketPortfolioHedgeExecutionBridgeIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(
            self.temp_dir.name, f"state_{uuid.uuid4().hex[:8]}.json"
        )
        try:
            self.real_pipeline = MarketPortfolioExecutionPipeline()
        except Exception:
            self.real_pipeline = None

        try:
            self.real_sync_engine = MarketPortfolioStressAutoHedgeSync()
        except Exception:
            self.real_sync_engine = None

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_bridge_initialization_and_storage_creation(self) -> None:
        max_vol = random.uniform(50000.0, 200000.0)
        max_pct = random.uniform(0.5, 0.95)

        bridge = MarketPortfolioHedgeExecutionBridge(
            pipeline=self.real_pipeline,
            sync_engine=self.real_sync_engine,
            storage_file=self.storage_file,
            max_hedge_volume=max_vol,
            max_hedge_percentage=max_pct,
        )

        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertTrue(data.get("created", False))
        self.assertEqual(data.get("executions"), [])
        self.assertEqual(bridge.max_hedge_volume, max_vol)
        self.assertEqual(bridge.max_hedge_percentage, max_pct)

    def test_limit_validation(self) -> None:
        max_vol = 1000.0
        max_pct = 0.5
        bridge = MarketPortfolioHedgeExecutionBridge(
            storage_file=self.storage_file,
            max_hedge_volume=max_vol,
            max_hedge_percentage=max_pct,
        )

        self.assertTrue(bridge.validate_limits(volume=max_vol - 1.0, percentage=max_pct - 0.05))
        self.assertTrue(bridge.check_limits(volume=max_vol, percentage=max_pct))
        self.assertTrue(bridge.validate_hedge_limits(volume=500.0, percentage=0.2))

        with self.assertRaises(ValueError):
            bridge.validate_limits(volume=max_vol + random.uniform(1.0, 50.0))

        with self.assertRaises(ValueError):
            bridge.validate_limits(percentage=max_pct + random.uniform(0.01, 0.2))

    def test_build_hedge_transactions_logic(self) -> None:
        bridge = MarketPortfolioHedgeExecutionBridge(storage_file=self.storage_file)

        sym_long = f"ASSET_{uuid.uuid4().hex[:4].upper()}"
        sym_short = f"ASSET_{uuid.uuid4().hex[:4].upper()}"
        vol_long = random.uniform(50.0, 200.0)
        vol_short = -random.uniform(50.0, 200.0)
        price_long = round(random.uniform(10.0, 300.0), 2)
        price_short = round(random.uniform(10.0, 300.0), 2)
        pct = random.uniform(0.1, 0.8)

        positions = [
            {"symbol": sym_long, "volume": vol_long, "price": price_long},
            {"symbol": sym_short, "volume": vol_short, "price": price_short},
        ]

        txs = bridge.build_hedge_transactions(positions, percentage=pct)
        self.assertEqual(len(txs), 2)

        self.assertEqual(txs[0]["symbol"], sym_long)
        self.assertAlmostEqual(txs[0]["volume"], vol_long * pct, places=5)
        self.assertEqual(txs[0]["price"], price_long)
        self.assertEqual(txs[0]["action"], "SELL")
        self.assertTrue(txs[0]["transaction_id"].startswith("tx_"))

        self.assertEqual(txs[1]["symbol"], sym_short)
        self.assertAlmostEqual(txs[1]["volume"], vol_short * pct, places=5)
        self.assertEqual(txs[1]["price"], price_short)
        self.assertEqual(txs[1]["action"], "BUY")

        txs_alias = bridge.prepare_transactions(positions, percentage=pct)
        self.assertEqual(len(txs_alias), 2)
        self.assertEqual(txs_alias[0]["symbol"], sym_long)

    def test_execute_hedge_integration_flow_and_state_persistence(self) -> None:
        bridge = MarketPortfolioHedgeExecutionBridge(
            pipeline=self.real_pipeline,
            sync_engine=self.real_sync_engine,
            storage_file=self.storage_file,
            max_hedge_volume=5000000.0,
            max_hedge_percentage=1.0,
        )

        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        request_id_1 = f"req_{uuid.uuid4().hex[:8]}"
        symbol_1 = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        percentage_1 = round(random.uniform(0.15, 0.45), 4)
        shifts_1 = {"volatility": round(random.uniform(0.05, 0.25), 2)}
        volume_1 = round(random.uniform(100.0, 5000.0), 2)

        result_1 = bridge.execute_hedge(
            portfolio_id=portfolio_id,
            request_id=request_id_1,
            symbol=symbol_1,
            percentage=percentage_1,
            shifts=shifts_1,
            volume=volume_1,
        )

        self.assertIn("status", result_1)
        self.assertIn(result_1["status"], ("executed", "completed"))
        self.assertEqual(result_1["portfolio_id"], portfolio_id)
        self.assertEqual(result_1["request_id"], request_id_1)
        self.assertEqual(result_1["symbol"], symbol_1)
        self.assertAlmostEqual(result_1["volume"], volume_1, places=2)
        self.assertAlmostEqual(result_1["percentage"], percentage_1, places=4)
        self.assertTrue(bool(result_1.get("execution_id")))

        request_id_2 = f"req_{uuid.uuid4().hex[:8]}"
        symbol_2 = f"SYM_{uuid.uuid4().hex[:4].upper()}"
        percentage_2 = round(random.uniform(0.1, 0.3), 4)
        volume_2 = round(random.uniform(50.0, 1000.0), 2)

        result_2 = bridge.execute_portfolio_hedge(
            portfolio_id=portfolio_id,
            request_id=request_id_2,
            symbol=symbol_2,
            percentage=percentage_2,
            shifts={},
            volume=volume_2,
        )

        self.assertEqual(result_2["portfolio_id"], portfolio_id)
        self.assertEqual(result_2["request_id"], request_id_2)
        self.assertEqual(result_2["symbol"], symbol_2)

        with open(self.storage_file, "r", encoding="utf-8") as f:
            persisted_state = json.load(f)

        executions = persisted_state.get("executions", [])
        self.assertEqual(len(executions), 2)
        self.assertEqual(executions[0]["request_id"], request_id_1)
        self.assertEqual(executions[0]["symbol"], symbol_1)
        self.assertEqual(executions[1]["request_id"], request_id_2)
        self.assertEqual(executions[1]["symbol"], symbol_2)

    def test_alias_compatibility_and_protection_call(self) -> None:
        self.assertIs(HedgeExecutionBridge, MarketPortfolioHedgeExecutionBridge)

        bridge = HedgeExecutionBridge(
            pipeline=self.real_pipeline,
            storage_file=self.storage_file,
        )

        portfolio_id = f"port_alias_{uuid.uuid4().hex[:6]}"
        request_id = f"req_alias_{uuid.uuid4().hex[:6]}"
        symbol = f"TICKER_{uuid.uuid4().hex[:4].upper()}"
        percentage = 0.25

        res = bridge.execute_hedge_protection(
            portfolio_id=portfolio_id,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts={"stress": 1.5},
        )

        self.assertEqual(res["portfolio_id"], portfolio_id)
        self.assertEqual(res["request_id"], request_id)
        self.assertEqual(res["symbol"], symbol)
        self.assertAlmostEqual(res["percentage"], percentage, places=4)
        self.assertAlmostEqual(res["volume"], 100.0 * percentage, places=4)


if __name__ == "__main__":
    unittest.main()