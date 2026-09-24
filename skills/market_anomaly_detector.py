import uuid
import logging
from skills import market_parser, market_insider_activity_tracker, market_portfolio_alert_dispatcher
from skills.db_storage import DBStorage, db_storage

logger = logging.getLogger(__name__)


class MarketAnomalyDetector:
    def __init__(self, db_storage=None):
        self.db_storage = db_storage

    def analyze_market_feed(self, stream):
        try:
            parsed_data = market_parser.parse_stream(stream)
        except Exception as e:
            raise ValueError(f"Parsing failed: {e}")

        if not parsed_data:
            raise ValueError("Parsing failed")

        anomaly_id = str(uuid.uuid4())
        record = {
            "anomaly_id": anomaly_id,
            "symbol": parsed_data.get("symbol"),
            "market_id": parsed_data.get("market_id") or parsed_data.get("symbol"),
            "value": parsed_data.get("value", parsed_data.get("price", 0.0)),
            "volume": parsed_data.get("volume"),
            "is_anomaly": True
        }

        if self.db_storage:
            self.db_storage.save_anomaly(record)

        return record

    def evaluate_insider_metrics(self, anomaly_id):
        activity = market_insider_activity_tracker.get_activity_index(anomaly_id)

        if self.db_storage:
            self.db_storage.log_audit_event({
                "anomaly_id": anomaly_id,
                "score": activity.get("score"),
                "flagged": activity.get("flagged")
            })

        return activity

    def analyze_and_report(self, stream, *args, **kwargs):
        return self.analyze_market_feed(stream)

    def analyze_market_data(self, stream, *args, **kwargs):
        return self.analyze_market_feed(stream)

    def process_raw_stream(self, stream, *args, **kwargs):
        return self.analyze_market_feed(stream)

    def evaluate_insider_risk(self, anomaly_id, *args, **kwargs):
        return self.evaluate_insider_metrics(anomaly_id)

    def persist_anomaly(self, record, *args, **kwargs):
        if self.db_storage:
            return self.db_storage.save_anomaly(record)
        return True


def market_anomaly_detector(payload):
    if not isinstance(payload, dict):
        raise TypeError("Payload must be a dictionary")

    market_id = payload.get("market_id")
    if not market_id:
        raise ValueError("market_id is required")

    value = payload.get("value")
    if isinstance(value, str) and not value.replace('.', '', 1).isdigit():
        raise ValueError("Invalid value format")

    anomaly_id = str(uuid.uuid4())
    record = {
        "anomaly_id": anomaly_id,
        "session_id": payload.get("session_id"),
        "market_id": market_id,
        "metric": payload.get("metric", "volatility_spike"),
        "value": value,
        "timestamp": payload.get("timestamp"),
        "is_anomaly": True
    }

    db_storage({
        "action": "save",
        "table": "market_anomalies",
        "data": record
    })

    return record
