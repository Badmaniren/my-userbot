import uuid
from typing import Dict, Any, List, Union

from skills import market_portfolio_collector_agent, market_anomaly_detector
from skills.db_storage import DBStorage
from skills.market_portfolio_valuation import PortfolioValuation


def _calculate_var(returns: Any, confidence_level: float) -> float:
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


def _calculate_cvar(returns: Any, confidence_level: float) -> float:
    if returns is None or len(returns) == 0:
        raise ValueError("No historical data available for portfolio")
    returns_list = [float(x) for x in returns]
    var_val = _calculate_var(returns_list, confidence_level)
    tail = [x for x in returns_list if x <= var_val]
    if not tail:
        return float(var_val)
    return float(sum(tail) / len(tail))


class TailRiskAnalyzer:
    """Анализатор хвостового риска (VaR и CVaR)."""

    def calculate_var(self, returns: Any, confidence_level: float = 0.95) -> float:
        return _calculate_var(returns, confidence_level)

    def calculate_cvar(self, returns: Any, confidence_level: float = 0.95) -> float:
        return _calculate_cvar(returns, confidence_level)

    def compute_raw_metrics(self, returns: Any, confidence_level: float = 0.95) -> Dict[str, float]:
        return {
            'var': self.calculate_var(returns, confidence_level),
            'cvar': self.calculate_cvar(returns, confidence_level)
        }

    def calculate_tail_risk(self, returns: Any, confidence_level: float = 0.95) -> Dict[str, float]:
        return self.compute_raw_metrics(returns, confidence_level)

    def analyze(self, portfolio_id: str) -> Dict[str, float]:
        returns = None
        if hasattr(market_portfolio_collector_agent, "get_historical_returns"):
            returns = market_portfolio_collector_agent.get_historical_returns(portfolio_id)
        if not returns:
            db = DBStorage()
            returns = db.get_portfolio_history(portfolio_id)
        if returns is None or len(returns) == 0:
            raise ValueError("No historical data available for portfolio")

        return {
            'var': self.calculate_var(returns, 0.95),
            'cvar': self.calculate_cvar(returns, 0.95)
        }

    def load_from_stream(self, path: str) -> List[float]:
        with open(path, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')
            clean_content = content.replace('\n', ',').replace('\r', '')
            return [float(x.strip()) for x in clean_content.split(',') if x.strip()]

    def check_risk_status(self, portfolio_id: str) -> Dict[str, Any]:
        if hasattr(market_anomaly_detector, "check_portfolio"):
            return market_anomaly_detector.check_portfolio(portfolio_id)
        return {"status": "ok", "portfolio_id": portfolio_id}


class MarketPortfolioTailRiskAnalyzer(TailRiskAnalyzer):
    """Интеграционный класс для работы с БД и оценкой портфеля."""

    def __init__(self, db_storage: DBStorage = None):
        self.db = db_storage if db_storage is not None else DBStorage()

    def calculate_risk_metrics(self, portfolio_id: str, confidence_level: float = 0.95) -> Dict[str, float]:
        returns = self.db.get_portfolio_history(portfolio_id)
        if not returns:
            raise ValueError("Portfolio data not found")

        var = self.calculate_var(returns, confidence_level)
        cvar = self.calculate_cvar(returns, confidence_level)

        report_id = uuid.uuid4().hex
        self.db.save_report(portfolio_id, report_id, {'var': var, 'cvar': cvar})

        return {'var': var, 'cvar': cvar}


def market_portfolio_tail_risk_analyzer(portfolio_id: str = None, returns: Any = None, confidence_level: float = 0.95, db_storage: Any = None, **kwargs) -> Dict[str, float]:
    """Точка входа модуля оценки хвостовых рисков."""
    analyzer = MarketPortfolioTailRiskAnalyzer(db_storage=db_storage)
    if returns is not None:
        return analyzer.compute_raw_metrics(returns, confidence_level)
    if portfolio_id is not None:
        return analyzer.calculate_risk_metrics(portfolio_id, confidence_level)
    return {'var': 0.0, 'cvar': 0.0}
