import os
import json
import requests
from bs4 import BeautifulSoup

class MarketParser:
    def __init__(self, storage_file="market_data.json"):
        self.storage_file = storage_file

    def fetch_price(self, url):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                price_span = soup.find(class_='price')
                if price_span:
                    return float(price_span.text)

                # Fallback for alternative HTML structures in tests or general use
                text = response.text
                if "Price:" in text:
                    parts = text.split("Price:")
                    price_str = parts[1].split()[0].strip()
                    return float(price_str)
            return None
        except Exception:
            return None

    def parse_html_prices(self, url):
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return {url: response.text}
        return {}

    def load_data(self, storage_file=None):
        file_path = storage_file or self.storage_file
        if not os.path.exists(file_path):
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return {}
            return json.loads(content)

    def fetch_and_store(self, symbol, price):
        data = self.load_data(self.storage_file)
        data[symbol] = price
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)


class PriceAlerter:
    def __init__(self, parser: MarketParser):
        self.parser = parser

    def check_threshold(self, symbol, new_price, threshold_percent):
        data = self.parser.load_data(self.parser.storage_file)
        raw_old_price = data.get(symbol, new_price)
        if isinstance(raw_old_price, dict):
            old_price = raw_old_price.get("price", new_price)
        else:
            old_price = raw_old_price

        if old_price is None or old_price == 0:
            change_percent = 0.0
        else:
            change_percent = ((new_price - old_price) / old_price) * 100.0

        triggered = abs(change_percent) >= threshold_percent

        message = self.format_notification(symbol, old_price, new_price, change_percent)

        return {
            "triggered": triggered,
            "symbol": symbol,
            "old_price": old_price,
            "new_price": new_price,
            "change_percent": change_percent,
            "message": message
        }

    def format_notification(self, symbol, old_price, new_price, change_percent):
        if new_price > old_price:
            direction = "выросла"
        elif new_price < old_price:
            direction = "упала"
        else:
            direction = "изменилась"
        return f"Внимание! Цена {symbol} {direction} с {old_price} до {new_price} (изменение: {change_percent:.2f}%)"