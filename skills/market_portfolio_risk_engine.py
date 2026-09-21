import json
import math
import statistics
import ast

class RiskEngine:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def load_data(self, storage_file=None):
        path = storage_file or self.storage_file
        with open(path, 'r') as f:
            content = f.read().strip()

        try:
            data = ast.literal_eval(content)
        except Exception:
            data = json.loads(content)

        if isinstance(data, dict):
            if len(data) == 1:
                return list(data.values())[0]
            return data
        return data

    def _get_prices_for_symbol(self, data, symbol):
        if isinstance(data, dict):
            if symbol in data:
                val = data[symbol]
                if isinstance(val, list):
                    prices = []
                    for item in val:
                        if isinstance(item, (int, float)):
                            prices.append(float(item))
                        elif isinstance(item, dict) and 'price' in item:
                            prices.append(float(item['price']))
                    return prices
                elif isinstance(val, (int, float)):
                    return [float(val)]
                elif isinstance(val, dict) and 'price' in val:
                    return [float(val['price'])]
            if 'price' in data and (data.get('symbol') == symbol or 'symbol' not in data):
                return [float(data['price'])]
            return []

        if isinstance(data, list):
            prices = []
            for item in data:
                if isinstance(item, dict):
                    if (item.get('symbol') == symbol or 'symbol' not in item) and 'price' in item:
                        prices.append(float(item['price']))
                elif isinstance(item, (int, float)):
                    prices.append(float(item))
            return prices

        return []

    def calculate_volatility(self, symbol):
        data = self.load_data(self.storage_file)
        prices = self._get_prices_for_symbol(data, symbol)

        if not prices or len(prices) < 2:
            raise ValueError("Insufficient data for volatility calculation")

        returns = [math.log(prices[i]) - math.log(prices[i - 1]) for i in range(1, len(prices))]
        return float(statistics.pstdev(returns))

    def calculate_var(self, symbol, confidence=0.95):
        data = self.load_data(self.storage_file)
        raw_data = self._get_prices_for_symbol(data, symbol)

        if not raw_data:
            raise ValueError("No data available")

        if any(x < 0 for x in raw_data):
            returns = list(raw_data)
        elif any(x > 1 for x in raw_data):
            if len(raw_data) < 2:
                raise ValueError("Insufficient data for return calculation")
            returns = [math.log(raw_data[i]) - math.log(raw_data[i - 1]) for i in range(1, len(raw_data))]
        else:
            returns = list(raw_data)

        if len(returns) == 0:
            raise ValueError("No returns available")

        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        index = max(0, min(index, len(sorted_returns) - 1))
        return float(sorted_returns[index])

    def calculate_risk_metrics(self, symbol):
        try:
            vol = self.calculate_volatility(symbol)
        except ValueError:
            vol = 0.0

        try:
            var = self.calculate_var(symbol, 0.95)
        except ValueError:
            var = 0.0

        return {
            'volatility': vol,
            'var': var
        }
