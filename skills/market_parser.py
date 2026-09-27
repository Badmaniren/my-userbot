import json
import os
import uuid
import requests
from bs4 import BeautifulSoup


class MarketParser:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file

    def parse_stream(self, stream):
        if hasattr(stream, 'read'):
            content = stream.read()
        else:
            content = stream

        if isinstance(content, bytes):
            content = content.decode('utf-8')

        ticker = "UNKNOWN"
        volumes = [100000, 120000, 110000, 105000, 115000]
        position_size = 500000

        if isinstance(content, str):
            parts = content.split(',')
            for part in parts:
                if part.startswith('ticker:'):
                    ticker = part.split(':')[1]
                elif part.startswith('vol:'):
                    vol_str = part.split(':')[1]
                    parsed_vols = []
                    for v in vol_str.split(','):
                        v_clean = v.strip()
                        if v_clean:
                            try:
                                parsed_vols.append(float(v_clean))
                            except ValueError:
                                parsed_vols.append(100000.0)
                    if parsed_vols:
                        volumes = parsed_vols
                elif part.startswith('pos:'):
                    try:
                        position_size = float(part.split(':')[1])
                    except ValueError:
                        position_size = 500000.0

        return {
            'ticker': ticker,
            'volumes': volumes,
            'position_size': position_size
        }

    def fetch_price(self, url):
        try:
            response = requests.get(url, timeout=10)
            try:
                data = response.json()
                return data
            except ValueError as e:
                return {"error": str(e)}
        except requests.exceptions.RequestException:
            return None

    def parse_html_prices(self, url):
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
        except requests.exceptions.RequestException:
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


market_parser = MarketParser()
