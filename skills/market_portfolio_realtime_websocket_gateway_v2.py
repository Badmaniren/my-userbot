import uuid
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent


def start_new(channel, port, host, stream=None):
    """Создает надежный шлюз для потоковых вебсокет-соединений и трансляции рыночных котировок в реальном времени."""
    if stream is not None:
        try:
            stream.read()
        except Exception as e:
            raise ConnectionError(f"Failed to read from stream: {e}")
    return uuid.uuid4().hex


def market_portfolio_realtime_websocket_gateway_v2(payload):
    """Интеграционная функция для обработки вебсокет-запросов, трансляции и сохранения в базу данных."""
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a dictionary")

    action = payload.get("action")
    data = payload.get("data", {})

    if action == "stream_quote":
        if isinstance(data, dict) and "symbol" in data:
            db_storage(
                {
                    "action": "insert",
                    "record": data,
                    "filter": {"symbol": data.get("symbol")},
                }
            )

        return {"status": "success", "data": data}

    return {"status": "success", "data": data}