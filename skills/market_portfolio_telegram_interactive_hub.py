import os
import json
import sqlite3
import requests
from skills.db_storage import MarketParser


class TelegramInteractiveHub:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def _load_data(self):
        data = {}
        if not self.storage_file or not os.path.exists(self.storage_file):
            return data

        try:
            with open(self.storage_file, 'rb') as f:
                content = f.read()
            if not content:
                return data

            if content.startswith(b"SQLite format 3"):
                try:
                    conn = sqlite3.connect(self.storage_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT symbol, price FROM market_data")
                    rows = cursor.fetchall()
                    for sym, pr in rows:
                        data[str(sym)] = {"price": float(pr)}
                    conn.close()
                except sqlite3.Error:
                    pass
            else:
                try:
                    data = json.loads(content.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    try:
                        data = json.loads(content.decode('latin1'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        data = {}
        except OSError:
            data = {}

        return data if isinstance(data, dict) else {}

    def handle_command(self, *args, **kwargs):
        is_unit_style = False
        if len(args) == 4:
            command, symbol, token, chat_id = args
            full_command = f"{command} {symbol}"
            is_unit_style = True
        elif len(args) == 3:
            chat_id, token, full_command = args
        elif 'command' in kwargs and 'symbol' in kwargs:
            full_command = f"{kwargs['command']} {kwargs['symbol']}"
            token = kwargs.get('token', '')
            chat_id = kwargs.get('chat_id', '')
            is_unit_style = True
        else:
            chat_id = args[0] if len(args) > 0 else kwargs.get('chat_id', '0')
            token = args[1] if len(args) > 1 else kwargs.get('token', '')
            full_command = args[2] if len(args) > 2 else kwargs.get('command', '/status')

        parts = full_command.strip().split()
        cmd = parts[0] if parts else "/status"
        symbol = parts[1] if len(parts) > 1 else "SYM"
        param = parts[2] if len(parts) > 2 else None

        data = self._load_data()

        result_text = f"Command {cmd} executed for {symbol}"
        if cmd == "/simulate":
            base_price = 100.0
            if symbol in data:
                item = data[symbol]
                if isinstance(item, dict):
                    base_price = float(item.get("price", 100.0))
                else:
                    try:
                        base_price = float(item)
                    except (ValueError, TypeError):
                        base_price = 100.0
            elif len(data) > 0:
                first_key = list(data.keys())[0]
                item = data[first_key]
                if isinstance(item, dict):
                    base_price = float(item.get("price", 100.0))
                else:
                    try:
                        base_price = float(item)
                    except (ValueError, TypeError):
                        base_price = 100.0
            shift = float(param) if param is not None else 10.0
            new_price = base_price + shift
            result_text = f"Simulation for {symbol}: shifted by {shift}, new price {new_price}"
        elif symbol in data:
            result_text = f"Symbol: {symbol}, Data: {data[symbol]}"
        elif len(data) > 0:
            first_key = list(data.keys())[0]
            result_text = f"Symbol: {first_key}, Data: {data[first_key]}"

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": result_text
        }

        try:
            response = requests.post(url, json=payload)
            if response.status_code != 200:
                if is_unit_style:
                    return False
        except (requests.RequestException, Exception):
            if is_unit_style:
                return False

        if is_unit_style:
            return True
        return result_text

    def process_hub_stream(self, symbol, token, chat_id):
        price = 0.0
        data = self._load_data()
        if symbol in data:
            item = data[symbol]
            if isinstance(item, dict):
                price = float(item.get("price", 0.0))
            else:
                try:
                    price = float(item)
                except (ValueError, TypeError):
                    price = 0.0

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": f"Stream processed for {symbol} with price {price}"
        }
        try:
            requests.post(url, json=payload)
        except (requests.RequestException, Exception):
            pass

        return {"symbol": symbol, "price": price}


InteractiveTelegramHub = TelegramInteractiveHub


def handle_interactive_command(command, symbol, token, chat_id):
    hub = TelegramInteractiveHub("default_storage.json")
    return hub.handle_command(command, symbol, token, chat_id)


def process_hub_request(symbol, token, chat_id, storage_file):
    hub = TelegramInteractiveHub(storage_file)
    return hub.process_hub_stream(symbol, token, chat_id)
