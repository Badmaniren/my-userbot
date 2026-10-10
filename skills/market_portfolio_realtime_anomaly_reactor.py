import sys
import io
import os
import json
from typing import Dict, Any, Optional

from skills import market_portfolio_realtime_stream_ingestor
from skills.market_anomaly_detector import MarketAnomalyDetector


class MarketPortfolioRealtimeAnomalyReactor:
    def __init__(self, stream_source: Any = None):
        self.stream_source = stream_source
        self.detector = MarketAnomalyDetector()

    def process_stream_tick(self, context: Any, ticker: str) -> Dict[str, Any]:
        if isinstance(context, str):
            ctx = {"session_id": context, "db_storage": None}
        elif isinstance(context, dict):
            ctx = context
        else:
            ctx = {"session_id": str(context), "db_storage": None}

        ingest_result = market_portfolio_realtime_stream_ingestor.start_new(ctx, self.stream_source)
        detection = self.detector.detect(ticker)

        is_anomaly = detection.get("is_anomaly", False) if isinstance(detection, dict) else False

        return {
            "anomaly_detected": is_anomaly,
            "ticker": ticker,
            "ingest_result": ingest_result,
            "detection": detection
        }

    def evaluate_exchange_feed(self, payload: Dict[str, Any], output_path: str, exchange: str) -> Dict[str, Any]:
        ingest_audit = market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor(payload, output_path)
        anomalies = self.detector.analyze_stream(exchange)

        return {
            "exchange": exchange,
            "anomalies": anomalies,
            "ingest_audit": ingest_audit
        }

    def _process_raw_bytes_stream(self, bio: io.BytesIO) -> bytes:
        return bio.read()


def market_portfolio_realtime_anomaly_reactor(
    context=None,
    stream_source=None,
    payload=None,
    output_path=None,
    exchange=None,
    ticker=None
):
    """
    Модуль интеграции потокового сборщика котировок в реальном времени с детектором
    рыночных аномалий для мгновенной оценки и генерации предупреждений.
    """
    effective_output_path = output_path
    if effective_output_path is None and isinstance(stream_source, str) and (
        stream_source.endswith(".json") or "/" in stream_source or "\\" in stream_source
    ):
        effective_output_path = stream_source

    effective_payload = payload
    if effective_payload is None and isinstance(context, dict):
        effective_payload = context

    # 1. Запуск потокового ингестора
    ingest_res = market_portfolio_realtime_stream_ingestor.start_new(context, stream_source)

    # 2. Детекция аномалий
    detector = MarketAnomalyDetector()

    target_ticker = ticker
    if not target_ticker and isinstance(context, dict):
        target_ticker = context.get("ticker")
    if not target_ticker and isinstance(effective_payload, dict):
        if "ticker" in effective_payload:
            target_ticker = effective_payload["ticker"]
        elif "ingest_data" in effective_payload and isinstance(effective_payload["ingest_data"], dict):
            target_ticker = effective_payload["ingest_data"].get("ticker")

    if not target_ticker:
        target_ticker = "DEFAULT_TICKER"

    detection_res = detector.detect(target_ticker)

    if exchange and hasattr(detector, "analyze_stream"):
        detector.analyze_stream(exchange)

    # 3. Формирование ответа и запись в файл, если требуется
    result = {
        "ingest_result": ingest_res,
        "detection_result": detection_res,
        "payload": effective_payload,
        "status": "success"
    }

    if effective_output_path:
        dir_name = os.path.dirname(os.path.abspath(effective_output_path))
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        session_id_to_write = ""
        if isinstance(effective_payload, dict):
            session_id_to_write = effective_payload.get("session_id", "")
        elif isinstance(context, dict):
            session_id_to_write = context.get("session_id", "")

        report_data = {
            "session_id": session_id_to_write,
            "result": result
        }
        with open(effective_output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f)

    return result


def market_portfolio_realtime_anomaly_reactor_main() -> Dict[str, Any]:
    stream_source = sys.argv[1] if len(sys.argv) > 1 else "default_stream"
    ticker = sys.argv[2] if len(sys.argv) > 2 else "DEFAULT_TICKER"

    reactor = MarketPortfolioRealtimeAnomalyReactor(stream_source=stream_source)
    context = {"session_id": "cli_session", "priority": "NORMAL"}

    result = reactor.process_stream_tick(context, ticker)
    return result


def process_realtime_anomaly_event(payload: Dict[str, Any], output_path: str) -> Dict[str, Any]:
    ticker = payload.get("ticker", "UNKNOWN") if isinstance(payload, dict) else "UNKNOWN"
    exchange = payload.get("exchange", "DEFAULT_EXCHANGE") if isinstance(payload, dict) else "DEFAULT_EXCHANGE"

    ingest_res = market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor(payload, output_path)
    detector = MarketAnomalyDetector()
    detection = detector.detect(ticker)

    if detection is None:
        detection = detector.analyze_stream(exchange)
        is_anomaly = True if detection else False
    else:
        is_anomaly = detection.get("is_anomaly", False) if isinstance(detection, dict) else False

    return {
        "status": "success",
        "anomaly_detected": is_anomaly,
        "ticker": ticker,
        "ingest_result": ingest_res,
        "detection": detection
    }


def reactor_main_pipeline(stream_source: Any, output_path: str) -> Dict[str, Any]:
    ticker = stream_source.get("ticker", "UNKNOWN") if isinstance(stream_source, dict) else "UNKNOWN"
    exchange = stream_source.get("exchange", "DEFAULT_EXCHANGE") if isinstance(stream_source, dict) else "DEFAULT_EXCHANGE"

    payload = {
        "ticker": ticker,
        "exchange": exchange,
        "price": stream_source.get("price", 100.0) if isinstance(stream_source, dict) else 100.0
    }

    ingest_res = market_portfolio_realtime_stream_ingestor.market_portfolio_realtime_stream_ingestor(payload, output_path)
    detector = MarketAnomalyDetector()
    anomalies = detector.analyze_stream(exchange)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"ingest": ingest_res, "anomalies": anomalies}, f)

    return {
        "status": "pipeline_completed",
        "ingest": ingest_res,
        "anomalies": anomalies
    }


if __name__ == "__main__":
    market_portfolio_realtime_anomaly_reactor_main()
