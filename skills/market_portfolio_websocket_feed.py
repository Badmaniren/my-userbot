import json
import os
import time
try:
    from websockets.sync import client as ws_client
except ImportError:
    ws_client = None

from skills.market_portfolio_autonomous_sentinel import AutonomousSentinel
from skills.db_storage import MarketParser

class WebSocketFeedProcessor:
    def __init__(self, storage_file=None, ws_url=None, sentinel=None):
        self.storage_file = storage_file
        self.ws_url = ws_url
        self._active_connections = 0
        self.sentinel = sentinel

    def parse_incoming_payload(self, payload):
        try:
            data = json.loads(payload)
            if isinstance(data, dict) and "symbol" in data and "price" in data and "timestamp" in data:
                return data
        except (json.JSONDecodeError, TypeError):
            pass
        return None

    def prepare_alert_trigger_data(self, data, threshold):
        current_price = data["price"]
        triggered = current_price >= threshold
        return {
            "symbol": data["symbol"],
            "current_price": current_price,
            "threshold": threshold,
            "triggered": triggered
        }

    def store_feed_datapoint(self, symbol, price):
        if not self.storage_file:
            return
        entry = {
            "symbol": symbol,
            "price": price,
            "timestamp": int(time.time())
        }
        with open(self.storage_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def consume_single_tick(self):
        if not self.ws_url or ws_client is None:
            return False
        self._active_connections += 1
        try:
            with ws_client.connect(self.ws_url) as websocket:
                raw_msg = websocket.recv()
                parsed = self.parse_incoming_payload(raw_msg)
                if parsed:
                    self.store_feed_datapoint(parsed["symbol"], parsed["price"])
                    return True
        finally:
            self._active_connections -= 1
        return False

    def get_live_feed_summary(self, symbol):
        total_ticks = 0
        prices = []
        if self.storage_file and os.path.exists(self.storage_file):
            with open(self.storage_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        if item.get("symbol") == symbol:
                            total_ticks += 1
                            prices.append(item.get("price"))

        summary = {
            "symbol": symbol,
            "total_ticks": total_ticks
        }
        if prices:
            summary["avg_price"] = sum(prices) / len(prices)
            summary["max_price"] = max(prices)
            summary["min_price"] = min(prices)
        else:
            summary["avg_price"] = 0.0
            summary["max_price"] = 0.0
            summary["min_price"] = 0.0

        return summary

    def ingest_live_quote(self, symbol, price, url=None, telegram_token=None, chat_id=None):
        self.store_feed_datapoint(symbol, price)
        if self.sentinel:
            if hasattr(self.sentinel, "check_and_notify"):
                try:
                    self.sentinel.check_and_notify(symbol=symbol, current_price=price, telegram_token=telegram_token, chat_id=chat_id)
                except TypeError:
                    self.sentinel.check_and_notify(symbol=symbol, current_price=price)
            elif hasattr(self.sentinel, "run_surveillance"):
                try:
                    self.sentinel.run_surveillance(symbol=symbol, url=url, telegram_token=telegram_token, chat_id=chat_id)
                except TypeError:
                    self.sentinel.run_surveillance(symbol, url, telegram_token, chat_id)
            elif hasattr(self.sentinel, "evaluate_and_alert"):
                self.sentinel.evaluate_and_alert(symbol=symbol, current_price=price, url=url, telegram_token=telegram_token, chat_id=chat_id)
        elif self.storage_file:
            parser = MarketParser(storage_file=self.storage_file)
            parser.fetch_and_store(symbol=symbol, price=price)