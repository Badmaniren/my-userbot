import os
import json
import requests
from bs4 import BeautifulSoup
from skills.market_portfolio_collector_agent import MarketParser
from skills.market_portfolio_valuation import PortfolioValuation


def start_new(storage_file=None, url=None, symbol=None, telegram_token=None, chat_id=None, shifts=None):
    """
    Создает единый модуль аналитической панели для агрегации метрик производительности, отчетов и прогнозов портфеля.
    """
    price = None
    if url:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                price_elem = soup.select_one('.price') or soup.select_one('span.price')
                if price_elem:
                    price = float(price_elem.get_text().strip())
        except (requests.RequestException, ValueError):
            price = None

    data = {}
    if storage_file and os.path.exists(storage_file):
        try:
            with open(storage_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                if content.strip():
                    loaded = json.loads(content)
                    if isinstance(loaded, list):
                        for entry in loaded:
                            s = entry.get('symbol')
                            p = entry.get('price')
                            if s and p is not None:
                                if s not in data:
                                    data[s] = []
                                data[s].append({"price": p, "timestamp": entry.get('timestamp', "current")})
                    elif isinstance(loaded, dict):
                        data = loaded
        except (OSError, json.JSONDecodeError, ValueError, AttributeError):
            data = {}

    if symbol and price is not None:
        if symbol not in data:
            data[symbol] = []
        data[symbol].append({"price": price, "timestamp": "current"})

        if storage_file:
            output_data = []
            for sym, entries in data.items():
                for entry in entries:
                    output_data.append({
                        "symbol": sym,
                        "price": entry["price"],
                        "timestamp": entry.get("timestamp", "current")
                    })
            try:
                with open(storage_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f)
            except (OSError, TypeError, ValueError):
                pass

    if telegram_token and chat_id and price is not None and symbol in data and len(data[symbol]) > 1:
        last_price = data[symbol][-2]["price"]
        if last_price and abs(price - last_price) / last_price > 0.5:
            try:
                requests.post(
                    f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                    json={"chat_id": chat_id, "text": f"Anomaly detected for {symbol}: {price}"},
                    timeout=5
                )
            except requests.RequestException:
                pass

    return data


class MarketPortfolioIntegrationHub:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def run_full_integration_pipeline(self, symbol, url, token, chat_id, shifts):
        return start_new(
            storage_file=self.storage_file,
            url=url,
            symbol=symbol,
            telegram_token=token,
            chat_id=chat_id,
            shifts=shifts
        )