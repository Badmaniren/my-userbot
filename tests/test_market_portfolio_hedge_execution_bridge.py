import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import os
import tempfile

from skills.market_portfolio_hedge_execution_bridge import (
    MarketPortfolioHedgeExecutionBridge,
    HedgeExecutionBridge,
)


class TestMarketPortfolioHedgeExecutionBridge(unittest.TestCase):

    def setUp(self) -> None:
        self.max_volume = float(random.randint(10000, 500000))
        self.max_pct = round(random.uniform(0.5, 1.0), 2)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"{uuid.uuid4().hex}.json")

        self.bridge = MarketPortfolioHedgeExecutionBridge(
            max_hedge_volume=self.max_volume,
            max_hedge_percentage=self.max_pct,
            storage_file=self.storage_file
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_initialization_and_aliases(self) -> None:
        self.assertIsInstance(self.bridge, HedgeExecutionBridge)
        self.assertEqual(self.bridge.max_hedge_volume, self.max_volume)
        self.assertEqual(self.bridge.max_hedge_percentage, self.max_pct)
        self.assertTrue(os.path.exists(self.storage_file))

    def test_validate_limits_success(self) -> None:
        test_vol = self.max_volume - float(random.randint(1, 1000))
        test_pct = self.max_pct - 0.1
        res = self.bridge.validate_limits(volume=test_vol, percentage=test_pct)
        self.assertTrue(res)

        res_aliases = self.bridge.validate_hedge_limits(volume=test_vol, percentage=test_pct)
        self.assertTrue(res_aliases)

        res_check = self.bridge.check_limits(volume=test_vol, percentage=test_pct)
        self.assertTrue(res_check)

    def test_validate_limits_volume_exception(self) -> None:
        test_vol = self.max_volume + float(random.randint(1, 10000))
        with self.assertRaises(ValueError):
            self.bridge.validate_limits(volume=test_vol)

    def test_validate_limits_percentage_exception(self) -> None:
        test_pct = self.bridge.max_hedge_percentage + round(random.uniform(0.01, 0.5), 2)
        with self.assertRaises(ValueError):
            self.bridge.validate_limits(percentage=test_pct)

    def test_build_hedge_transactions(self) -> None:
        symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        volume = float(random.randint(100, 1000))
        price = round(random.uniform(10.0, 500.0), 2)
        percentage = round(random.uniform(0.1, 1.0), 2)

        positions = [{"symbol": symbol, "volume": volume, "price": price}]
        transactions = self.bridge.build_hedge_transactions(positions, percentage)

        self.assertEqual(len(transactions), 1)
        tx = transactions[0]
        self.assertEqual(tx["symbol"], symbol)
        self.assertEqual(tx["volume"], volume * percentage)
        self.assertEqual(tx["price"], price)
        self.assertEqual(tx["percentage"], percentage)
        self.assertIn("transaction_id", tx)

        prep_tx = self.bridge.prepare_transactions(positions, percentage)
        self.assertEqual(prep_tx, transactions)

    def test_execute_hedge_with_sync_and_pipeline(self) -> None:
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        symbol = f"ASSET_{uuid.uuid4().hex[:4]}"
        percentage = round(random.uniform(0.1, 0.5), 2)
        shifts = {"shift": random.random()}
        volume = float(random.randint(100, 5000))

        mock_sync = MagicMock()
        mock_sync.synchronize.return_value = {"sync_status": "ok", "id": uuid.uuid4().hex}

        mock_pipeline = MagicMock()
        exec_id = f"exec_{uuid.uuid4().hex[:8]}"
        mock_pipeline.execute.return_value = {"execution_id": exec_id, "status": "executed"}

        bridge = MarketPortfolioHedgeExecutionBridge(
            sync_engine=mock_sync,
            pipeline=mock_pipeline,
            max_hedge_volume=self.max_volume,
            max_hedge_percentage=self.max_pct,
            storage_file=self.storage_file
        )

        result = bridge.execute_hedge(
            portfolio_id=portfolio_id,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts,
            volume=volume
        )

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["request_id"], request_id)
        self.assertEqual(result["symbol"], symbol)
        self.assertEqual(result["volume"], volume)
        self.assertEqual(result["execution_id"], exec_id)
        self.assertEqual(result["status"], "executed")
        self.assertIsNotNone(result["sync"])
        self.assertIsNotNone(result["execution"])

    def test_execute_portfolio_hedge_and_protection_aliases(self) -> None:
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        symbol = f"SYM_{uuid.uuid4().hex[:4]}"
        percentage = 0.2
        shifts = {}
        volume = 500.0

        with patch.object(self.bridge, "execute_hedge", return_value={"status": "executed", "portfolio_id": portfolio_id}) as mock_exec:
            res1 = self.bridge.execute_portfolio_hedge(
                portfolio_id=portfolio_id,
                request_id=request_id,
                symbol=symbol,
                percentage=percentage,
                shifts=shifts,
                volume=volume
            )
            mock_exec.assert_called_once()
            self.assertEqual(res1["portfolio_id"], portfolio_id)

        with patch.object(self.bridge, "execute_hedge", return_value={"status": "executed", "portfolio_id": portfolio_id}) as mock_exec:
            res2 = self.bridge.execute_hedge_protection(
                portfolio_id=portfolio_id,
                request_id=request_id,
                symbol=symbol,
                percentage=percentage,
                shifts=shifts,
                volume=volume
            )
            mock_exec.assert_called_once()
            self.assertEqual(res2["portfolio_id"], portfolio_id)

    def test_load_state_corrupted_file(self) -> None:
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{invalid_json")

        state = self.bridge._load_state()
        self.assertEqual(state, {"executions": []})

    def test_pipeline_fallback_execution(self) -> None:
        target_mock = MagicMock(spec=[])
        bridge = MarketPortfolioHedgeExecutionBridge(
            pipeline=target_mock,
            storage_file=self.storage_file
        )
        kwargs = {"custom_arg": uuid.uuid4().hex}
        res = bridge._run_pipeline_fallback(**kwargs)
        self.assertEqual(res["status"], "executed")
        self.assertIn("execution_id", res)
        self.assertEqual(res["details"], kwargs)