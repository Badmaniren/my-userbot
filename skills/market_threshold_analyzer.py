from skills.market_parser import MarketParser
from skills.db_storage import load_data
from skills.market_telegram_pipeline import send_telegram_notification

def analyze_and_notify(symbol, url, threshold, telegram_token, chat_id, storage_file=None):
    parser = MarketParser(storage_file=storage_file)
    current_price = parser.fetch_price(url)
    parser.fetch_and_store(symbol, current_price)

    exceeded = current_price > threshold
    if exceeded:
        message = f"Symbol {symbol} exceeded threshold with price {current_price}"
        send_telegram_notification(telegram_token, chat_id, message)

    return exceeded

def analyze_and_check_thresholds(storage_file, symbol, threshold):
    data = load_data(storage_file)
    if isinstance(data, dict):
        prices = data.get(symbol, [])
    else:
        prices = []

    if isinstance(prices, dict):
        current_price = float(prices.get("price", 0.0))
    elif isinstance(prices, list) and len(prices) > 0:
        current_price = float(prices[-1])
    elif isinstance(prices, (int, float)):
        current_price = float(prices)
    else:
        current_price = 0.0

    exceeded = current_price > threshold
    return {
        "exceeded": exceeded,
        "current_price": current_price
    }