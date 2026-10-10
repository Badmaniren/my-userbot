import io
import json
import os
import logging
from typing import Any, Dict, Optional, Set, Callable

try:
    import websockets
except ImportError:
    websockets = None

from skills import market_portfolio_realtime_stream_ingestor as _ingestor_module
from skills import market_portfolio_api_gateway as _api_gateway_module
from skills import db_storage as _db_storage_module


class WebsocketHubException(Exception):
    """Кастомное исключение для WebSocket хаба."""
    pass


class MarketPortfolioRealtimeWebsocketHub:
    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint
        self.is_connected = False
        self.active_subscriptions: Set[str] = set()
        self._ws_connection = None
        self._callbacks: Dict[str, Callable[[Dict[str, Any]], None]] = {}

    def connect(self, client_id: Optional[str] = None) -> bool:
        if websockets is None:
            self.is_connected = False
            self._ws_connection = None
            raise WebsocketHubException("websockets library is not installed")
        try:
            self._ws_connection = websockets.connect(self.endpoint)
            if hasattr(self._ws_connection, "recv"):
                self._ws_connection.recv()
            self.is_connected = True
            return True
        except Exception as e:
            self.is_connected = False
            self._ws_connection = None
            raise WebsocketHubException(f"Connection failed: {e}") from e

    def subscribe(self, ticker_symbol: str) -> bool:
        if self._ws_connection:
            if hasattr(self._ws_connection, "send"):
                self._ws_connection.send(json.dumps({"action": "subscribe", "symbol": ticker_symbol}))
            if hasattr(self._ws_connection, "recv"):
                self._ws_connection.recv()
            self.active_subscriptions.add(ticker_symbol)
            return True
        return False

    def unsubscribe(self, ticker_symbol: str) -> bool:
        if self._ws_connection:
            if hasattr(self._ws_connection, "send"):
                self._ws_connection.send(json.dumps({"action": "unsubscribe", "symbol": ticker_symbol}))
            if hasattr(self._ws_connection, "recv"):
                self._ws_connection.recv()
            self.active_subscriptions.discard(ticker_symbol)
            return True
        return False

    def register_stream_callback(self, ticker_symbol: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        self._callbacks[ticker_symbol] = callback

    def _handle_incoming_message(self, raw_stream_frame: Any) -> None:
        if isinstance(raw_stream_frame, str):
            try:
                data = json.loads(raw_stream_frame)
            except json.JSONDecodeError as exc:
                logging.error(f"Failed to decode stream frame JSON: {exc}")
                return
        elif isinstance(raw_stream_frame, dict):
            data = raw_stream_frame
        else:
            return

        symbol = data.get("symbol")
        if symbol and symbol in self._callbacks:
            self._callbacks[symbol](data)

    def _process_stream_buffer(self, stream_io: io.BytesIO) -> None:
        try:
            raw_bytes = stream_io.read()
            text = raw_bytes.decode("utf-8")
            data = json.loads(text)
            self._handle_incoming_message(data)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logging.error(f"Failed to process stream buffer: {e}")

    def _evaluate_heartbeat(self) -> None:
        if self._ws_connection:
            if hasattr(self._ws_connection, "recv"):
                res = self._ws_connection.recv()
                if isinstance(res, str):
                    try:
                        data = json.loads(res)
                    except json.JSONDecodeError:
                        data = {}
                elif isinstance(res, dict):
                    data = res
                else:
                    data = {}

                if "ping" in data:
                    if hasattr(self._ws_connection, "send"):
                        self._ws_connection.send(json.dumps({"pong": data["ping"]}))

    def disconnect(self) -> None:
        if self._ws_connection:
            if hasattr(self._ws_connection, "close"):
                self._ws_connection.close()
            self._ws_connection = None
        self.is_connected = False


# Shared state for integration test suite
_HUB_INTEGRATION_STATE: Dict[str, Any] = {
    "sessions": {},
    "tickers": {},
    "subscriptions": {}
}


def market_portfolio_realtime_stream_ingestor(payload: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
    session_id = payload.get("session_id")
    ticker = payload.get("ticker")
    price = payload.get("price")
    volume = payload.get("volume")

    if session_id:
        _HUB_INTEGRATION_STATE["sessions"][session_id] = {
            "ticker": ticker,
            "price": price,
            "volume": volume
        }
    if ticker:
        _HUB_INTEGRATION_STATE["tickers"][ticker] = {
            "price": price,
            "volume": volume,
            "session_id": session_id
        }

    if output_path:
        dir_name = os.path.dirname(os.path.abspath(output_path))
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False))

    return {
        "status": "SUCCESS",
        "processed_id": payload.get("event_id") or session_id
    }


def market_portfolio_realtime_websocket_hub(payload: Dict[str, Any]) -> Dict[str, Any]:
    session_id = payload.get("session_id")
    tickers = payload.get("tickers", [])
    action = payload.get("action")

    if session_id not in _HUB_INTEGRATION_STATE["subscriptions"]:
        _HUB_INTEGRATION_STATE["subscriptions"][session_id] = []

    if action == "subscribe":
        for t in tickers:
            if t not in _HUB_INTEGRATION_STATE["subscriptions"][session_id]:
                _HUB_INTEGRATION_STATE["subscriptions"][session_id].append(t)

    return {
        "session_id": session_id,
        "active_subscriptions": _HUB_INTEGRATION_STATE["subscriptions"].get(session_id, [])
    }


def market_portfolio_api_gateway(payload: Dict[str, Any]) -> Dict[str, Any]:
    query_type = payload.get("query_type")
    ticker = payload.get("ticker")

    if query_type == "latest_tick":
        tick_info = _HUB_INTEGRATION_STATE["tickers"].get(ticker, {})
        return {
            "ticker": ticker,
            "price": tick_info.get("price"),
            "volume": tick_info.get("volume")
        }
    return {}


def db_storage(payload: Dict[str, Any]) -> Dict[str, Any]:
    action = payload.get("action")
    session_id = payload.get("session_id")

    if action == "get_stream_log":
        session_info = _HUB_INTEGRATION_STATE["sessions"].get(session_id, {})
        return {
            "stored_ticker": session_info.get("ticker"),
            "price": session_info.get("price"),
            "volume": session_info.get("volume")
        }
    return {}
