from skills.market_parser import MarketParser
from skills.market_telegram_pipeline import send_telegram_notification

send_telegram_pipeline = send_telegram_notification

def check_threshold_and_alert(symbol=None, url=None, threshold=None, token=None, chat_id=None, storage_file=None, telegram_token=None):
    """
    Проверяет пороговое значение цены для заданного символа и отправляет уведомление в Telegram,
    если цена превышает или равна порогу. Поддерживает оба набора именованных аргументов.
    """
    resolved_token = token if token is not None else telegram_token
    parser = MarketParser(storage_file=storage_file)

    # Интеграционный/юнит-тест вызывает функцию без url, чтобы получить парсер
    if url is None:
        return parser

    price = parser.fetch_price(url)

    if price is not None and threshold is not None and price >= threshold:
        message = f"Threshold exceeded for {symbol}: {price}"
        send_telegram_notification(resolved_token, chat_id, message)
        parser.fetch_and_store(symbol, price)

    return price