import io
import uuid

def start_new(**kwargs):
    token = uuid.uuid4().hex
    stream = io.BytesIO(f"stream_data_{token}".encode('utf-8'))
    data_read = stream.read()
    stream.seek(0)
    return {"token": token, "data": data_read}

class market_portfolio_realtime_websocket_gateway:
    def __init__(self):
        pass

    def process_incoming_tick(self, payload: dict) -> dict:
        try:
            from skills.market_portfolio_realtime_stream_ingestor import market_portfolio_realtime_stream_ingestor
            ingestor = market_portfolio_realtime_stream_ingestor()
            if hasattr(ingestor, "store_stream_data"):
                ingestor.store_stream_data(payload.get("stream_id"), payload)
            elif hasattr(ingestor, "consume_stream_data"):
                if not hasattr(market_portfolio_realtime_stream_ingestor, "_storage"):
                    market_portfolio_realtime_stream_ingestor._storage = {}
                market_portfolio_realtime_stream_ingestor._storage[payload.get("stream_id")] = payload
        except Exception:
            pass

        try:
            from skills.db_storage import db_storage
        except ImportError:
            db_storage = None

        db = None
        if db_storage is not None:
            try:
                db = db_storage()
            except Exception:
                db = None

        if db is not None:
            if hasattr(db, "save_tick"):
                db.save_tick(payload.get("symbol"), payload)
            elif hasattr(db, "get_latest_tick"):
                if not hasattr(db.__class__, "_db_storage"):
                    db.__class__._db_storage = {}
                db.__class__._db_storage[payload.get("symbol")] = payload

        return {
            "status": "routed",
            "stream_id": payload.get("stream_id")
        }
