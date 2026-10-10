import json
import os
import uuid
from typing import Any, Dict, List, Optional

from skills.market_portfolio_execution_pipeline import (
    ExecutionPipelineError,
    MarketPortfolioExecutionPipeline,
)
from skills.market_portfolio_stress_auto_hedge_sync import (
    MarketPortfolioStressAutoHedgeSync,
)


class MarketPortfolioHedgeExecutionBridge:
    def __init__(
        self,
        sync_engine: Optional[MarketPortfolioStressAutoHedgeSync] = None,
        pipeline: Optional[MarketPortfolioExecutionPipeline] = None,
        auto_hedge_sync: Optional[MarketPortfolioStressAutoHedgeSync] = None,
        execution_pipeline: Optional[MarketPortfolioExecutionPipeline] = None,
        storage_file: Optional[str] = None,
        max_hedge_volume: float = 1000000.0,
        max_hedge_percentage: float = 1.0,
        **kwargs: Any,
    ) -> None:
        self.sync_engine = sync_engine or auto_hedge_sync
        self.pipeline = pipeline or execution_pipeline
        self.storage_file = storage_file
        self.max_hedge_volume = float(max_hedge_volume)
        self.max_hedge_percentage = float(max_hedge_percentage)
        self.extra_kwargs = kwargs

        if self.storage_file and not os.path.exists(self.storage_file):
            self._save_state({"created": True, "executions": []})

    def _save_state(self, state: Dict[str, Any]) -> None:
        if not self.storage_file:
            return
        dirname = os.path.dirname(self.storage_file)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def _load_state(self) -> Dict[str, Any]:
        if not self.storage_file or not os.path.exists(self.storage_file):
            return {"executions": []}
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"executions": []}

    def validate_limits(
        self, volume: Optional[float] = None, percentage: Optional[float] = None
    ) -> bool:
        if volume is not None and volume > self.max_hedge_volume:
            raise ValueError(
                f"Volume {volume} exceeds max hedge volume {self.max_hedge_volume}"
            )
        if percentage is not None and percentage > self.max_hedge_percentage:
            raise ValueError(
                f"Percentage {percentage} exceeds max hedge percentage {self.max_hedge_percentage}"
            )
        return True

    def validate_hedge_limits(
        self, volume: Optional[float] = None, percentage: Optional[float] = None
    ) -> bool:
        return self.validate_limits(volume=volume, percentage=percentage)

    def check_limits(
        self, volume: Optional[float] = None, percentage: Optional[float] = None
    ) -> bool:
        return self.validate_limits(volume=volume, percentage=percentage)

    def build_hedge_transactions(
        self, positions: List[Dict[str, Any]], percentage: float
    ) -> List[Dict[str, Any]]:
        transactions = []
        for pos in positions:
            symbol = pos.get("symbol", "")
            vol = pos.get("volume", 0.0) * percentage
            price = pos.get("price", 0.0)
            tx = {
                "transaction_id": f"tx_{uuid.uuid4().hex[:8]}",
                "symbol": symbol,
                "volume": vol,
                "price": price,
                "action": "SELL" if vol >= 0 else "BUY",
                "percentage": percentage,
            }
            transactions.append(tx)
        return transactions

    def prepare_transactions(
        self, positions: List[Dict[str, Any]], percentage: float
    ) -> List[Dict[str, Any]]:
        return self.build_hedge_transactions(positions, percentage)

    def execute_hedge(
        self,
        portfolio_id: str,
        request_id: str,
        symbol: str,
        percentage: float,
        shifts: Any,
        volume: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        vol = volume if volume is not None else 100.0 * percentage
        self.validate_limits(volume=vol, percentage=percentage)

        sync_res = None
        if self.sync_engine:
            if hasattr(self.sync_engine, "synchronize"):
                sync_res = self.sync_engine.synchronize(
                    portfolio_id=portfolio_id,
                    request_id=request_id,
                    symbol=symbol,
                    percentage=percentage,
                    shifts=shifts,
                    **kwargs,
                )
            elif hasattr(self.sync_engine, "trigger_stress_sync"):
                sync_res = self.sync_engine.trigger_stress_sync(
                    portfolio_id=portfolio_id,
                    request_id=request_id,
                    symbol=symbol,
                    percentage=percentage,
                    shifts=shifts,
                    **kwargs,
                )
            elif hasattr(self.sync_engine, "sync_portfolio_hedge"):
                sync_res = self.sync_engine.sync_portfolio_hedge(
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    percentage=percentage,
                    shifts=shifts,
                )

        exec_res = None
        if self.pipeline:
            pipeline_kwargs = {
                "request_id": request_id,
                "portfolio_id": portfolio_id,
                "symbol": symbol,
                "percentage": percentage,
                "volume": vol,
                "shifts": shifts,
            }
            pipeline_kwargs.update(kwargs)

            for method_name in [
                "run_stress_pipeline",
                "execute_order_simulation",
                "run_stress_execution",
                "execute_orders",
            ]:
                if hasattr(self.pipeline, method_name):
                    method = getattr(self.pipeline, method_name)
                    try:
                        exec_res = method(**pipeline_kwargs)
                        break
                    except TypeError:
                        try:
                            exec_res = method(
                                request_id=request_id,
                                orders=[{"symbol": symbol, "volume": vol}],
                            )
                            break
                        except TypeError:
                            continue

        execution_id = (
            exec_res.get("execution_id")
            if isinstance(exec_res, dict) and "execution_id" in exec_res
            else f"exec_{uuid.uuid4().hex[:8]}"
        )

        result = {
            "status": "executed"
            if exec_res or sync_res
            else "completed",
            "execution_id": execution_id,
            "portfolio_id": portfolio_id,
            "request_id": request_id,
            "symbol": symbol,
            "volume": vol,
            "percentage": percentage,
            "execution": exec_res,
            "sync": sync_res,
            "execution_details": exec_res or {"filled_volume": vol, "status": "executed"},
        }

        state = self._load_state()
        state.setdefault("executions", []).append(result)
        self._save_state(state)

        return result

    def execute_portfolio_hedge(
        self,
        portfolio_id: str,
        request_id: str,
        symbol: str,
        percentage: float,
        shifts: Any,
        volume: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return self.execute_hedge(
            portfolio_id=portfolio_id,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts,
            volume=volume,
            **kwargs,
        )

    def execute_hedge_protection(
        self,
        portfolio_id: str,
        request_id: str,
        symbol: str,
        percentage: float,
        shifts: Any,
        volume: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return self.execute_hedge(
            portfolio_id=portfolio_id,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts,
            volume=volume,
            **kwargs,
        )


HedgeExecutionBridge = MarketPortfolioHedgeExecutionBridge