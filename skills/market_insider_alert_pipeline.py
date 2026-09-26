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
        anomaly_result = self.detector.detect(ticker)

        if activity_result.get("status") == "suspicious" and anomaly_result.get("is_anomaly"):
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


def market_insider_alert_pipeline(raw_data):
    tracker = MarketInsiderActivityTracker()
    detector = MarketAnomalyDetector()
    
    ticker = raw_data.get("ticker")
    
    # Ensure raw_data can be handled whether it's a dict or a stream
    if isinstance(raw_data, dict):
        stream_arg = io.BytesIO(str(raw_data).encode('utf-8'))
    else:
        stream_arg = raw_data
        
    analysis_result = tracker.analyze_activity(stream_arg)
    anomaly_result = detector.detect(ticker)
    
    alert_result = {
        "alert_id": uuid.uuid4().hex,
        "ticker": ticker,
        "signature": raw_data.get("signature") if isinstance(raw_data, dict) else None,
        "analysis": analysis_result,
        "anomaly": anomaly_result
    }
    return alert_result