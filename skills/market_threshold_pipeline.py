from skills.market_parser import MarketParser
from skills.market_report_generator import MarketReportGenerator

def send_telegram_notification(token: str, chat_id: str, message: str) -> None:
    pass

def check_market_threshold(storage_file: str, symbol: str, threshold: float, current_price: float = None) -> tuple:
    parser = MarketParser(storage_file=storage_file)
    try:
        parser.load_data(storage_file)
    except TypeError:
        parser.load_data()

    price = current_price
    if price is None:
        price = 0.0

    triggered = price >= threshold
    return triggered, price

def run_threshold_pipeline(symbol: str, url: str, storage_file: str, threshold: float, telegram_token: str = None, chat_id: str = None):
    parser = MarketParser(storage_file=storage_file)
    current_price = parser.fetch_price(url)

    report_gen = MarketReportGenerator(storage_file=storage_file)
    report = report_gen.generate_symbol_report(symbol)

    triggered, price = check_market_threshold(
        storage_file=storage_file,
        symbol=symbol,
        threshold=threshold,
        current_price=current_price
    )

    if triggered and telegram_token and chat_id:
        message = f"Threshold triggered for {symbol}: price {current_price} >= {threshold}"
        send_telegram_notification(telegram_token, chat_id, message)

    if telegram_token is None and chat_id is None:
        return triggered

    return {
        "price": price,
        "report": report
    }