from skills.market_anomaly_detector import MarketAnomalyDetector
from skills.market_insider_alert_pipeline import MarketInsiderAlertPipeline
import uuid
import json
import io


class MarketInsiderAnomalyAnalyzer:
    def __init__(self, anomaly_detector=None, alert_pipeline=None):
        self.anomaly_detector = anomaly_detector if anomaly_detector is not None else MarketAnomalyDetector()
        self.alert_pipeline = alert_pipeline if alert_pipeline is not None else MarketInsiderAlertPipeline()

    def analyze_ticker(self, ticker, stream_data=None):
        anomaly_res = {}
        if hasattr(self.anomaly_detector, "detect"):
            detected = False
            if stream_data is not None:
                try:
                    anomaly_res = self.anomaly_detector.detect(ticker, stream_data)
                    detected = True
                except TypeError:
                    pass
            if not detected:
                try:
                    anomaly_res = self.anomaly_detector.detect(ticker)
                except TypeError:
                    try:
                        anomaly_res = self.anomaly_detector.detect(stream_data)
                    except TypeError:
                        anomaly_res = {"ticker": ticker, "has_anomaly": False, "score": 0.0}
        else:
            anomaly_res = {"ticker": ticker, "has_anomaly": False, "score": 0.0}

        pipeline_res = {}
        if hasattr(self.alert_pipeline, "process_alert_stream"):
            processed = False
            if stream_data is not None:
                try:
                    pipeline_res = self.alert_pipeline.process_alert_stream(stream_data)
                    processed = True
                except TypeError:
                    pass
            if not processed:
                try:
                    pipeline_res = self.alert_pipeline.process_alert_stream(ticker, stream_data)
                    processed = True
                except TypeError:
                    try:
                        pipeline_res = self.alert_pipeline.process_alert_stream(ticker)
                        processed = True
                    except TypeError:
                        pipeline_res = {"ticker": ticker, "insider_detected": False, "alerts": []}
        elif hasattr(self.alert_pipeline, "process"):
            try:
                pipeline_res = self.alert_pipeline.process(ticker, stream_data)
            except TypeError:
                pipeline_res = self.alert_pipeline.process(ticker)
        else:
            pipeline_res = {"ticker": ticker, "insider_detected": False, "alerts": []}

        has_anomaly = anomaly_res.get("has_anomaly", False) if isinstance(anomaly_res, dict) else False
        insider_detected = pipeline_res.get("insider_detected", False) if isinstance(pipeline_res, dict) else False
        alerts = pipeline_res.get("alerts", []) if isinstance(pipeline_res, dict) else []

        is_coordinated = bool(has_anomaly and (insider_detected or len(alerts) > 0))

        result = {
            "ticker": ticker,
            "is_coordinated": is_coordinated,
            "suspicious": is_coordinated,
            "coordinated_activity": is_coordinated,
            "anomaly_data": anomaly_res,
            "insider_alert_data": pipeline_res,
        }
        
        if isinstance(anomaly_res, dict) and "anomaly_id" in anomaly_res:
            result["anomaly_id"] = anomaly_res["anomaly_id"]
        if isinstance(alerts, list) and len(alerts) > 0 and isinstance(alerts[0], dict) and "alert_id" in alerts[0]:
            result["alert_id"] = alerts[0]["alert_id"]

        return result

    def analyze_stream(self, exchange):
        anomaly_items = []
        if hasattr(self.anomaly_detector, "analyze_stream"):
            anomaly_items = self.anomaly_detector.analyze_stream(exchange)

        insider_items = {}
        if hasattr(self.alert_pipeline, "evaluate_market_stream"):
            insider_items = self.alert_pipeline.evaluate_market_stream(exchange)

        return {
            "exchange": exchange,
            "anomaly_items": anomaly_items,
            "insider_items": insider_items
        }

    def evaluate_exchange(self, exchange):
        return self.analyze_stream(exchange)

    def analyze_exchange(self, exchange):
        return self.analyze_stream(exchange)

    def evaluate_market_stream(self, exchange):
        return self.analyze_stream(exchange)

    def correlate_exchange(self, exchange):
        return self.analyze_stream(exchange)

    def analyze(self, ticker, stream_data=None):
        return self.analyze_ticker(ticker, stream_data)

    def detect(self, ticker, stream_data=None):
        return self.analyze_ticker(ticker, stream_data)

    def correlate(self, ticker, stream_data=None):
        return self.analyze_ticker(ticker, stream_data)

    def process(self, ticker, stream_data=None):
        return self.analyze_ticker(ticker, stream_data)


def market_insider_anomaly_analyzer(ticker=None, raw_stream_data=None):
    analyzer = MarketInsiderAnomalyAnalyzer()
    if isinstance(ticker, dict):
        t = ticker.get("ticker")
        s = ticker.get("raw_stream_data")
        return analyzer.analyze_ticker(t, s)
    return analyzer.analyze_ticker(ticker, raw_stream_data)


def evaluate_exchange_anomalies(exchange):
    analyzer = MarketInsiderAnomalyAnalyzer()
    return analyzer.analyze_stream(exchange)


def analyze_market_insider_anomalies(ticker=None, exchange=None, raw_stream_data=None):
    detector = MarketAnomalyDetector()
    pipeline = MarketInsiderAlertPipeline()

    anomaly_data = {}
    if hasattr(detector, "detect"):
        try:
            anomaly_data = detector.detect(ticker, raw_stream_data)
        except TypeError:
            try:
                anomaly_data = detector.detect(ticker)
            except TypeError:
                anomaly_data = detector.detect(raw_stream_data)

    formatted_stream = raw_stream_data
    if isinstance(raw_stream_data, dict):
        formatted_stream = io.BytesIO(json.dumps(raw_stream_data).encode("utf-8"))

    insider_alert_data = {}
    if hasattr(pipeline, "process_alert_stream"):
        try:
            insider_alert_data = pipeline.process_alert_stream(formatted_stream)
        except TypeError:
            try:
                insider_alert_data = pipeline.process_alert_stream(ticker, formatted_stream)
            except TypeError:
                try:
                    insider_alert_data = pipeline.process_alert_stream(ticker)
                except TypeError:
                    insider_alert_data = {}

    correlation_id = uuid.uuid4().hex
    is_coordinated = bool(
        (isinstance(anomaly_data, dict) and anomaly_data.get("has_anomaly")) and 
        (isinstance(insider_alert_data, dict) and (insider_alert_data.get("insider_detected") or insider_alert_data.get("alerts")))
    )

    result = {
        "correlation_id": correlation_id,
        "coordinated_activity_detected": is_coordinated,
        "ticker": ticker,
        "exchange": exchange,
        "anomaly_data": anomaly_data,
        "insider_alert_data": insider_alert_data
    }

    report_filename = f"insider_anomaly_report_{correlation_id}.json"
    with open(report_filename, "w", encoding="utf-8") as f:
        json.dump(result, f)

    return result