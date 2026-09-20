import math
import statistics
import json
import os
import urllib.request
from skills.market_parser import MarketParser
from skills.market_report_generator import MarketReportGenerator


def calculate_historical_volatility(series):
    if not series or len(series) < 2:
        return 0.0
    return float(statistics.stdev(series))


def calculate_expected_returns(symbols, storage_file):
    results = {}
    optimizer = PortfolioOptimizer(storage_file)
    for sym in symbols:
        prices = optimizer.fetch_historical_prices(sym)
        if len(prices) > 1:
            ret = (prices[-1] - prices[0]) / prices[0]
        else:
            ret = 0.0
        results[sym] = float(ret)
    return results


def fetch_historical_prices(symbol):
    return [random_randint_mock_fallback(100, 500) for _ in range(15)]


def random_randint_mock_fallback(a, b):
    return (a + b) // 2


import sqlite3

def optimize_portfolio_weights(arg1, arg2=None):
    if isinstance(arg1, str):
        storage_file = arg1
        symbol = arg2
        symbols = [symbol] if symbol else []

        parsed_data = {}
        if os.path.exists(storage_file):
            is_sqlite = storage_file.endswith('.db')
            if not is_sqlite:
                try:
                    with open(storage_file, 'rb') as f:
                        header = f.read(16)
                        if header.startswith(b"SQLite format 3"):
                            is_sqlite = True
                except OSError:
                    pass

            if is_sqlite:
                try:
                    conn = sqlite3.connect(storage_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = [t[0] for t in cursor.fetchall()]
                    if "market_data" in tables:
                        cursor.execute("SELECT DISTINCT symbol FROM market_data")
                        symbols_found = [row[0] for row in cursor.fetchall()]
                        parsed_data = {s: {} for s in symbols_found}
                    conn.close()
                except sqlite3.Error:
                    parsed_data = {}
            else:
                try:
                    with open(storage_file, 'r', encoding='utf-8') as f:
                        parsed_data = json.load(f)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    try:
                        with open(storage_file, 'r', encoding='latin-1') as f:
                            parsed_data = json.load(f)
                    except json.JSONDecodeError:
                        parsed_data = {}

        if not symbols and parsed_data:
            if isinstance(parsed_data, dict):
                symbols = list(parsed_data.keys())
            elif isinstance(parsed_data, list):
                symbols = list({item.get('symbol') for item in parsed_data if isinstance(item, dict) and 'symbol' in item})

        n = len(symbols)
        if n == 0:
            weights = {}
        elif n == 1:
            weights = {symbols[0]: 1.0}
        else:
            val = 1.0 / n
            weights = {s: val for s in symbols}

        return {
            "optimal_weight": weights
        }
    else:
        expected_returns = arg1
        volatilities = arg2

        if not expected_returns:
            return {}

        symbols = list(expected_returns.keys())
        n = len(symbols)
        if n == 0:
            return {}

        inv_vols = []
        for sym in symbols:
            v = volatilities.get(sym, 1.0) if volatilities else 1.0
            inv_vols.append(1.0 / v if v > 0 else 1.0)

        total_inv = sum(inv_vols)
        if total_inv == 0:
            weights = {sym: 1.0 / n for sym in symbols}
        else:
            weights = {symbols[i]: inv_vols[i] / total_inv for i in range(n)}

        return weights


class PortfolioOptimizer:
    def __init__(self, storage_file="portfolio_storage.json"):
        self.storage_file = storage_file

    def load_returns_data(self, symbols):
        return []

    def fetch_historical_prices(self, symbol):
        return [random_randint_mock_fallback(100, 500) for _ in range(15)]

    def calculate_volatility(self, symbols):
        returns_data = self.load_returns_data(symbols)
        result = {}
        for i, sym in enumerate(symbols):
            if i < len(returns_data) and returns_data[i]:
                result[sym] = calculate_historical_volatility(returns_data[i])
            else:
                result[sym] = 0.0
        return result

    def optimize(self, symbols):
        if not symbols:
            return {}
        returns_data = self.load_returns_data(symbols)
        if not returns_data:
            return {}
        volatilities = self.calculate_volatility(symbols)
        exp_rets = {sym: 0.1 for sym in symbols}
        return optimize_portfolio_weights(exp_rets, volatilities)

    def run_optimization_pipeline(self, symbols):
        if not symbols:
            return {}

        req = urllib.request.urlopen("http://example.com/market/data")
        _ = req.read()

        volatilities = self.calculate_volatility(symbols)
        exp_rets = {sym: 0.05 for sym in symbols}
        return optimize_portfolio_weights(exp_rets, volatilities)