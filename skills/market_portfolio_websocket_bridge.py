import time
from skills.market_parser import MarketParser

def send_telegram_notification(token: str, chat_id: str, message: str) -> bool:
    """Заглушка функции отправки уведомлений в Telegram."""
    return True

def start_new(
    symbol: str,
    url: str,
    telegram_token: str,
    chat_id: str,
    storage_file: str,
    max_iterations: int = 10
):
    """
    Запускает процесс стриминга обновлений портфеля через эмулируемый канал.
    """
    parser = MarketParser(storage_file)
    iterations = 0

    while iterations < max_iterations:
        try:
            price = parser.fetch_price(url)
            message = f"Symbol: {symbol}, Price: {price}"
            send_telegram_notification(telegram_token, chat_id, message)
        except Exception as e:
            message = f"Error: {e}"
            send_telegram_notification(telegram_token, chat_id, message)
        
        iterations += 1
        time.sleep(1)


class MarketPortfolioWebsocketBridge:
    """
    Класс для интеграционного тестирования стриминга портфеля и эмуляции соединения.
    """
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.parser = MarketParser(storage_file)

    def emulate_connection(self) -> bool:
        """Эмулирует установку веб-сокет соединения."""
        return True

    def stream_portfolio_updates(self, symbol: str) -> str:
        """Возвращает актуальные данные портфеля для указанного символа."""
        data = self.parser.load_data(self.storage_file)
        prices = data.get(symbol, [])
        latest_price = prices[-1] if prices else 0.0
        return f"Stream update -> Symbol: {symbol}, Price: {latest_price}"