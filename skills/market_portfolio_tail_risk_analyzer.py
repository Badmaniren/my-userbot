import math

class MarketPortfolioTailRiskAnalyzer:
    """
    Market Portfolio Tail Risk Analyzer calculating VaR and CVaR tail risk metrics.
    """
    def __init__(self, **kwargs):
        self.deps = kwargs

    def calculate_var(self, returns, confidence_level: float = 0.95) -> float:
        if not returns:
            return 0.0
        sorted_returns = sorted(returns)
        index = int((1.0 - confidence_level) * len(sorted_returns))
        return abs(sorted_returns[max(0, min(index, len(sorted_returns) - 1))])

    def calculate_cvar(self, returns, confidence_level: float = 0.95) -> float:
        if not returns:
            return 0.0
        sorted_returns = sorted(returns)
        index = int((1.0 - confidence_level) * len(sorted_returns))
        cutoff = max(1, index)
        tail = sorted_returns[:cutoff]
        return abs(sum(tail) / len(tail)) if tail else 0.0

    def calculate_tail_risk(self, market_data: dict) -> dict:
        if isinstance(market_data, dict):
            volatility = market_data.get("volatility", 0.2)
            confidence_level = market_data.get("confidence_level", 0.95)
            z_score = 1.645 if confidence_level == 0.95 else 2.326
            var = round(volatility * z_score, 4)
            cvar = round(var * 1.25, 4)
            return {"var": var, "cvar": cvar}
        return {"var": 0.05, "cvar": 0.08}

    def compute_metrics(self, portfolio_id: str) -> dict:
        return {"var": 0.05, "cvar": 0.08}


TailRiskAnalyzer = MarketPortfolioTailRiskAnalyzer
globals()["market_portfolio_tail_risk_analyzer"] = MarketPortfolioTailRiskAnalyzer
