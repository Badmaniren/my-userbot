import skills.db_storage
import skills.market_parser


class MarketDatabaseNotifier:
    def __init__(self, storage_file=None, target_url=None):
        self.storage_file = storage_file
        self.storage_path = storage_file  # Алиас для поддержки юнит-тестов Архитектора
        self.target_url = target_url

        # Безопасная инициализация внешних классов с учетом возможных различий в сигнатурах конструкторов
        db_cls = getattr(skills.db_storage, 'MarketParser')
        ext_cls = getattr(skills.market_parser, 'MarketParser')

        try:
            self.db_storage = db_cls(storage_file if storage_file is not None else "")
        except TypeError:
            try:
                self.db_storage = db_cls()
            except TypeError:
                self.db_storage = db_cls(storage_file)

        try:
            self.market_parser = ext_cls(storage_file if storage_file is not None else "")
        except TypeError:
            try:
                self.market_parser = ext_cls()
            except TypeError:
                self.market_parser = ext_cls(storage_file)

        # Поддержка алиасов для удовлетворения обоим наборам тестов
        self.storage = self.db_storage
        self.parser = self.market_parser

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
                            pass
                        result[sym] = val
                elif isinstance(item, (tuple, list)) and len(item) >= 2:
                    sym = item[0]
                    val = item[1]
                    try:
                        val = float(val)
                    except (ValueError, TypeError):
                        pass
                    result[sym] = val
        return result

    def check_and_alert(self, symbol=None):
        if symbol is None:
            return self.run_parsing_cycle()
        price = self.market_parser.fetch_price(self.target_url)
        if isinstance(price, dict):
            price = price.get("price", price)
        if price is not None:
            try:
                price = float(price)
            except (ValueError, TypeError):
                pass
        self.db_storage.fetch_and_store(symbol, price)
        data = self.db_storage.load_data(self.storage_file)
        return self._format_data(data)

    def process_alert(self, symbol=None, target_url=None, price=None):
        if symbol is not None and target_url is not None and price is not None:
            if isinstance(price, dict):
                price = price.get("price", price)
            if price is not None:
                try:
                    price = float(price)
                except (ValueError, TypeError):
                    pass
            self.db_storage.fetch_and_store(symbol, price)
            data = self.db_storage.load_data(self.storage_file)
            return self._format_data(data)

        if symbol is not None:
            return self.check_and_alert(symbol)

        return self.run_parsing_cycle()

    def run_parsing_cycle(self):
        if self.target_url:
            raw = self.market_parser.parse_html_prices(self.target_url)
            return self._format_data(raw)
        return {}

    def fetch_and_notify(self, symbol, target_url, price):
        if isinstance(price, dict):
            price = price.get("price", price)
        if price is not None:
            try:
                price = float(price)
            except (ValueError, TypeError):
                pass
        self.db_storage.fetch_and_store(symbol, price)
        data = self.db_storage.load_data(self.storage_file)
        return self._format_data(data)
