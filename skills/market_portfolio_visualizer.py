import json
import os
import sqlite3

try:
    from skills.market_parser import MarketParser
except ImportError:
    from skills.db_storage import MarketParser

from skills.market_portfolio_valuation import PortfolioValuation
from skills.market_report_generator import MarketReportGenerator

class PortfolioVisualizer:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def load_data(self, storage_path: str = None):
        path = storage_path or self.storage_file
        if not os.path.exists(path):
            return []

        try:
            with open(path, "rb") as f:
                header = f.read(16)
            if header.startswith(b"SQLite format 3"):
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT symbol, price FROM market_data")
                    rows = cursor.fetchall()
                    return [{"symbol": row[0], "price": float(row[1])} for row in rows]
                except sqlite3.Error:
                    return []
                finally:
                    conn.close()
        except OSError:
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="latin-1", errors="ignore") as f:
                    content = f.read()
            except Exception:
                return []

        if not content:
            return []
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return []

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if "price" in data and not isinstance(data.get("price"), (dict, list)):
                return [data]

            result = []
            for k, v in data.items():
                if isinstance(v, dict) and "price" in v:
                    item = {"symbol": k}
                    item.update(v)
                    result.append(item)
                elif isinstance(v, list):
                    for sub in v:
                        if isinstance(sub, dict):
                            item = {"symbol": k}
                            item.update(sub)
                            result.append(item)
                        elif isinstance(sub, (int, float)):
                            result.append({"symbol": k, "price": float(sub)})
            if result:
                return result
            return [data]
        return []

    def generate_chart(self, symbol: str) -> str:
        data = self.load_data(self.storage_file)
        filtered = [item for item in data if item.get("symbol") == symbol]
        if not filtered:
            filtered = [item for item in data if "price" in item and "symbol" not in item]
        if not filtered:
            filtered = [item for item in data if "price" in item]
        if not filtered:
            return "NO DATA"
        prices = [item.get("price") for item in filtered if item.get("price") is not None]
        if not prices:
            return "NO DATA"
        return generate_ascii_chart(prices)


def generate_ascii_chart(data_points: list) -> str:
    if not data_points:
        return "NO DATA"
    lines = []
    min_val = min(data_points)
    max_val = max(data_points)
    span = max_val - min_val if max_val != min_val else 1.0

    for val in data_points:
        int_val = int(val)
        bar_len = int(((val - min_val) / span) * 10) + 1
        bar = "#" * bar_len
        lines.append(f"{int_val} | {bar}")
    return "\n".join(lines)


def render_text_trend(data_points: list) -> str:
    if len(data_points) < 2:
        return "FLAT Trend"
    first = data_points[0]
    last = data_points[-1]
    if last > first:
        return "UP Trend (Positive Growth)"
    elif last < first:
        return "DOWN Trend (Negative Growth)"
    else:
        return "FLAT Trend"