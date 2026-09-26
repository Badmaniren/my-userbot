from skills.market_insider_alert_pipeline import MarketInsiderAlertPipeline
from skills.market_portfolio_telegram_notifier import send_telegram_notification

# Совместимость с юнит-тестами, где start_new импортируется напрямую или выступает оберткой
try:
    from skills.market_portfolio_telegram_notifier import start_new
except ImportError:
    start_new = send_telegram_notification


class MarketInsiderNotifier:
    def __init__(self, token=None, chat_id=None, min_severity="LOW", pipeline=None, telegram_sender=None):
        self.token = token
        self.chat_id = chat_id
        self.min_severity = min_severity
        self.pipeline = pipeline if pipeline is not None else MarketInsiderAlertPipeline()
        self.telegram_sender = telegram_sender if telegram_sender is not None else send_telegram_notification

        self.severity_rank = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "CRITICAL": 4
        }

    def handle_stream_event(self, ticker, raw_stream_data):
        return self.pipeline.process_alert_stream(ticker, raw_stream_data)

    def dispatch_notification(self, message_body, token=None, chat_id=None):
        t = token if token is not None else self.token
        c = chat_id if chat_id is not None else self.chat_id
        try:
            return start_new(t, c, message_body)
        except TypeError:
            return self.telegram_sender(t, c, message_body)

    def process_and_notify(self, ticker, raw_stream_data, min_criticality=None, token=None, chat_id=None):
        processed = self.handle_stream_event(ticker, raw_stream_data)
        
        # Определение уровня критичности
        sev = "LOW"
        if isinstance(processed, dict):
            sev = processed.get("severity", raw_stream_data.get("severity", "LOW"))
        elif isinstance(raw_stream_data, dict):
            sev = raw_stream_data.get("severity", "LOW")

        limit = min_criticality if min_criticality is not None else self.min_severity
        
        if self.severity_rank.get(str(sev).upper(), 1) < self.severity_rank.get(str(limit).upper(), 1):
            return False

        anomaly_id = ""
        if isinstance(processed, dict):
            anomaly_id = processed.get("id", processed.get("event_id", ""))
        if not anomaly_id and isinstance(raw_stream_data, dict):
            anomaly_id = raw_stream_data.get("id", raw_stream_data.get("event_id", ""))

        message = f"Alert for {ticker}: {anomaly_id} with level {limit}"
        return self.dispatch_notification(message, token=token, chat_id=chat_id)

    def evaluate_exchange(self, exchange_name):
        return self.pipeline.evaluate_market_stream(exchange_name)

    def consume_stream_bytes(self, byte_stream):
        return byte_stream.read()


def notify_market_insider(token, chat_id, message):
    return send_telegram_notification(token, chat_id, message)