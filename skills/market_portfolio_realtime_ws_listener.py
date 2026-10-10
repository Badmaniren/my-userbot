import json
import asyncio
from typing import Callable, Optional, Dict, Any
import websockets

try:
    from skills.db_storage import db_storage
except ImportError:
    db_storage = None

try:
    from skills.market_parser import market_parser
except ImportError:
    market_parser = None


class WebSocketConnectionError(Exception):
    """Исключение при ошибках подключения к WebSocket."""
    pass


class InvalidMessageError(Exception):
    """Исключение при невалидных или поврежденных сообщениях."""
    pass


class MarketPortfolioRealtimeWsListener:
    def __init__(
        self,
        uri: Optional[str] = None,
        channel: Optional[str] = None,
        target_file: Optional[str] = None,
        expected_event_id: Optional[str] = None
    ):
        self.uri = uri
        self.channel = channel
        self.target_file = target_file
        self.expected_event_id = expected_event_id
        self.is_connected = False
        self.on_message_callback: Optional[Callable[[Dict[str, Any]], None]] = None

    def validate_and_parse(self, raw_payload: str) -> Dict[str, Any]:
        try:
            data = json.loads(raw_payload)
        except (json.JSONDecodeError, TypeError):
            raise InvalidMessageError("Invalid JSON format")

        if not isinstance(data, dict):
            raise InvalidMessageError("Payload must be a dictionary")

        if "event_id" not in data or "symbol" not in data or "price" not in data:
            raise InvalidMessageError("Missing required fields")

        return data

    def process_stream_buffer(self, stream_io) -> Dict[str, Any]:
        content = stream_io.read().decode('utf-8')
        return self.validate_and_parse(content)

    async def process_raw_message(self, raw_message: str) -> Dict[str, Any]:
        parsed = self.validate_and_parse(raw_message)
        if self.target_file:
            with open(self.target_file, "a") as f:
                f.write(raw_message + "\n")
        return parsed

    async def connect_and_listen(self, max_retries: int = 5):
        if websockets is None:
            raise WebSocketConnectionError("websockets module is not installed")
        retries = 0
        while retries < max_retries or max_retries == 0:
            try:
                self.is_connected = True
                async with websockets.connect(self.uri) as ws:
                    while True:
                        msg = await ws.recv()
                        if msg is None:
                            break
                        parsed = self.validate_and_parse(msg)
                        if self.on_message_callback:
                            self.on_message_callback(parsed)
                break
            except Exception as e:
                self.is_connected = False
                retries += 1
                if retries >= max_retries:
                    raise WebSocketConnectionError(f"Failed to connect: {e}")
                await asyncio.sleep(0.1)


def market_portfolio_realtime_ws_listener(
    uri: Optional[str] = None,
    channel: Optional[str] = None,
    target_file: Optional[str] = None,
    expected_event_id: Optional[str] = None
) -> MarketPortfolioRealtimeWsListener:
    return MarketPortfolioRealtimeWsListener(
        uri=uri,
        channel=channel,
        target_file=target_file,
        expected_event_id=expected_event_id
    )