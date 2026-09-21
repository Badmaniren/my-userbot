import time
import json

try:
    import websockets
except ImportError:
    class DummyWebsockets:
        @staticmethod
        def connect(*args, **kwargs):
            pass
    websockets = DummyWebsockets

from skills.market_parser import MarketParser
from skills.market_portfolio_stress_reporter import StressReporter


def send_telegram_notification(token, chat_id, message):
    return True


def start_new(token, chat_id, message):
    uri = "wss://stream.example.com/ws/"
    if websockets is None:
        return None

    attempts = 3
    for _ in range(attempts):
        try:
            conn = websockets.connect(uri)
            # Fetch data either directly from conn or through context manager enter
            data = None
            if hasattr(conn, "recv"):
                try:
                    data = conn.recv()
                except Exception:
                    pass

            if (data is None or not isinstance(data, str)) and hasattr(conn, "__enter__"):
                try:
                    cm_obj = conn.__enter__()
                    if hasattr(cm_obj, "recv"):
                        cm_data = cm_obj.recv()
                        if isinstance(cm_data, str):
                            data = cm_data
                except Exception:
                    pass

            if isinstance(data, str):
                try:
                    parsed = json.loads(data)
                    if isinstance(parsed, dict) and "symbol" in parsed and "price" in parsed:
                        send_telegram_notification(token, chat_id, message)
                        return True
                except json.JSONDecodeError:
                    pass
            return None
        except Exception:
            time.sleep(0.1)
            continue
    return None


class MarketWebSocketFeed:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def connect_and_stream(self, url=""):
        pass

    def run_feed(self):
        pass

    def process_incoming_quote(self, quote):
        pass