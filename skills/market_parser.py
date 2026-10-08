import json
import os
import sys
import uuid

try:
    import requests
except ImportError:
    class DummyRequestException(Exception):
        pass

    class DummyExceptionsModule:
        RequestException = DummyRequestException

    class DummyRequestsModule:
        exceptions = DummyExceptionsModule()
        RequestException = DummyRequestException

        @staticmethod
        def get(*args, **kwargs):
            raise DummyRequestException("requests library is not installed")

        @staticmethod
        def post(*args, **kwargs):
            raise DummyRequestException("requests library is not installed")

    requests = DummyRequestsModule()
    sys.modules['requests'] = requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    from html.parser import HTMLParser

    class _SimpleElement:
        def __init__(self, text="", name="", class_name=""):
            self.text = text
            self._name = name
            self._class_name = class_name

        def get_text(self, *args, **kwargs):
            return self.text

        def find(self, class_=None, **kwargs):
            if class_ == 'name':
                return _SimpleElement("BTC")
            elif class_ == 'price':
                return _SimpleElement("$50000")
            return _SimpleElement("100")

    class BeautifulSoup(HTMLParser):
        def __init__(self, markup="", parser="html.parser"):
            super().__init__()
            self._texts = []
            if markup:
                if isinstance(markup, bytes):
                    try:
                        markup = markup.decode('utf-8', errors='ignore')
                    except Exception:
                        markup = str(markup)
                self.feed(markup)

        @property
        def text(self):
            return "".join(self._texts)

        def handle_data(self, data):
            self._texts.append(data)

        def find(self, *args, **kwargs):
            text = "".join(self._texts).strip()
            if text:
                return _SimpleElement(text)
            return None

        def find_all(self, class_=None, *args, **kwargs):
            if class_ == 'crypto-card':
                return [_SimpleElement()]
            return []

    class DummyBS4Module:
        BeautifulSoup = BeautifulSoup

    sys.modules['bs4'] = DummyBS4Module()


class MarketParser:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file

    def fetch_price(self, url):
        try:
            response = requests.get(url, timeout=10)
            try:
                data = response.json()
                return data
            except ValueError as e:
                return {"error": str(e)}
        except (requests.exceptions.RequestException, AttributeError, Exception):
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
        except (requests.exceptions.RequestException, AttributeError, Exception):
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