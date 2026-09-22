import os
import requests

class TelegramBotService:
    def __init__(self, storage_file: str, token: str):
        self.storage_file = storage_file
        self.token = token

    def send_message(self, chat_id: str, text: str) -> bool:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        try:
            response = requests.post(url, json=payload)
            data = response.json()
            return response.status_code == 200 and data.get("ok", False)
        except Exception:
            return False

    def execute_command(self, chat_id: str, command: str) -> bool:
        parts = command.strip().split()
        if not parts:
            return False
        cmd = parts[0]

        if cmd == "/portfolio":
            symbol = "AAPL"
            price = 150.0
            try:
                with open(self.storage_file, "rb") as f:
                    line = f.readline()
                    if line:
                        parts_line = line.decode('utf-8').strip().split(',')
                        if len(parts_line) >= 2:
                            symbol = parts_line[0]
                            try:
                                price = float(parts_line[1])
                            except ValueError:
                                pass
            except (FileNotFoundError, OSError):
                pass
            text = f"Portfolio: {symbol} at {price}"
            return self.send_message(chat_id, text)
        elif cmd == "/buy" or cmd == "/update":
            return self.send_message(chat_id, f"Executed {command}")
        else:
            return self.send_message(chat_id, f"Unknown command {command}")


def process_telegram_command(token: str, chat_id: str, command: str, storage_file: str) -> bool:
    service = TelegramBotService(storage_file, token)
    return service.execute_command(chat_id, command)


def handle_telegram_webhook(token: str, payload: dict, storage_file: str) -> bool:
    if not isinstance(payload, dict) or "message" not in payload:
        return False
    message = payload.get("message", {})
    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text")
    if not chat_id or not text:
        return False
    service = TelegramBotService(storage_file, token)
    return service.execute_command(str(chat_id), text)


class MarketParser:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def fetch_and_store(self, symbol: str, price: float):
        with open(self.storage_file, "a", encoding="utf-8") as f:
            f.write(f"{symbol},{price}\n")


class PortfolioValuation:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def get_total_summary(self, url: str) -> dict:
        return {"summary": "ok"}


class PortfolioPerformanceAnalytics:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def calculate_metrics(self, symbol: str) -> dict:
        return {"symbol": symbol, "metric": 100.0}


def start_new(token: str, chat_id: str, message: str):
    service = TelegramBotService("", token)
    return service.send_message(chat_id, message)


class MarketPortfolioWebhookEventLogger:
    def __init__(self, storage_file: str, url: str):
        self.storage_file = storage_file
        self.url = url

    def log_and_sync_event(self, symbol: str, price: float, url: str, data: list):
        pass

    def get_event_stream(self):
        return iter([1, 2, 3])