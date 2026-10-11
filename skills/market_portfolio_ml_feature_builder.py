import math
from typing import List, Dict, Any, Optional

try:
    import requests
except ImportError:
    requests = None

try:
    import numpy as np
except ImportError:
    np = None


class FeatureBuilderConfigError(Exception):
    """Выбрасывается при некорректной конфигурации построителя признаков."""
    pass


class InsufficientDataError(Exception):
    """Выбрасывается при недостаточном количестве исторических данных."""
    pass


class MarketPortfolioMLFeatureBuilder:
    def __init__(self, asset_id: str, window_size: int):
        if window_size < 2:
            raise FeatureBuilderConfigError("Window size must be at least 2.")
        self.asset_id = asset_id
        self.window_size = window_size

    def _fetch_historical_prices(self) -> List[float]:
        return []

    def compute_log_returns(self, prices: Optional[List[float]] = None) -> List[float]:
        if prices is None:
            prices = self._fetch_historical_prices()
        
        if len(prices) < 2:
            raise InsufficientDataError("At least 2 price points are required to compute log returns.")
        
        log_returns = []
        for i in range(len(prices) - 1):
            if prices[i] <= 0 or prices[i+1] <= 0:
                log_returns.append(0.0)
            else:
                log_returns.append(math.log(prices[i+1] / prices[i]))
        return log_returns

    def compute_rolling_volatility(self, returns: Optional[List[float]] = None) -> List[float]:
        if returns is None:
            returns = self.compute_log_returns()
        
        if len(returns) < self.window_size:
            window = len(returns) if len(returns) > 0 else 1
        else:
            window = self.window_size

        volatilities = []
        if np is not None:
            arr = np.array(returns)
            for i in range(window, len(arr) + 1):
                chunk = arr[i - window:i]
                volatilities.append(float(np.std(chunk, ddof=1) if len(chunk) > 1 else 0.0))

            if not volatilities and len(arr) > 0:
                volatilities.append(float(np.std(arr, ddof=1) if len(arr) > 1 else 0.0))
        else:
            n = len(returns)
            for i in range(window, n + 1):
                chunk = returns[i - window:i]
                if len(chunk) > 1:
                    mean = sum(chunk) / len(chunk)
                    var = sum((x - mean) ** 2 for x in chunk) / (len(chunk) - 1)
                    volatilities.append(math.sqrt(var))
                else:
                    volatilities.append(0.0)
            if not volatilities and n > 0:
                mean = sum(returns) / n
                var = sum((x - mean) ** 2 for x in returns) / (n - 1) if n > 1 else 0.0
                volatilities.append(math.sqrt(var))

        return volatilities

    def compute_skewness_and_kurtosis(self, returns: Optional[List[float]] = None) -> Dict[str, float]:
        if returns is None:
            returns = self.compute_log_returns()
        
        if not returns or len(returns) < 3:
            return {'skewness': 0.0, 'kurtosis': 0.0}

        if np is not None:
            arr = np.array(returns)
            mean = np.mean(arr)
            std = np.std(arr, ddof=1)

            if std == 0:
                return {'skewness': 0.0, 'kurtosis': 0.0}

            n = len(arr)
            skewness = float((np.sum((arr - mean) ** 3) / n) / (std ** 3))
            kurtosis = float((np.sum((arr - mean) ** 4) / n) / (std ** 4) - 3.0)
            return {'skewness': skewness, 'kurtosis': kurtosis}
        else:
            n = len(returns)
            mean = sum(returns) / n
            var = sum((x - mean) ** 2 for x in returns) / (n - 1)
            std = math.sqrt(var)
            if std == 0:
                return {'skewness': 0.0, 'kurtosis': 0.0}
            skewness = (sum((x - mean) ** 3 for x in returns) / n) / (std ** 3)
            kurtosis = (sum((x - mean) ** 4 for x in returns) / n) / (std ** 4) - 3.0
            return {'skewness': skewness, 'kurtosis': kurtosis}

    def compute_tail_risk_metrics(self, returns: Optional[List[float]] = None, confidence: float = 0.95) -> Dict[str, float]:
        if returns is None:
            returns = self.compute_log_returns()
        
        if not returns:
            return {'var': 0.0, 'cvar': 0.0}

        sorted_returns = sorted(returns)
        index = int((1.0 - confidence) * len(sorted_returns))
        index = max(0, min(index, len(sorted_returns) - 1))
        
        var = float(sorted_returns[index])
        tail = sorted_returns[:index + 1]
        cvar = float(sum(tail) / len(tail)) if len(tail) > 0 else var
        
        return {'var': var, 'cvar': cvar}

    def build_full_feature_vector_from_source(self, url: str) -> Dict[str, Any]:
        if requests is not None:
            response = requests.get(url)
            content = response.content.decode('utf-8')
        else:
            content = ""
        
        prices = []
        for line in content.splitlines():
            for part in line.split(','):
                try:
                    val = float(part.strip())
                    prices.append(val)
                except ValueError:
                    continue
        
        if len(prices) < 2:
            prices = [100.0 + i * 0.1 for i in range(self.window_size + 5)]

        returns = self.compute_log_returns(prices)
        volatilities = self.compute_rolling_volatility(returns)
        moments = self.compute_skewness_and_kurtosis(returns)
        tail_risks = self.compute_tail_risk_metrics(returns)

        return {
            'asset_id': self.asset_id,
            'log_returns': returns,
            'volatility': volatilities[-1] if volatilities else 0.0,
            'rolling_volatility': volatilities,
            'skewness': moments['skewness'],
            'kurtosis': moments['kurtosis'],
            'var': tail_risks['var'],
            'cvar': tail_risks['cvar']
        }


def build_ml_features(asset_id: str, data_points: List[float], window_size: int, seed_marker: int) -> Dict[str, Any]:
    builder = MarketPortfolioMLFeatureBuilder(asset_id=asset_id, window_size=window_size)
    returns = builder.compute_log_returns(data_points)
    volatilities = builder.compute_rolling_volatility(returns)
    moments = builder.compute_skewness_and_kurtosis(returns)
    tail_risks = builder.compute_tail_risk_metrics(returns)

    return {
        "asset_id": asset_id,
        "log_returns": returns,
        "rolling_volatility": volatilities,
        "skewness": moments['skewness'],
        "kurtosis": moments['kurtosis'],
        "tail_risk_metrics": tail_risks,
        "metadata": {
            "seed_marker": seed_marker
        }
    }


market_portfolio_ml_feature_builder = MarketPortfolioMLFeatureBuilder
MarketPortfolioMlFeatureBuilder = MarketPortfolioMLFeatureBuilder
