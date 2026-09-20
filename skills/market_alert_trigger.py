from skills.market_parser import MarketParser
from skills.db_storage import MarketParser as DBStorageParser

def fetch_and_store(symbol, price, storage_file=None):
    """
    Вспомогательная функция для сохранения данных через DBStorageParser,
    если в модуле db_storage отсутствует прямая функция fetch_and_store.
    """
    db_instance = DBStorageParser(storage_file=storage_file)
    if hasattr(db_instance, "fetch_and_store"):
        return db_instance.fetch_and_store(symbol, price)
    elif hasattr(db_instance, "save_data"):
        data = db_instance.load_data(storage_file) if hasattr(db_instance, "load_data") else {}
        data[symbol] = {"price": price}
        return db_instance.save_data(data, storage_file)
    return None

def load_data(storage_file=None):
    """
    Загружает данные из хранилища с помощью DBStorageParser без использования глушения ошибок.
    """
    db_instance = DBStorageParser(storage_file=storage_file)
    if hasattr(db_instance, "load_data"):
        return db_instance.load_data(storage_file)
    return {}

def _extract_symbol_info(loaded_data, symbol):
    if not loaded_data or not symbol:
        return None

    if isinstance(loaded_data, dict) and symbol in loaded_data:
        item = loaded_data[symbol]
        if isinstance(item, dict):
            return item
        elif isinstance(item, (int, float)):
            return {"price": float(item)}
        elif isinstance(item, str):
            try:
                return {"price": float(item)}
            except ValueError:
                pass

    if isinstance(loaded_data, (list, tuple)):
        for row in loaded_data:
            if isinstance(row, str) and symbol in row:
                parts = row.strip().split(',')
                if len(parts) >= 2 and parts[0].strip() == symbol:
                    try:
                        return {"price": float(parts[1].strip())}
                    except ValueError:
                        pass
    return None


def check_market_alerts(symbol=None, url=None, storage_file=None, threshold=None):
    """
    Проверяет рыночные данные на пороговые значения с использованием MarketParser и db_storage.
    """
    current_price = None
    if url is not None:
        parser = MarketParser(storage_file=storage_file)
        current_price = parser.fetch_price(url)

    loaded_data = load_data(storage_file) if storage_file else {}
    symbol_info = _extract_symbol_info(loaded_data, symbol)

    if current_price is None and symbol_info and "price" in symbol_info:
        current_price = symbol_info["price"]

    if threshold is not None:
        t_price = threshold
        condition = "above"
        if symbol_info:
            t_price = symbol_info.get("threshold", threshold)
            condition = symbol_info.get("condition", "above")

        if current_price is not None:
            if condition == "above":
                return current_price > t_price
            elif condition == "below":
                return current_price < t_price

    if symbol_info and "threshold" in symbol_info:
        t_price = symbol_info["threshold"]
        condition = symbol_info.get("condition", "above")
        if current_price is not None and t_price is not None:
            if condition == "above":
                return current_price > t_price
            elif condition == "below":
                return current_price < t_price

    return False


def trigger_alert_if_needed(symbol, url, storage_file, trigger_condition):
    """
    Генерирует алерт (сохраняет в БД), если условие срабатывания истинно.
    """
    if trigger_condition:
        parser = MarketParser(storage_file=storage_file)
        current_price = parser.fetch_price(url)
        fetch_and_store(symbol, current_price, storage_file=storage_file)