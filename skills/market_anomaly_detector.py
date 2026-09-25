import io
from skills.market_insider_activity_tracker import MarketInsiderActivityTracker, DBStorage
from skills.market_portfolio_alert_dispatcher import dispatch_portfolio_alerts

class MarketAnomalyDetector:
    def __init__(self, db_path=None):
        self.db_path = db_path
        if db_path:
            self.tracker = MarketInsiderActivityTracker(db_path=db_path)
            self.storage = DBStorage(db_path=db_path)
        else:
            self.tracker = MarketInsiderActivityTracker()
            self.storage = None

    def _ensure_stream(self, stream):
        if hasattr(stream, "read"):
            return stream
        if isinstance(stream, bytes):
            return io.BytesIO(stream)
        if isinstance(stream, str):
            return io.BytesIO(stream.encode('utf-8'))
        return io.BytesIO(str(stream).encode('utf-8'))

    def detect_anomaly(
        self,
        raw_data_stream,
        symbol,
        url,
        telegram_token,
        chat_id,
        storage_file,
        severity_level,
        min_threshold,
        channels
    ):
        raw_data_stream = self._ensure_stream(raw_data_stream)
        activity_result = self.tracker.analyze_activity(raw_data_stream)

        is_anomaly = activity_result.get("is_anomaly", False) or activity_result.get("status") == "ALERT"

        if is_anomaly:
            dispatch_portfolio_alerts(
                symbol,
                url,
                telegram_token,
                chat_id,
                storage_file,
                severity_level,
                min_threshold,
                channels
            )

        return activity_result

    def process_raw_stream_bytes(self, stream_bytes):
        stream_bytes = self._ensure_stream(stream_bytes)
        return self.tracker.analyze_activity(stream_bytes)

    def process_raw_stream(self, stream_data):
        return self.process_raw_stream_bytes(stream_data)

    def detect_and_dispatch(
        self,
        ticker,
        raw_data_stream,
        url,
        telegram_token,
        chat_id,
        storage_file,
        severity_level,
        min_threshold,
        channels
    ):
        raw_data_stream = self._ensure_stream(raw_data_stream)
        activity_result = self.tracker.analyze_activity(raw_data_stream)
        is_anomaly = activity_result.get("is_anomaly", False) or activity_result.get("status") == "ALERT"

        dispatch_status = None
        if is_anomaly:
            dispatch_status = dispatch_portfolio_alerts(
                ticker,
                url,
                telegram_token,
                chat_id,
                storage_file,
                severity_level,
                min_threshold,
                channels
            )

        return {
            "anomaly_detected": is_anomaly,
            "dispatch_status": dispatch_status,
            "activity_details": activity_result
        }

    def analyze_market_feed(self, raw_data_stream, *args, **kwargs):
        raw_data_stream = self._ensure_stream(raw_data_stream)
        return self.tracker.analyze_activity(raw_data_stream)

    def evaluate_insider_metrics(self, raw_data_stream, *args, **kwargs):
        return self.analyze_market_feed(raw_data_stream, *args, **kwargs)

    def evaluate_insider_risk(self, raw_data_stream, *args, **kwargs):
        return self.evaluate_insider_metrics(raw_data_stream, *args, **kwargs)

    def analyze_and_report(self, ticker, raw_data_stream, url="", telegram_token="", chat_id="", storage_file="", severity_level="INFO", min_threshold=0.0, channels=None):
        return self.detect_and_dispatch(ticker, raw_data_stream, url, telegram_token, chat_id, storage_file, severity_level, min_threshold, channels or [])

    def analyze_market_data(self, raw_data_stream, *args, **kwargs):
        return self.analyze_market_feed(raw_data_stream, *args, **kwargs)

    def persist_anomaly(self, ticker, is_anomaly, signature):
        if self.storage:
            self.storage.save_activity(ticker, is_anomaly, signature)
            return True
        return False


market_anomaly_detector = MarketAnomalyDetector()
