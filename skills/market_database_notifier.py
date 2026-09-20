from skills.db_storage import MarketParser
from skills.market_telegram_pipeline import run_pipeline, send_telegram_notification


class MarketDatabaseNotifier:
    def __init__(self, storage_file="market_data.db", telegram_token=None, chat_id=None, target_url=None):
        self.storage_file = storage_file
        self.storage_path = storage_file
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.target_url = target_url

        self.db_storage = MarketParser(storage_file)
        self.market_parser = self.db_storage
        self.storage = self.db_storage
        self.parser = self.db_storage

    def _format_data(self, data):
        if isinstance(data, dict):
            return data
        result = {}
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    parts = item.strip().split(',')
                    if len(parts) >= 2:
                        sym = parts[0].strip()
                        try:
                            val = float(parts[1].strip())
                        except (ValueError, TypeError):
                            val = parts[1].strip()
                        result[sym] = val
                elif isinstance(item, dict):
                    sym = item.get('symbol')
                    val = item.get('price')
                    if sym is not None:
                        try:
                            val = float(val)
                        except (ValueError, TypeError):
                            val = 0.0
                        result[sym] = val
                elif isinstance(item, (tuple, list)) and len(item) >= 2:
                    sym = item[0]
                    val = item[1]
                    try:
                        val = float(val)
                    except (ValueError, TypeError):
                        val = 0.0
                    result[sym] = val
        return result

    def notify_on_fetch(self, symbol, url):
        price = self.parser.fetch_price(url)
        if isinstance(price, dict):
            price = price.get("price")
        if price is None:
            price = 0.0
        try:
            price = float(price)
        except (ValueError, TypeError):
            price = 0.0

        self.parser.fetch_and_store(symbol, price)
        message = f"Symbol {symbol} updated with price {price} from {url}"
        run_pipeline(symbol, url, self.telegram_token, self.chat_id, self.storage_file)
        return message

    def check_and_alert(self, symbol=None):
        if symbol is None:
            return self.run_parsing_cycle()
        url = self.target_url or "https://example.com"
        price = self.parser.fetch_price(url)
        if isinstance(price, dict):
            price = price.get("price")
        if price is None:
            price = 0.0
        try:
            price = float(price)
        except (ValueError, TypeError):
            price = 0.0
        self.parser.fetch_and_store(symbol, price)
        data = self.parser.load_data(self.storage_file)
        return self._format_data(data)

    def process_alert(self, symbol=None, target_url=None, price=None):
        if symbol is not None and target_url is not None and price is not None:
            if isinstance(price, dict):
                price = price.get("price")
            if price is None:
                price = 0.0
            try:
                price = float(price)
            except (ValueError, TypeError):
                price = 0.0
            self.parser.fetch_and_store(symbol, price)
            data = self.parser.load_data(self.storage_file)
            return self._format_data(data)

        if symbol is not None:
            return self.check_and_alert(symbol)

        return self.run_parsing_cycle()

    def run_parsing_cycle(self):
        if self.target_url:
            raw = self.parser.parse_html_prices(self.target_url)
            return self._format_data(raw)
        return {}

    def fetch_and_notify(self, symbol, target_url, price):
        if isinstance(price, dict):
            price = price.get("price")
        if price is None:
            price = 0.0
        try:
            price = float(price)
        except (ValueError, TypeError):
            price = 0.0
        self.parser.fetch_and_store(symbol, price)
        data = self.parser.load_data(self.storage_file)
        return self._format_data(data)
