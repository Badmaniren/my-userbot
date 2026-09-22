import json
import os
import websocket

def send_telegram_notification(token, chat_id, message):
    """Заглушка для отправки уведомлений в Telegram."""
    pass

class MarketWebSocketFeed:
    """Класс для интеграционного тестирования и управления WebSocket потоками."""
    
    def __init__(self, storage_file="market_storage.json"):
        self.storage_file = storage_file

    def process_incoming_data(self, symbol, price):
        """Обрабатывает входящие данные котировок и сохраняет в хранилище."""
        data = {}
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                data = {}

        data[symbol] = {
            "price": price
        }

        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except OSError:
            pass

        return data[symbol]

    def connect_and_stream(self, uri, symbol, max_messages=1):
        """Подключается к WebSocket и получает сообщения."""
        def on_message(ws, message):
            pass

        def on_error(ws, error):
            raise error

        ws_app = websocket.WebSocketApp(
            uri,
            on_message=on_message,
            on_error=on_error
        )
        ws_app.run_forever()


def start_new(uri, symbol, telegram_token, chat_id):
    """Функция для запуска нового потока котировок WebSocket (для юнит-тестов)."""
    feed = MarketWebSocketFeed()

    def on_message(ws, message):
        try:
            parsed = json.loads(message)
            price = parsed.get("price")
            if price is not None:
                feed.process_incoming_data(symbol, price)
                send_telegram_notification(telegram_token, chat_id, f"Symbol: {symbol}, Price: {price}")
        except (json.JSONDecodeError, TypeError):
            pass

    def on_error(ws, error):
        raise error

    ws_app = websocket.WebSocketApp(
        uri,
        on_message=on_message,
        on_error=on_error
    )
    ws_app.run_forever()
    return True