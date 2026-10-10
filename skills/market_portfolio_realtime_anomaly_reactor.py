import json
import os
from skills import market_portfolio_realtime_stream_ingestor
from skills import market_anomaly_detector

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
    detector = market_anomaly_detector.MarketAnomalyDetector()

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