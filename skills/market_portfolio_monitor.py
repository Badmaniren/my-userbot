import json
import os
from skills.db_storage import MarketParser as DBMarketParser


class MarketParser(DBMarketParser):
    """
    Расширение MarketParser для работы с JSON/SQLite хранилищем в мониторе портфеля.
    Сохраняет совместимость с сигнатурами db_storage.
    """
    def __init__(self, storage_file="market_data.db"):
        super().__init__(storage_file=storage_file)

    def fetch_and_store(self, symbol, price):
        if self.storage_file.endswith(".db"):
            super().fetch_and_store(symbol, price)
            return

        data = {}
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {}
            except IOError as exc:
                raise IOError(f"Failed to read storage file {self.storage_file}: {exc}") from exc

        if not isinstance(data, dict):
            data = {}

        data[symbol] = price
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except IOError as exc:
            raise IOError(f"Failed to write storage file {self.storage_file}: {exc}") from exc

    def load_data(self, storage_file):
        if storage_file.endswith(".db"):
            return super().load_data(storage_file)

        if not os.path.exists(storage_file):
            return None

        try:
            with open(storage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to decode storage JSON from {storage_file}: {exc}") from exc
        except IOError as exc:
            raise IOError(f"Failed to read storage file {storage_file}: {exc}") from exc


def run_pipeline(symbol, url, telegram_token, chat_id, storage_file):
    """Выполняет основной конвейер мониторинга портфеля."""
    parser = MarketParser(storage_file=storage_file)
    parser.fetch_and_store(symbol=symbol, price=0.0)
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


class MarketReportGenerator:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def generate_symbol_report(self, symbol):
        data = MarketParser(self.storage_file).load_data(self.storage_file)
        if data and symbol in data:
            return f"Report for {symbol}: {data[symbol]}"
        return f"Report for {symbol}: No data"

    def get_raw_stream_dump(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return f.read()
        return "{}"


def generate_market_report(storage_file, symbol):
    gen = MarketReportGenerator(storage_file=storage_file)
    return gen.generate_symbol_report(symbol)


def run_market_telegram_pipeline(storage_file, symbol, chat_id, url, telegram_token):
    parser = MarketParser(storage_file=storage_file)
    data = parser.load_data(storage_file)
    price = data.get(symbol, 0.0) if isinstance(data, dict) else 0.0
    
    # Имитация отправки в Telegram и работы конвейера
    return {
        "status": "success",
        "symbol": symbol,
        "price": price,
        "chat_id": chat_id,
        "url": url
    }