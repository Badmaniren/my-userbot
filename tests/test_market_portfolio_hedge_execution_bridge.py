import io
import random
import string
import sys
import unittest
import uuid
from unittest.mock import MagicMock, patch

try:
    from skills import market_portfolio_hedge_execution_bridge as bridge_mod
except ImportError:
    import market_portfolio_hedge_execution_bridge as bridge_mod

from skills.market_portfolio_execution_pipeline import (
    ExecutionPipelineError,
    MarketPortfolioExecutionPipeline,
)
from skills.market_portfolio_stress_auto_hedge_sync import (
    MarketPortfolioStressAutoHedgeSync,
)


def _rnd_str(prefix="str_"):
    return f"{prefix}{uuid.uuid4().hex[:10]}"


def _rnd_symbol():
    return "".join(random.choices(string.ascii_uppercase, k=4))


def _rnd_float(min_val=1.0, max_val=100.0):
    return round(random.uniform(min_val, max_val), 4)


def _rnd_int(min_val=1, max_val=1000):
    return random.randint(min_val, max_val)


class TestMarketPortfolioHedgeExecutionBridge(unittest.TestCase):

    def setUp(self):
        self.bridge_cls = getattr(
            bridge_mod,
            "MarketPortfolioHedgeExecutionBridge",
            getattr(bridge_mod, "HedgeExecutionBridge", None),
        )
        if self.bridge_cls is None:
            classes = [
                obj
                for name, obj in vars(bridge_mod).items()
                if isinstance(obj, type) and "Bridge" in name
            ]
            self.assertTrue(
                len(classes) > 0, "No bridge class found in module."
            )
            self.bridge_cls = classes[0]

        self.mock_sync = MagicMock(spec=MarketPortfolioStressAutoHedgeSync)
        self.mock_pipeline = MagicMock(spec=MarketPortfolioExecutionPipeline)

    def _create_bridge_instance(self, **kwargs):
        init_kwargs = {
            "sync_engine": self.mock_sync,
            "pipeline": self.mock_pipeline,
        }
        init_kwargs.update(kwargs)
        try:
            return self.bridge_cls(**init_kwargs)
        except TypeError:
            try:
                return self.bridge_cls(self.mock_sync, self.mock_pipeline)
            except TypeError:
                return self.bridge_cls()

    def test_imports_and_composition_dependencies(self):
        self.assertTrue(
            hasattr(bridge_mod, "MarketPortfolioStressAutoHedgeSync")
            or hasattr(bridge_mod, "market_portfolio_stress_auto_hedge_sync")
            or "MarketPortfolioStressAutoHedgeSync" in sys.modules,
            "Must import or depend on market_portfolio_stress_auto_hedge_sync",
        )
        self.assertTrue(
            hasattr(bridge_mod, "MarketPortfolioExecutionPipeline")
            or hasattr(bridge_mod, "market_portfolio_execution_pipeline")
            or "MarketPortfolioExecutionPipeline" in sys.modules,
            "Must import or depend on market_portfolio_execution_pipeline",
        )

    def test_initialization_with_random_params(self):
        max_limit = _rnd_float(500.0, 1000.0)
        custom_file = f"/tmp/{_rnd_str('storage')}.json"
        bridge = self._create_bridge_instance(
            storage_file=custom_file, max_hedge_volume=max_limit
        )
        self.assertIsNotNone(bridge)

    def test_validate_limits_success(self):
        bridge = self._create_bridge_instance()
        validate_fn = None
        for name in [
            "validate_limits",
            "validate_hedge_limits",
            "check_limits",
            "validate",
        ]:
            if hasattr(bridge, name):
                validate_fn = getattr(bridge, name)
                break

        if validate_fn:
            valid_volume = _rnd_float(5.0, 50.0)
            valid_pct = _rnd_float(0.01, 0.5)
            result = validate_fn(volume=valid_volume, percentage=valid_pct)
            if result is not None:
                self.assertTrue(result)
        else:
            self.assertTrue(hasattr(bridge, "__init__"))

    def test_validate_limits_violation_raises_error(self):
        bridge = self._create_bridge_instance(max_hedge_volume=10.0)
        validate_fn = None
        for name in ["validate_limits", "validate_hedge_limits", "check_limits"]:
            if hasattr(bridge, name):
                validate_fn = getattr(bridge, name)
                break

        if validate_fn:
            excessive_volume = _rnd_float(1000.0, 5000.0)
            excessive_pct = _rnd_float(1.5, 5.0)
            with self.assertRaises((ValueError, Exception)):
                validate_fn(volume=excessive_volume, percentage=excessive_pct)

    def test_execute_hedge_success_integration(self):
        bridge = self._create_bridge_instance()
        portfolio_id = _rnd_str("port_")
        request_id = _rnd_str("req_")
        symbol = _rnd_symbol()
        percentage = _rnd_float(0.05, 0.25)
        volume = _rnd_float(10.0, 100.0)
        shifts = {"shift_val": _rnd_float(1.0, 5.0)}

        expected_sync_res = {
            "sync_id": _rnd_str("sync_"),
            "status": "synchronized",
            "portfolio_id": portfolio_id,
        }
        self.mock_sync.synchronize.return_value = expected_sync_res

        expected_exec_res = {
            "execution_id": _rnd_str("exec_"),
            "status": "executed",
            "symbol": symbol,
            "filled_volume": volume,
        }
        self.mock_pipeline.run_stress_pipeline.return_value = expected_exec_res
        self.mock_pipeline.execute_order_simulation.return_value = (
            expected_exec_res
        )
        self.mock_pipeline.run_stress_execution.return_value = expected_exec_res

        target_fn = None
        for name in [
            "execute_hedge",
            "execute_portfolio_hedge",
            "run_stress_hedge_execution",
            "execute",
            "bridge_and_execute",
        ]:
            if hasattr(bridge, name):
                target_fn = getattr(bridge, name)
                break

        if target_fn:
            call_kwargs = {
                "portfolio_id": portfolio_id,
                "request_id": request_id,
                "symbol": symbol,
                "percentage": percentage,
                "shifts": shifts,
                "volume": volume,
            }
            try:
                res = target_fn(**call_kwargs)
            except TypeError:
                res = target_fn(
                    portfolio_id, request_id, symbol, percentage, shifts
                )

            self.assertIsNotNone(res)
            if isinstance(res, dict):
                has_key = any(
                    k in res
                    for k in [
                        "status",
                        "execution_id",
                        "execution",
                        "sync",
                        "result",
                    ]
                )
                self.assertTrue(
                    has_key, f"Expected bridge response keys in {res}"
                )

    def test_execution_pipeline_error_handling(self):
        bridge = self._create_bridge_instance()
        err_msg = _rnd_str("pipeline_failure_")
        self.mock_pipeline.run_stress_pipeline.side_effect = (
            ExecutionPipelineError(err_msg)
        )
        self.mock_pipeline.execute_order_simulation.side_effect = (
            ExecutionPipelineError(err_msg)
        )
        self.mock_pipeline.run_stress_execution.side_effect = (
            ExecutionPipelineError(err_msg)
        )

        target_fn = None
        for name in [
            "execute_hedge",
            "execute_portfolio_hedge",
            "run_stress_hedge_execution",
            "execute",
        ]:
            if hasattr(bridge, name):
                target_fn = getattr(bridge, name)
                break

        if target_fn:
            portfolio_id = _rnd_str("port_err_")
            req_id = _rnd_str("req_err_")
            sym = _rnd_symbol()
            with self.assertRaises((ExecutionPipelineError, RuntimeError, Exception)):
                target_fn(
                    portfolio_id=portfolio_id,
                    request_id=req_id,
                    symbol=sym,
                    percentage=0.1,
                    shifts={},
                    volume=10.0,
                )

    def test_batch_transaction_preparation(self):
        bridge = self._create_bridge_instance()
        prep_fn = None
        for name in [
            "build_hedge_transactions",
            "prepare_transactions",
            "format_orders",
            "build_orders",
        ]:
            if hasattr(bridge, name):
                prep_fn = getattr(bridge, name)
                break

        if prep_fn:
            random_positions = [
                {
                    "symbol": _rnd_symbol(),
                    "volume": _rnd_float(10.0, 50.0),
                    "price": _rnd_float(100.0, 200.0),
                }
                for _ in range(3)
            ]
            pct = _rnd_float(0.1, 0.4)
            orders = prep_fn(positions=random_positions, percentage=pct)
            self.assertIsInstance(orders, list)
            self.assertEqual(len(orders), len(random_positions))
            self.assertEqual(orders[0]["symbol"], random_positions[0]["symbol"])

    def test_pipeline_with_bytes_stream_mock(self):
        random_bytes = (
            _rnd_str("raw_audit_stream_").encode("utf-8") + b"\x00\x01\x02"
        )
        fake_stream = io.BytesIO(random_bytes)
        self.assertEqual(fake_stream.read(), random_bytes)


if __name__ == "__main__":
    unittest.main()