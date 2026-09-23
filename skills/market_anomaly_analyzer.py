import math
import statistics

class MarketAnomalyAnalyzer:
    def __init__(self, db_storage=None, market_parser=None, alert_dispatcher=None):
        self.db_storage = db_storage
        self.market_parser = market_parser
        self.alert_dispatcher = alert_dispatcher

    def _calculate_z_score(self, target_value, data):
        if not data or len(data) < 2:
            return 0.0

        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return 0.0

        return (target_value - mean) / std_dev

    def detect_anomaly(self, ticker, z_score, threshold):
        return z_score > threshold

    def save_report(self, report_data):
        if self.db_storage:
            self.db_storage.save(report_data)

    def fetch_market_data(self):
        return self.market_parser.fetch_data()

    def dispatch_alert(self, event_id):
        if self.alert_dispatcher:
            self.alert_dispatcher.dispatch(event_id)

    def log_to_audit(self, log_entry):
        # Реализация логирования
        pass

    def analyze(self, symbol, data, request_id):
        volumes = [d['volume'] for d in data]
        target_volume = volumes[-1]
        historical_volumes = volumes[:-1]

        z_score = self._calculate_z_score(target_volume, historical_volumes)
        is_anomaly = self.detect_anomaly(symbol, z_score, threshold=2.0)

        report = {
            "request_id": request_id,
            "symbol": symbol,
            "z_score": z_score,
            "is_anomaly": is_anomaly
        }

        self.save_report(report)

        if is_anomaly and self.alert_dispatcher:
            self.alert_dispatcher.dispatch({
                "request_id": request_id,
                "anomaly_type": "Z-SCORE_EXCEEDED"
            })

        return report