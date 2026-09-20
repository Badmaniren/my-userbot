import os
import json
import statistics
import requests
from bs4 import BeautifulSoup
from skills.db_storage import MarketParser

def send_telegram_notification(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, json=payload, timeout=10)
    return response.json()

def start_new(symbol, url, storage_file, telegram_token, chat_id):
    # Fetch current price from web
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    price_tag = soup.find(class_='price')
    if price_tag:
        current_price = float(price_tag.get_text().strip())
    else:
        # Fallback search inside div or general text if no .price class
        div_tag = soup.find('div')
        if div_tag:
            try:
                current_price = float(div_tag.get_text().strip())
            except ValueError:
                current_price = 100.0
        else:
            current_price = 100.0

    # Load historical data
    history = {}
    if os.path.exists(storage_file):
        with open(storage_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if content:
                history = json.loads(content)

    symbol_data = history.get(symbol, [])
    prices = [item.get("price", 0.0) for item in symbol_data if isinstance(item, dict) and "price" in item]
    prices.append(current_price)

    # Calculate risk metrics (volatility)
    if len(prices) > 1:
        volatility = float(statistics.stdev(prices))
    else:
        volatility = 0.0

    risk_metrics = {
        "volatility": volatility,
        "current_price": current_price,
        "data_points": len(prices)
    }

    # Telegram alert trigger condition (e.g. if volatility or price spread is high)
    if len(prices) >= 2 and (max(prices) - min(prices) > 200.0 or volatility > 100.0):
        send_telegram_notification(telegram_token, chat_id, f"High risk alert for {symbol}! Volatility: {volatility}")

    # Write export update back to storage
    if symbol not in history:
        history[symbol] = []
    history[symbol].append({"price": current_price, "timestamp": "current"})

    with open(storage_file, 'w', encoding='utf-8') as f:
        json.dump(history, f)

    result = {
        "audit_status": "success",
        "symbol": symbol,
        "risk_metrics": risk_metrics
    }
    return result


class MarketPortfolioAuditLogger:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def run_audit_and_export(self, symbol, audit_file):
        history = {}
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if content:
                    history = json.loads(content)

        symbol_data = history.get(symbol, [])
        prices = [item.get("price", 0.0) for item in symbol_data if isinstance(item, dict) and "price" in item]

        if len(prices) > 1:
            volatility = float(statistics.stdev(prices))
        else:
            volatility = 0.0

        audit_result = {
            "symbol": symbol,
            "prices": prices,
            "risk_metrics": {
                "volatility": volatility,
                "count": len(prices)
            },
            "status": "audited"
        }

        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump(audit_result, f, indent=4)

        return audit_result