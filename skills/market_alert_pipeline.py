import requests
from skills.market_parser import MarketParser
from skills.db_storage import MarketParser as DBStorage


class MarketAlertPipeline:
    def __init__(self, storage_file=None):
        self.parser = MarketParser()
        self.storage = DBStorage(storage_file=storage_file) if storage_file else DBStorage()
        self.db_storage = self.storage

    def process_and_check(self, symbol, url, threshold):
        current_price = self.parser.fetch_price(url)
        if isinstance(current_price, dict):
            current_price = current_price.get("price", 0.0)
        
        db_threshold = None
        if hasattr(self.storage, 'get_threshold'):
            db_threshold = self.storage.get_threshold(symbol)
            
        active_threshold = db_threshold if db_threshold is not None else threshold

        if current_price < active_threshold:
            alert_data = {
                "symbol": symbol,
                "url": url,
                "price": current_price,
                "threshold": active_threshold
            }
            if hasattr(self.storage, 'save_alert'):
                self.storage.save_alert(alert_data)
            return True
        return False

    def run_batch_pipeline(self, urls):
        all_results = []
        for url in urls:
            response = requests.get(url, stream=True)
            raw_content = response.raw.read()
            parsed_items = self.parser.parse_html_prices(raw_content)
            if parsed_items:
                if hasattr(self.storage, 'fetch_and_store'):
                    self.storage.fetch_and_store(parsed_items)
                all_results.extend(parsed_items)
        return all_results

    def process_alert_check(self, symbol, url, threshold_price):
        current_price = self.parser.fetch_price(url)
        if isinstance(current_price, dict):
            current_price = current_price.get("price", 0.0)
            
        alert_triggered = current_price < threshold_price
        
        if alert_triggered:
            alert_data = {
                "symbol": symbol,
                "url": url,
                "price": current_price,
                "threshold": threshold_price
            }
            if hasattr(self.storage, 'save_alert'):
                self.storage.save_alert(alert_data)
            elif hasattr(self.storage, 'store_alert'):
                self.storage.store_alert(alert_data)
            elif hasattr(self.storage, 'save'):
                self.storage.save(alert_data)
            
        return {
            "alert_triggered": alert_triggered,
            "current_price": current_price
        }


DBStorage = DBStorage