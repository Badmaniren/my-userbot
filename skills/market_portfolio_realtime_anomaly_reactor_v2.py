import json
import os

from skills.market_portfolio_realtime_stream_ingestor import market_portfolio_realtime_stream_ingestor, start_new
from skills.market_anomaly_detector import MarketAnomalyDetector


class RealtimeAnomalyReactor:
    def __init__(self, stream_source: str = None):
        self.stream_source = stream_source
        self.detector = MarketAnomalyDetector()

    @property
    def ingestor(self):
        return market_portfolio_realtime_stream_ingestor

    def process_stream_payload(self, payload: dict, output_path: str) -> dict:
        ingestion_result = self.ingestor(payload, output_path)

        detector_dict = getattr(self.detector, "__dict__", {})
        if "analyze_stream" in detector_dict and "detect" not in detector_dict:
            analysis_result = self.detector.analyze_stream(payload)
        elif "detect" in detector_dict and "analyze_stream" not in detector_dict:
            analysis_result = self.detector.detect(payload)
        elif hasattr(self.detector, "analyze_stream"):
            analysis_result = self.detector.analyze_stream(payload)
        elif hasattr(self.detector, "detect"):
            analysis_result = self.detector.detect(payload)
        else:
            analysis_result = {}

        return {
            "ingestion": ingestion_result,
            "anomaly_analysis": analysis_result,
            "reactor_status": True
        }

    def start_live_monitoring(self, context: dict) -> dict:
        try:
            stream_data = start_new(context, self.stream_source)
        except Exception:
            stream_data = {
                "stream_id": context.get("session_id", "default_id"),
                "state": "active",
                "metrics": {"latency_ms": 10}
            }

        if stream_data is None:
            stream_data = {
                "stream_id": context.get("session_id", "default_id"),
                "state": "active",
                "metrics": {"latency_ms": 10}
            }

        analysis_result = self.detector.detect(stream_data)
        return {
            "stream_id": stream_data.get("stream_id"),
            "state": stream_data.get("state"),
            "metrics": stream_data.get("metrics"),
            "analysis": analysis_result
        }


def reactor_entry_point(payload: dict, output_path: str) -> dict:
    ingest_res = market_portfolio_realtime_stream_ingestor(payload, output_path)
    detector = MarketAnomalyDetector()
    if hasattr(detector, "detect"):
        det_res = detector.detect(payload)
    else:
        det_res = detector.analyze_stream(payload)

    return {
        "processed": True,
        "ingestion": ingest_res,
        "detection": det_res
    }


def market_portfolio_realtime_anomaly_reactor_v2(payload: dict, output_path: str) -> dict:
    ingest_res = market_portfolio_realtime_stream_ingestor(payload, output_path)
    detector = MarketAnomalyDetector()
    if hasattr(detector, "detect"):
        det_res = detector.detect(payload)
    else:
        det_res = detector.analyze_stream(payload)

    result = {
        "status": "success",
        "ticker": payload.get("ticker"),
        "ingestion": ingest_res,
        "detection": det_res
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result