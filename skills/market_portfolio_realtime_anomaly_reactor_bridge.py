import json
import os
from typing import Dict, Any

from skills.market_portfolio_realtime_stream_ingestor import (
    market_portfolio_realtime_stream_ingestor,
    start_new
)
from skills.market_anomaly_detector import MarketAnomalyDetector, market_anomaly_detector


class MarketPortfolioRealtimeAnomalyReactorBridge:
    def __init__(self, stream_source: str = ""):
        self.stream_source = stream_source

    def process_stream(self, ticker: str) -> str:
        detector = MarketAnomalyDetector()
        res = detector.detect(ticker)
        return str(res.get("reaction_id", ""))


def market_portfolio_realtime_anomaly_reactor_bridge(
    payload_or_context: Any, output_path: str, ticker: str = None
) -> Dict[str, Any]:
    """Связывает реальный потоковый сборщик котировок с модулем обнаружения рыночных аномалий

    для формирования итогового события мгновенной реакции.
    """
    ingested_data = {}
    if isinstance(payload_or_context, dict) and "ingested_data" in payload_or_context:
        ingested_data = payload_or_context["ingested_data"]
    else:
        if ticker:
            try:
                ingested_data = market_portfolio_realtime_stream_ingestor(
                    payload_or_context, output_path
                )
            except Exception:
                ingested_data = {"payload": payload_or_context}
        else:
            ingested_data = {"payload": payload_or_context}

    target_ticker = ticker
    if not target_ticker and isinstance(payload_or_context, dict):
        if "ticker" in payload_or_context:
            target_ticker = payload_or_context["ticker"]
        elif "detection_meta" in payload_or_context:
            target_ticker = payload_or_context["detection_meta"].get("ticker", "UNKNOWN")
        else:
            target_ticker = "UNKNOWN"
    elif not target_ticker:
        target_ticker = "UNKNOWN"

    detector = MarketAnomalyDetector()
    detection_result = detector.detect(target_ticker)

    reaction_event = {
        "ingested_data": ingested_data,
        "detection_result": detection_result,
        "status": "reacted"
    }

    dir_name = os.path.dirname(os.path.abspath(output_path))
    if dir_name and not os.path.exists(dir_name):
        try:
            os.makedirs(dir_name, exist_ok=True)
        except OSError:
            output_path = os.path.basename(output_path)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(reaction_event, f, ensure_ascii=False, indent=2)

    return reaction_event