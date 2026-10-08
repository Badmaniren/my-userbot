import sys
import uuid
from skills import db_storage as default_db_storage

class MarketPortfolioStressAuditRealtimeStreamer:
    def __init__(self, db_storage=None):
        self.db_storage = db_storage if db_storage is not None else default_db_storage
        self.market_anomaly_detector = None
        self.market_portfolio_alert_event_sink = None

    def stream_and_persist(self, portfolio_id: str) -> bool:
        line_data = sys.stdin.readline()
        if isinstance(line_data, bytes):
            line = line_data.decode('utf-8', errors='ignore').strip()
        else:
            line = str(line_data).strip()
            
        if not line:
            return False
        
        parts = line.split(":")
        if len(parts) >= 3:
            p_id, metric_name, metric_value = parts[0], parts[1], parts[2]
            if p_id == portfolio_id:
                try:
                    val = float(metric_value)
                except ValueError:
                    val = metric_value
                
                if hasattr(self.db_storage, 'save_metric'):
                    self.db_storage.save_metric(portfolio_id, metric_name, val)
                elif hasattr(self.db_storage, 'save_portfolio_metric'):
                    self.db_storage.save_portfolio_metric(portfolio_id, metric_name, val)
                return True
        return False

    def process_stream_chunk(self, chunk_data: dict) -> bool:
        if self.market_anomaly_detector is not None:
            is_anomaly = self.market_anomaly_detector.evaluate(chunk_data)
            if is_anomaly:
                return True
        return False

    def get_live_audit_metrics(self, unique_key: str) -> dict:
        if hasattr(self.db_storage, 'fetch_latest_audit'):
            return self.db_storage.fetch_latest_audit(unique_key)
        return {}

    def emit_stress_event(self, event_tag: str, value: int):
        if self.market_portfolio_alert_event_sink is not None:
            self.market_portfolio_alert_event_sink.push({
                "tag": event_tag,
                "value": value
            })

    def stream_audit_metrics(self, portfolio_id: str) -> dict:
        stream_id = str(uuid.uuid4())
        return {
            "stream_id": stream_id,
            "portfolio_id": portfolio_id
        }