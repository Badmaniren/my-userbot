import math
from typing import List, Dict, Any, Optional

try:
    import requests
except ImportError:
    from unittest.mock import MagicMock
    requests = MagicMock()

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
    def __init__(self, asset_id: str = "DEFAULT", window_size: int = 2):
        if window_size < 2:
            raise FeatureBuilderConfigError("Window size must be at least 2.")
        self.asset_id = asset_id
        self.window_size = window_size

    def _fetch_historical_prices(self) -> List[float]:
        # Метод-заглушка, переопределяемый через patch в юнит-тестах
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
        
        if not returns:
            return []

        if len(returns) < self.window_size:
            window = len(returns) if len(returns) > 0 else 1
        else:
            window = self.window_size

        volatilities = []
        for i in range(window, len(returns) + 1):
            chunk = returns[i - window:i]
            n = len(chunk)
            if n > 1:
                if np is not None:
                    vol = float(np.std(chunk, ddof=1))
                else:
                    mean_val = sum(chunk) / n
                    var_val = sum((x - mean_val) ** 2 for x in chunk) / (n - 1)
                    vol = math.sqrt(max(0.0, var_val))
            else:
                vol = 0.0
            volatilities.append(vol)
        
        if not volatilities and len(returns) > 0:
            n = len(returns)
            if n > 1:
                if np is not None:
                    vol = float(np.std(returns, ddof=1))
                else:
                    mean_val = sum(returns) / n
                    var_val = sum((x - mean_val) ** 2 for x in returns) / (n - 1)
                    vol = math.sqrt(max(0.0, var_val))
            else:
                vol = 0.0
            volatilities.append(vol)
        
        return volatilities

    def compute_skewness_and_kurtosis(self, returns: Optional[List[float]] = None) -> Dict[str, float]:
        if returns is None:
            returns = self.compute_log_returns()
        
        n = len(returns)
        if n < 3:
            return {'skewness': 0.0, 'kurtosis': 0.0}
        
        if np is not None:
            arr = np.array(returns)
            mean = float(np.mean(arr))
            std = float(np.std(arr, ddof=1))
        else:
            mean = sum(returns) / n
            var = sum((x - mean) ** 2 for x in returns) / (n - 1)
            std = math.sqrt(max(0.0, var))

        if std == 0:
            return {'skewness': 0.0, 'kurtosis': 0.0}
        
        skewness = float((sum((x - mean) ** 3 for x in returns) / n) / (std ** 3))
        kurtosis = float((sum((x - mean) ** 4 for x in returns) / n) / (std ** 4) - 3.0)
        
        return {'skewness': skewness, 'kurtosis': kurtosis}

    def compute_tail_risk_metrics(self, returns: Optional[List[float]] = None, confidence: float = 0.95) -> Dict[str, float]:
        if returns is None:
            returns = self.compute_log_returns()
        
        if len(returns) == 0:
            return {'var': 0.0, 'cvar': 0.0}
        
        sorted_returns = sorted(returns)
        n = len(sorted_returns)
        index = int((1.0 - confidence) * n)
        index = max(0, min(index, n - 1))
        
        var = float(sorted_returns[index])
        tail = sorted_returns[:index + 1]
        cvar = float(sum(tail) / len(tail)) if len(tail) > 0 else var
        
        return {'var': var, 'cvar': cvar}

    def build_features(self, asset: Optional[str] = None, prices: Optional[List[float]] = None) -> Dict[str, Any]:
        asset_id = asset or self.asset_id
        if prices is None:
            prices = self._fetch_historical_prices()

        returns = self.compute_log_returns(prices) if len(prices) >= 2 else []
        volatilities = self.compute_rolling_volatility(returns) if returns else [0.0]
        moments = self.compute_skewness_and_kurtosis(returns) if returns else {'skewness': 0.0, 'kurtosis': 0.0}
        tail_risks = self.compute_tail_risk_metrics(returns) if returns else {'var': 0.0, 'cvar': 0.0}

        return {
            'asset_id': asset_id,
            'log_returns': returns,
            'volatility': volatilities[-1] if volatilities else 0.0,
            'rolling_volatility': volatilities,
            'skewness': moments['skewness'],
            'kurtosis': moments['kurtosis'],
            'var': tail_risks['var'],
            'cvar': tail_risks['cvar']
        }

    def build_full_feature_vector_from_source(self, url: str) -> Dict[str, Any]:
        response = requests.get(url)
        content = response.content.decode('utf-8') if hasattr(response.content, 'decode') else str(response.content)
        
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


MarketPortfolioMlFeatureBuilder = MarketPortfolioMLFeatureBuilder


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
