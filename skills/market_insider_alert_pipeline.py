from skills.market_insider_activity_tracker import MarketInsiderActivityTracker, DBStorage
from skills.market_anomaly_detector import MarketAnomalyDetector
import uuid
import io


class MarketInsiderAlertPipeline:
    def __init__(self):
        self.tracker = MarketInsiderActivityTracker()
        self.detector = MarketAnomalyDetector()

    def process_alert_stream(self, ticker, raw_stream_data):
        activity_result = self.tracker.analyze_activity(raw_stream_data)
        
        if activity_result.get("status") != "suspicious":
            return None

        anomaly_result = self.detector.detect(ticker)

        if anomaly_result and anomaly_result.get("is_anomaly"):
            alert = {
                "ticker": activity_result.get("ticker", ticker),
                "signature": activity_result.get("signature"),
                "is_anomaly": anomaly_result.get("is_anomaly"),
                "anomaly_score": anomaly_result.get("anomaly_score")
            }
            return alert
        return None

    def evaluate_market_stream(self, exchange):
        return self.detector.analyze_stream(exchange)


def market_insider_alert_pipeline(raw_data=None, *args, **kwargs):
    if raw_data is None:
        return []
    if isinstance(raw_data, list):
        alerts = []
        for item in raw_data:
            if isinstance(item, dict):
                vol = item.get("volume", 0)
                is_anomaly = item.get("insider_flag", False) or vol > 50000
                alerts.append({
                    "alert_id": uuid.uuid4().hex,
                    "ticker": item.get("ticker"),
                    "volume": vol,
                    "is_anomaly": is_anomaly,
                    "timestamp": item.get("timestamp")
                })
        return alerts
    elif isinstance(raw_data, dict):
        ticker = raw_data.get("ticker")
        if "stream" in raw_data and raw_data["stream"] is not None:
            stream_arg = raw_data["stream"]
        else:
            stream_arg = io.BytesIO(str(raw_data).encode('utf-8'))
        tracker = MarketInsiderActivityTracker()
        detector = MarketAnomalyDetector()
        analysis_result = tracker.analyze_activity(stream_arg)
        anomaly_result = detector.detect(ticker)
        return {
            "alert_id": uuid.uuid4().hex,
            "ticker": ticker,
            "signature": raw_data.get("signature"),
            "analysis": analysis_result,
            "anomaly": anomaly_result
        }
    else:
        tracker = MarketInsiderActivityTracker()
        detector = MarketAnomalyDetector()
        analysis_result = tracker.analyze_activity(raw_data)
        anomaly_result = detector.detect(None)
        return {
            "alert_id": uuid.uuid4().hex,
            "ticker": None,
            "signature": None,
            "analysis": analysis_result,
            "anomaly": anomaly_result
        }
