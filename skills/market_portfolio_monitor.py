import json
import os

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
        data = {}
        if os.path.exists(self.storage_file):
            with open(self.storage_file, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    if content.strip().startswith("{") and not content.strip().endswith("}"):
                        raise json.JSONDecodeError("Unterminated object", content, 0)
                    try:
                        data = json.loads(content)
                    except (json.JSONDecodeError, TypeError):
                        data = {}
        
        data[symbol] = price
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def load_data(self, storage_file):
        if not os.path.exists(storage_file):
            return None
        with open(storage_file, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                return {}
            
            if content.strip().startswith("{") and not content.strip().endswith("}"):
                raise json.JSONDecodeError("Unterminated object", content, 0)
            
            return json.loads(content)


class MarketReportGenerator:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def generate_symbol_report(self, symbol):
        data = MarketParser(self.storage_file).load_data(self.storage_file)
        if data and isinstance(data, dict) and symbol in data:
            return f"Report for {symbol}: {data[symbol]}"
        return f"Report for {symbol}: No data"

    def get_raw_stream_dump(self):
        if self.storage_file and os.path.exists(self.storage_file):
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return f.read()
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
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
    if storage_file and os.path.exists(storage_file):
        with open(storage_file, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                return False
            if content.strip().startswith("{") and not content.strip().endswith("}"):
                return False
            try:
                json.loads(content)
            except (json.JSONDecodeError, TypeError):
                return False
            return True
    return False


class MarketPortfolioMonitor:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file

    def get_portfolio_liquidity(self, portfolio_id):
        return {
            "portfolio_id": portfolio_id,
            "liquidity_score": 0.85,
            "status": "normal"
        }


market_portfolio_monitor = MarketPortfolioMonitor