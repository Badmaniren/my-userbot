import skills.market_parser
import skills.db_storage
from skills.market_parser import MarketParser
from skills.db_storage import MarketParser as DBStorageMarketParser


def check_market_threshold(symbol, url, threshold, storage_file=None):
    parser = MarketParser(storage_file)
    price = parser.fetch_price(url)
    parser.fetch_and_store(symbol, price)

    triggered = price > threshold if (price is not None and threshold is not None) else False
    alert = (
        f"Alert: Symbol {symbol} reached price {price}, exceeding threshold {threshold}!"
        if triggered
        else None
    )

    return {
        "triggered": triggered,
        "symbol": symbol,
        "price": price,
        "threshold": threshold,
        "alert": alert,
    }


class MarketThresholdChecker:
    def __init__(self, storage_file=None, threshold=None):
        self.storage_file = storage_file
        self.threshold = threshold
        self.parser = MarketParser(storage_file)
        self.storage = DBStorageMarketParser(storage_file) if storage_file else None

    def check_threshold(self, symbol, url, threshold=None):
        th = threshold if threshold is not None else self.threshold
        price = self.parser.fetch_price(url)
        self.parser.fetch_and_store(symbol, price)
        if self.storage and hasattr(self.storage, 'fetch_and_store'):
            self.storage.fetch_and_store(symbol, price)

        triggered = price > th if (price is not None and th is not None) else False
        alert = (
            f"Alert: Symbol {symbol} reached price {price}, exceeding threshold {th}!"
            if triggered
            else None
        )

        return {
            "triggered": triggered,
            "symbol": symbol,
            "price": price,
            "threshold": th,
            "alert": alert,
        }

    def check_and_alert(self, symbol, url, price_override=None):
        th = self.threshold
        if price_override is not None:
            price = price_override
            self.parser.fetch_and_store(symbol, price)
            if self.storage and hasattr(self.storage, 'fetch_and_store'):
                self.storage.fetch_and_store(symbol, price)
        else:
            price = self.parser.fetch_price(url)
            self.parser.fetch_and_store(symbol, price)
            if self.storage and hasattr(self.storage, 'fetch_and_store'):
                self.storage.fetch_and_store(symbol, price)

        triggered = price > th if (price is not None and th is not None) else False
        alert = (
            f"Alert: Symbol {symbol} reached price {price}, exceeding threshold {th}!"
            if triggered
            else None
        )

        return {
            "triggered": triggered,
            "symbol": symbol,
            "price": price,
            "threshold": th,
            "alert": alert,
        }
