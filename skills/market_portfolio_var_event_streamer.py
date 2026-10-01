import datetime
import hashlib
import uuid
import requests

from skills.market_portfolio_collector_agent import collect_market_data
from skills.db_storage import save_stream_record, get_stream_record

class MarketPortfolioVaREventStreamer:
    def __init__(self, streamer_id: str, endpoint_url: str):
        self.streamer_id = streamer_id
        self.endpoint_url = endpoint_url
        self.is_streaming = False
        self.event_counter = 0

    def generate_var_event_payload(
        self,
        portfolio_id: str,
        confidence_level: float,
        var_value: float,
        currency: str = "USD"
    ) -> dict:
        return {
            "streamer_id": self.streamer_id,
            "portfolio_id": portfolio_id,
            "confidence_level": confidence_level,
            "var_value": var_value,
            "currency": currency,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event_uuid": str(uuid.uuid4())
        }

    def stream_event(
        self,
        portfolio_id: str,
        confidence_level: float,
        var_value: float,
        currency: str = "USD"
    ) -> bool:
        payload = self.generate_var_event_payload(
            portfolio_id=portfolio_id,
            confidence_level=confidence_level,
            var_value=var_value,
            currency=currency
        )
        try:
            response = requests.post(self.endpoint_url, json=payload)
            if response.status_code == 200:
                self.event_counter += 1
                return True
            return False
        except Exception:
            return False

    def batch_stream_events(self, portfolio_ids: list, confidence_level: float = 0.95, var_value: float = 1000.0) -> int:
        success_count = 0
        for pid in portfolio_ids:
            if self.stream_event(portfolio_id=pid, confidence_level=confidence_level, var_value=var_value):
                success_count += 1
        return success_count

    def export_metrics_stream(self, file_stream) -> dict:
        content = file_stream.read()
        checksum = hashlib.sha256(content).hexdigest()
        return {
            "streamer_id": self.streamer_id,
            "bytes_processed": len(content),
            "checksum": checksum
        }




def run_var_event_streamer(stream_id: str, symbol: str, confidence: float, payload: dict) -> dict:
    price = payload.get("price", 100.0)
    volume = payload.get("volume", 1000)
    var_metric = round(price * volume * (1.0 - confidence), 2)
    return {
        "stream_id": stream_id,
        "symbol": symbol,
        "confidence": confidence,
        "var_metric": var_metric,
        "raw_payload": payload
    }