import time
import json
try:
    import websockets
except ImportError:
    websockets = None

from skills.market_parser import MarketParser
from skills.market_portfolio_stress_reporter import StressReporter


def send_telegram_notification(token, chat_id, message):
    return True


def start_new(token, chat_id, message):
    uri = "wss://stream.example.com/ws/"
    if websockets is None:
        return False
    try:
        with websockets.connect(uri) as websocket:
            data = websocket.recv()
            if isinstance(data, str):
                parsed = json.loads(data)
                if "symbol" in parsed and "price" in parsed:
                    send_telegram_notification(token, chat_id, message)
                    return True
            return False
    except Exception:
        return False


class MarketWebSocketFeed:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def connect_and_stream(self, url=""):
        pass

    def run_feed(self):
        pass

    def process_incoming_quote(self, quote):
        pass