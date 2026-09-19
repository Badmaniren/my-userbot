import requests
from skills.market_parser import MarketParser
from skills.db_storage import DBStorage


class MarketAlertPipeline:
    def __init__(self, storage_file=None):
        self.parser = MarketParser()
        self.storage = DBStorage(storage_file=storage_file) if storage_file else DBStorage()
        self.db_storage = self.storage

    def process_and_check(self, symbol, url, threshold):
        current_price = self.parser.fetch_price(url)
        
        db_threshold = self.storage.get_threshold(symbol)
        active_threshold = db_threshold if db_threshold is not None else threshold

        if current_price < active_threshold:
            alert_data = {
                "symbol": symbol,
                "url": url,
                "price": current_price,
                "threshold": active_threshold
            }
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
                self.storage.fetch_and_store(parsed_items)
                all_results.extend(parsed_items)
        return all_results

    def process_alert_check(self, symbol, url, threshold_price):
        current_price = self.parser.fetch_price(url)
        alert_triggered = current_price < threshold_price
        
        if alert_triggered:
            self.storage.save_alert({
                "symbol": symbol,
                "url": url,
                "price": current_price,
                "threshold": threshold_price
            })
            
        return {
            "alert_triggered": alert_triggered,
            "current_price": current_price
        }