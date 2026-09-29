import json
import os
import uuid
try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class MarketParser:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file

    def fetch_price(self, url):
        if requests is None:
            return None
        try:
            response = requests.get(url, timeout=10)
            try:
                data = response.json()
                return data
            except ValueError as e:
                return {"error": str(e)}
        except Exception:
            return None

    def parse_html_prices(self, url):
        if requests is None or BeautifulSoup is None:
            return []
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            parsed_items = []
            
            cards = soup.find_all(class_='crypto-card')
            for card in cards:
                name_elem = card.find(class_='name')
                price_elem = card.find(class_='price')
                if name_elem and price_elem:
                    parsed_items.append({
                        "symbol": name_elem.get_text().strip(),
                        "price": price_elem.get_text().strip()
                    })
            return parsed_items
        except Exception:
            return []

    def fetch_and_store(self, symbol, price):
        record_id = str(uuid.uuid4())
        data = {}
        
        if self.storage_file and os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                data = {}

        data[symbol] = {
            "price": price,
            "record_id": record_id
        }

        if self.storage_file:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        return record_id

    def load_data(self, filename):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
