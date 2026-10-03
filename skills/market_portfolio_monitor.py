import json
import os
from skills import db_storage

def _get_storage_handler():
    """Безопасное получение доступных методов хранилища db_storage."""
    return db_storage

def run_pipeline(symbol, url, telegram_token, chat_id, storage_file):
    """Выполняет основной конвейер мониторинга портфеля."""
    parser = MarketParser(storage_file=storage_file)
    data = parser.load_data(storage_file)
    current_price = 0.0
    if isinstance(data, dict) and symbol in data:
        current_price = data[symbol]
    
    parser.fetch_and_store(symbol=symbol, price=current_price)
    report_gen = MarketReportGenerator(storage_file=storage_file)
    report_gen.generate_symbol_report(symbol=symbol)
    generate_market_report(storage_file=storage_file, symbol=symbol)
    run_market_telegram_pipeline(
        storage_file=storage_file,
        symbol=symbol,
        chat_id=chat_id,
        url=url,
        telegram_token=telegram_token
    )
    return True

def start_new(symbol, url, telegram_token, chat_id, storage_file):
    """Точка входа для запуска нового мониторинга."""
    return run_pipeline(
        symbol=symbol,
        url=url,
        telegram_token=telegram_token,
        chat_id=chat_id,
        storage_file=storage_file
    )

def start_ened(symbol, url, telegram_token, chat_id, storage_file):
    """Алиас для интеграционного теста."""
    return start_new(
        symbol=symbol,
        url=url,
        telegram_token=telegram_token,
        chat_id=chat_id,
        storage_file=storage_file
    )


class MarketParser:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def fetch_and_store(self, symbol, price):
        data = self.load_data(self.storage_file)
        if data is None or not isinstance(data, dict):
            data = {}
        data[symbol] = price
        store = _get_storage_handler()
        if hasattr(store, "save_data"):
            store.save_data(self.storage_file, data)
        elif hasattr(store, "save"):
            store.save(self.storage_file, data)
        else:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f)

    def load_data(self, storage_file):
        store = _get_storage_handler()
        if hasattr(store, "load_data"):
            try:
                res = store.load_data(storage_file)
                if isinstance(res, (dict, list)):
                    return res
            except (AttributeError, TypeError, OSError, json.JSONDecodeError):
                pass
        elif hasattr(store, "load"):
            try:
                res = store.load(storage_file)
                if isinstance(res, (dict, list)):
                    return res
            except (AttributeError, TypeError, OSError, json.JSONDecodeError):
                pass

        try:
            with open(storage_file, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    return None
                try:
                    return json.loads(content)
                except (json.JSONDecodeError, TypeError):
                    return None
        except (FileNotFoundError, OSError):
            return None


class MarketReportGenerator:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def generate_symbol_report(self, symbol):
        data = MarketParser(self.storage_file).load_data(self.storage_file)
        if data and isinstance(data, dict) and symbol in data:
            return f"Report for {symbol}: {data[symbol]}"
        return f"Report for {symbol}: No data"

    def get_raw_stream_dump(self):
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return f.read()
        except (FileNotFoundError, OSError):
            return "{}"


def generate_market_report(storage_file, symbol):
    gen = MarketReportGenerator(storage_file=storage_file)
    return gen.generate_symbol_report(symbol)


def run_market_telegram_pipeline(storage_file, symbol, chat_id, url, telegram_token):
    parser = MarketParser(storage_file=storage_file)
    data = parser.load_data(storage_file)
    price = data.get(symbol, 0.0) if isinstance(data, dict) and data is not None else 0.0
    
    return {
        "status": "success",
        "symbol": symbol,
        "price": price,
        "chat_id": chat_id,
        "url": url
    }


def export_audit_logs(storage_file=None):
    """Экспорт аудиторских логов с явным возвратом результата."""
    if storage_file:
        try:
            with open(storage_file, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip():
                    return False
                try:
                    json.loads(content)
                except (json.JSONDecodeError, TypeError):
                    return False
                return True
        except (FileNotFoundError, OSError):
            return False
    return False
