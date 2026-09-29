import uuid
from typing import Dict, Any, List, Union

try:
    from skills import market_portfolio_collector_agent, market_anomaly_detector
    from skills.db_storage import DBStorage
except ImportError:
    market_portfolio_collector_agent = None
    market_anomaly_detector = None
    DBStorage = None


def _calculate_var(returns: Any, confidence_level: float = 0.95) -> float:
    if returns is None or len(returns) == 0:
        raise ValueError("No historical data available for portfolio")
    returns_list = [float(x) for x in returns]
    n = len(returns_list)
    if n == 0:
        raise ValueError("No historical data available for portfolio")
    sorted_returns = sorted(returns_list)
    p = (1.0 - float(confidence_level)) * 100.0
    if p <= 0:
        return float(sorted_returns[0])
    if p >= 100:
        return float(sorted_returns[-1])
    k = (n - 1) * (p / 100.0)
    f = int(k)
    c = f + 1 if f + 1 < n else f
    d = k - f
    var_val = sorted_returns[f] + d * (sorted_returns[c] - sorted_returns[f])
    return float(var_val)


def _calculate_cvar(returns: Any, confidence_level: float = 0.95) -> float:
    if returns is None or len(returns) == 0:
        raise ValueError("No historical data available for portfolio")
    returns_list = [float(x) for x in returns]
    var_val = _calculate_var(returns_list, confidence_level)
    tail = [x for x in returns_list if x <= var_val]
    if not tail:
        return float(var_val)
    return float(sum(tail) / len(tail))


def _calculate_max_tail_drawdown(returns: Any) -> float:
    if returns is None or len(returns) == 0:
        return 0.0
    returns_list = [float(x) for x in returns]
    min_return = min(returns_list)
    return float(min_return)


class TailRiskAnalyzer:
    """Анализатор хвостового риска (VaR и CVaR)."""

    def calculate_var(self, returns: Any, confidence_level: float = 0.95) -> float:
        return _calculate_var(returns, confidence_level)

    def calculate_cvar(self, returns: Any, confidence_level: float = 0.95) -> float:
        return _calculate_cvar(returns, confidence_level)

    def compute_raw_metrics(self, returns: Any, confidence_level: float = 0.95) -> Dict[str, float]:
        var_val = self.calculate_var(returns, confidence_level)
        cvar_val = self.calculate_cvar(returns, confidence_level)
        max_tail = _calculate_max_tail_drawdown(returns)
        return {
            'var': var_val,
            'cvar': cvar_val,
            'var_95': var_val,
            'cvar_95': cvar_val,
            'max_tail_drawdown': max_tail
        }

    def calculate_tail_risk(self, returns: Any, confidence_level: float = 0.95) -> Dict[str, float]:
        return self.compute_raw_metrics(returns, confidence_level)

    def analyze(self, portfolio_id: str) -> Dict[str, float]:
        returns = None
        if market_portfolio_collector_agent and hasattr(market_portfolio_collector_agent, "get_historical_returns"):
            returns = market_portfolio_collector_agent.get_historical_returns(portfolio_id)
        if not returns and DBStorage:
            db = DBStorage()
            if hasattr(db, "get_portfolio_history"):
                returns = db.get_portfolio_history(portfolio_id)
        if returns is None or len(returns) == 0:
            raise ValueError("No historical data available for portfolio")

        return self.compute_raw_metrics(returns, 0.95)

    def load_from_stream(self, path: str) -> List[float]:
        with open(path, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')
            clean_content = content.replace('\n', ',').replace('\r', '')
            return [float(x.strip()) for x in clean_content.split(',') if x.strip()]

    def check_risk_status(self, portfolio_id: str) -> Dict[str, Any]:
        if market_anomaly_detector and hasattr(market_anomaly_detector, "check_portfolio"):
            return market_anomaly_detector.check_portfolio(portfolio_id)
        return {"status": "ok", "portfolio_id": portfolio_id}


class MarketPortfolioTailRiskAnalyzer(TailRiskAnalyzer):
    """Интеграционный класс для работы с БД и оценкой портфеля."""

    def __init__(self, confidence_level: float = 0.95, db_storage: Any = None):
        self.confidence_level = confidence_level
        self.db = db_storage if db_storage is not None else (DBStorage() if DBStorage else None)

    def calculate_risk_metrics(self, returns_or_portfolio_id: Any, confidence_level: float = None) -> Dict[str, float]:
        conf = confidence_level if confidence_level is not None else self.confidence_level
        if isinstance(returns_or_portfolio_id, str):
            returns = None
            if self.db and hasattr(self.db, "get_portfolio_history"):
                returns = self.db.get_portfolio_history(returns_or_portfolio_id)
            if not returns and market_portfolio_collector_agent and hasattr(market_portfolio_collector_agent, "get_historical_returns"):
                returns = market_portfolio_collector_agent.get_historical_returns(returns_or_portfolio_id)
            if not returns:
                raise ValueError("Portfolio data not found")
        else:
            returns = returns_or_portfolio_id

        metrics = self.compute_raw_metrics(returns, conf)

        if isinstance(returns_or_portfolio_id, str) and self.db and hasattr(self.db, "save_report"):
            report_id = uuid.uuid4().hex
            self.db.save_report(returns_or_portfolio_id, report_id, metrics)

        return metrics


def market_portfolio_tail_risk_analyzer(
    portfolio_id: str = None,
    returns: Any = None,
    confidence_level: float = 0.95,
    db_storage: Any = None,
    **kwargs
) -> Dict[str, float]:
    """Точка входа модуля оценки хвостовых рисков."""
    analyzer = MarketPortfolioTailRiskAnalyzer(confidence_level=confidence_level, db_storage=db_storage)
    if returns is not None:
        return analyzer.calculate_risk_metrics(returns, confidence_level)
    if portfolio_id is not None:
        return analyzer.calculate_risk_metrics(portfolio_id, confidence_level)
    return {'var': 0.0, 'cvar': 0.0, 'var_95': 0.0, 'cvar_95': 0.0, 'max_tail_drawdown': 0.0}
