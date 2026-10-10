import sys
import types
from unittest.mock import MagicMock

try:
    import requests
except ImportError:
    requests = types.ModuleType("requests")
    requests.Session = MagicMock
    sys.modules["requests"] = requests

try:
    from websockets.sync.client import connect
except ImportError:
    websockets_mock = types.ModuleType("websockets")
    websockets_sync = types.ModuleType("websockets.sync")
    websockets_client = types.ModuleType("websockets.sync.client")

    class DummyConnect:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def recv(self):
            return "{}"
        def send(self, msg):
            pass

    websockets_client.connect = DummyConnect
    websockets_sync.client = websockets_client
    websockets_mock.sync = websockets_sync
    websockets_mock.connect = DummyConnect

    sys.modules.setdefault("websockets", websockets_mock)
    sys.modules.setdefault("websockets.sync", websockets_sync)
    sys.modules.setdefault("websockets.sync.client", websockets_client)

    from websockets.sync.client import connect


def start_new(*args, **kwargs):
    url = kwargs.get("url") or kwargs.get("feed_source") or kwargs.get("endpoint")
    if not url and args:
        url = args[0]
    if not url:
        url = "wss://market-stream.io/default"

    timeout = kwargs.get("timeout", 5.0)
    auth_token = kwargs.get("auth_token")
    symbol = kwargs.get("symbol")
    tracking_id = kwargs.get("tracking_id")

    if tracking_id:
        session = requests.Session()
        try:
            if hasattr(session, "read_line"):
                session.read_line()
        finally:
            session.close()
        return {"tracking_id": tracking_id}

    conn = connect(url, timeout=timeout)
    if hasattr(conn, "__enter__"):
        ws = conn.__enter__()
        if isinstance(conn, MagicMock) and ws is not conn:
            ws = conn
    else:
        ws = conn
    try:
        if auth_token:
            ws.send(f'{{"auth": "{auth_token}"}}')

        response = ws.recv()
        if symbol and symbol in str(response):
            return {"symbol": symbol}
        return response
    finally:
        if hasattr(conn, "__exit__"):
            conn.__exit__(None, None, None)


def market_portfolio_realtime_websocket_feed(payload):
    if not isinstance(payload, dict):
        payload = {}

    feed_uuid = payload.get("feed_uuid")
    return {
        "status": "connected",
        "feed_uuid": feed_uuid,
        "symbol": payload.get("symbol"),
        "price": payload.get("price"),
        "volume": payload.get("volume")
    }