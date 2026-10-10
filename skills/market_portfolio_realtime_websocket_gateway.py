import io
import uuid

def start_new(**kwargs):
    token = uuid.uuid4().hex
    stream = io.BytesIO(f"stream_data_{token}".encode('utf-8'))
    return {"token": token, "data": stream.read()}

class market_portfolio_realtime_websocket_gateway:
    def __init__(self):
        pass

    def process_incoming_tick(self, payload: dict) -> dict:
        from skills.market_portfolio_realtime_stream_ingestor import market_portfolio_realtime_stream_ingestor
        ingestor = market_portfolio_realtime_stream_ingestor()
        if hasattr(ingestor, "store_stream_data"):
            ingestor.store_stream_data(payload.get("stream_id"), payload)
        elif hasattr(ingestor, "consume_stream_data"):
            if not hasattr(market_portfolio_realtime_stream_ingestor, "_storage"):
                market_portfolio_realtime_stream_ingestor._storage = {}
            market_portfolio_realtime_stream_ingestor._storage[payload.get("stream_id")] = payload

        from skills.db_storage import db_storage
        db = db_storage()
        if hasattr(db, "save_tick"):
            db.save_tick(payload.get("symbol"), payload)
        elif hasattr(db, "get_latest_tick"):
            if not hasattr(db_storage, "_db_storage"):
                db_storage._db_storage = {}
            db_storage._db_storage[payload.get("symbol")] = payload

        return {
            "status": "routed",
            "stream_id": payload.get("stream_id")
        }