import json
import os

from skills.market_portfolio_realtime_stream_ingestor import market_portfolio_realtime_stream_ingestor, start_new
from skills.market_anomaly_detector import MarketAnomalyDetector


class RealtimeAnomalyReactor:
    def __init__(self, stream_source: str = None):
        self.stream_source = stream_source
        self.ingestor = market_portfolio_realtime_stream_ingestor
        self.detector = MarketAnomalyDetector()

    def process_stream_payload(self, payload: dict, output_path: str) -> dict:
        ingestion_result = self.ingestor(payload, output_path)
        
        if hasattr(self.detector, "analyze_stream"):
            analysis_result = self.detector.analyze_stream(payload)
        else:
            analysis_result = self.detector.detect(payload)

        return {
            "ingestion": ingestion_result,
            "anomaly_analysis": analysis_result,
            "reactor_status": True
        }

    def start_live_monitoring(self, context: dict) -> dict:
        stream_data = start_new(context, self.stream_source)
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