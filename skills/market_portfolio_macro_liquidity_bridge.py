import uuid
import io
import logging

from skills import db_storage
from skills import market_portfolio_liquidity_scenario_analyzer
from skills import market_portfolio_var_liquidity_core

logger = logging.getLogger(__name__)

class MacroLiquidityBridge:
    def __init__(self, db_storage=None, liquidity_analyzer=None):
        self.db_storage = db_storage
        self.liquidity_analyzer = liquidity_analyzer

    def process_macro_event(self, event_id: str, payload: dict) -> dict:
        trace_id = uuid.uuid4().hex

        metric = payload.get("metric")
        value = payload.get("value")
        raw_stream = payload.get("raw_stream")

        stream_data = b""
        if raw_stream and isinstance(raw_stream, io.BytesIO):
            stream_data = raw_stream.read()

        evaluation_result = {"score": 0.0, "status": "processed"}
        if self.liquidity_analyzer and hasattr(self.liquidity_analyzer, "evaluate_liquidity"):
            evaluation_result = self.liquidity_analyzer.evaluate_liquidity(
                event_id=event_id,
                metric=metric,
                value=value,
                stream_size=len(stream_data)
            )

        db_key = None
        if self.db_storage and hasattr(self.db_storage, "store_macro_metric"):
            db_key = self.db_storage.store_macro_metric(
                event_id=event_id,
                metric=metric,
                value=value,
                evaluation=evaluation_result
            )

        return {
            "trace_id": trace_id,
            "event_id": event_id,
            "db_key": db_key,
            "evaluation": evaluation_result
        }