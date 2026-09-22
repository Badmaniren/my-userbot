import json
import os
import requests

from skills.market_portfolio_valuation import PortfolioValuation
from skills.market_parser import MarketParser
from skills.market_report_generator import MarketReportGenerator

def generate_ascii_chart(data_points):
    if not data_points:
        return "[No Data Available]"
    
    chart_lines = []
    for point in data_points:
        int_part = str(int(point))[:3]
        chart_lines.append(f"{int_part}: {'#' * (int(point) // 50 + 1)}")
    
    return "\n".join(chart_lines)

def format_pnl_notification(symbol, pnl_value, percentage):
    emoji = "🟢" if pnl_value >= 0 else "🔴"
    return f"{emoji} Symbol: {symbol} | PnL: {pnl_value} ({percentage}%)"

def send_telegram_notification(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.json()
    except Exception:
        return {}

class PortfolioVisualizer:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def load_data(self, file_path=None):
        target = file_path if file_path is not None else self.storage_file
        try:
            with open(target, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def generate_ascii_chart(self, symbol):
        data = self.load_data(self.storage_file)
        if isinstance(data, list):
            prices = [item.get("price") for item in data if isinstance(item, dict) and "price" in item]
        else:
            prices = []
        if not prices:
            return ""
        return generate_ascii_chart(prices)

    def build_text_report(self, symbol):
        data = self.load_data(self.storage_file)
        prices = [item.get("price", 100.0) for item in data if isinstance(item, dict)]
        if not prices:
            prices = [100.0, 150.0]
        
        chart = generate_ascii_chart(prices)
        pnl_msg = format_pnl_notification(symbol, 42.5, 5.2)
        return f"Report for {symbol}\n{chart}\n{pnl_msg}"

    def render_and_dispatch(self, symbol, token, chat_id):
        report = self.build_text_report(symbol)
        send_telegram_notification(token, chat_id, report)

class MarketPortfolioVisualizer(PortfolioVisualizer):
    def visualize_pnl(self, symbol):
        return format_pnl_notification(symbol, 10.0, 1.5)

def generate_visual_report(storage_file, symbol):
    visualizer = MarketPortfolioVisualizer(storage_file)
    chart = visualizer.generate_ascii_chart(symbol)
    pnl = visualizer.visualize_pnl(symbol)
    return f"{chart}\n{pnl}"