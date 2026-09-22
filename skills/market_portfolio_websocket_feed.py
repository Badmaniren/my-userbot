import json
import os
import random
import time
from typing import Generator, Dict, Any, Optional

try:
    import websockets.sync.client
except ImportError:
    import sys
    import types

    websockets = types.ModuleType("websockets")
    sync = types.ModuleType("sync")
    client = types.ModuleType("client")

    class DummyConnect:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def recv(self):
            raise Exception("websockets module is not available")

    def connect(*args, **kwargs):
        return DummyConnect(*args, **kwargs)

    client.connect = connect
    sync.client = client
    websockets.sync = sync
    sys.modules["websockets"] = websockets
    sys.modules["websockets.sync"] = sync
    sys.modules["websockets.sync.client"] = client


class MarketPortfolioWebsocketFeed:
    """Модуль для организации реального времени потока рыночных данных через веб-сокеты или симуляции стриминга."""

    def __init__(self, storage_file: str, ws_url: str):
        self.storage_file = storage_file
        self.ws_url = ws_url
        self.is_running = False

    def connect_and_stream(self, symbol: str, max_ticks: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        self.is_running = True
        tick_count = 0
        try:
            with websockets.sync.client.connect(self.ws_url) as websocket:
                while self.is_running:
                    if max_ticks is not None and tick_count >= max_ticks:
                        break
                    try:
                        message = websocket.recv()
                        data = json.loads(message)
                        if data.get("symbol") == symbol:
                            tick_count += 1
                            yield data
                    except json.JSONDecodeError as jde:
                        raise jde
        except Exception as e:
            if isinstance(e, json.JSONDecodeError):
                raise e
        finally:
            self.is_running = False

    def simulate_tick_stream(self, symbol: str, count: int = 5) -> Generator[Dict[str, Any], None, None]:
        self.is_running = True
        current_price = round(random.uniform(50.0, 500.0), 2)
        try:
            for _ in range(count):
                change = round(random.uniform(-2.0, 2.0), 2)
                current_price = max(0.01, round(current_price + change, 2))
                tick = {
                    "symbol": symbol,
                    "price": current_price,
                    "timestamp": str(time.time())
                }
                yield tick
        finally:
            self.is_running = False

    def broadcast_tick_to_storage(self, tick_data: Dict[str, Any]) -> None:
        symbol = tick_data.get("symbol")
        if not symbol:
            return

        data = {}
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

        if symbol not in data:
            data[symbol] = []

        data[symbol].append(tick_data)

        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_live_stream_summary(self, symbol: str) -> Dict[str, Any]:
        if not os.path.exists(self.storage_file):
            return {"symbol": symbol, "status": "no_data"}

        with open(self.storage_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        ticks = data.get(symbol, [])
        if not ticks:
            return {"symbol": symbol, "status": "no_data"}

        prices = [t["price"] for t in ticks if "price" in t]
        if not prices:
            return {"symbol": symbol, "status": "no_data"}

        return {
            "symbol": symbol,
            "status": "active",
            "total_ticks": len(ticks),
            "latest_price": prices[-1],
            "min_price": min(prices),
            "max_price": max(prices)
        }


class MarketParser:
    """Алиас класса для интеграционных тестов."""
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def load_data(self, storage_file: Optional[str] = None) -> Any:
        path = storage_file or self.storage_file
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)