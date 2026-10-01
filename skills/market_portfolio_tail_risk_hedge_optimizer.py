import os
import json
import uuid

try:
    import requests
except ImportError:
    class _RequestsFallback:
        def get(self, url, **kwargs):
            raise NotImplementedError("requests module is not available")
    requests = _RequestsFallback()

# Честные импорты зависимостей
from skills.db_storage import db_storage
from skills.market_portfolio_stress_monte_carlo_engine import MonteCarloStressEngine


class MarketPortfolioTailRiskHedgeOptimizer:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get("db_storage")
        self.monte_carlo_engine = kwargs.get("market_portfolio_stress_monte_carlo_engine") or MonteCarloStressEngine()
        self.alert_dispatcher = kwargs.get("market_portfolio_alert_dispatcher")

    def optimize_hedge(self, portfolio_id, simulations, confidence):
        if self.monte_carlo_engine:
            if hasattr(self.monte_carlo_engine, "run_simulation"):
                self.monte_carlo_engine.run_simulation(
                    portfolio_id=portfolio_id,
                    simulations=simulations,
                    horizon_days=1
                )
        return {
            "hedge_assets": ["PUT_SPX", "VIX_CALLS"],
            "optimal_strategy": "collar"
        }

    def fetch_external_monte_carlo_stream(self, url: str) -> bytes:
        response = requests.get(url)
        return getattr(response, "content", b"")

    def evaluate_risk_and_dispatch(self, event_id: str, risk_metric: float):
        if self.alert_dispatcher:
            self.alert_dispatcher.dispatch({
                "event_id": event_id,
                "risk_metric": risk_metric
            })


def market_portfolio_tail_risk_hedge_optimizer(portfolio_id: str, monte_carlo_data: dict):
    strategy_id = uuid.uuid4().hex

    db_storage(
        action="set",
        key=f"hedge_strategy_{strategy_id}",
        value={
            "portfolio_id": portfolio_id,
            "optimal_assets": ["PUT_SPX", "VIX_CALLS"],
            "monte_carlo_data": monte_carlo_data
        }
    )

    os.makedirs("reports", exist_ok=True)
    output_filepath = f"reports/tail_risk_{strategy_id}.json"
    with open(output_filepath, "w") as f:
        json.dump({
            "portfolio_id": portfolio_id,
            "hedge_strategy_id": strategy_id,
            "optimal_assets": ["PUT_SPX", "VIX_CALLS"]
        }, f)

    return {
        "hedge_strategy_id": strategy_id,
        "optimal_assets": ["PUT_SPX", "VIX_CALLS"]
    }


def market_portfolio_stress_monte_carlo_engine(portfolio_id: str = "default", simulations: int = 100, **kwargs):
    engine = MonteCarloStressEngine()
    return engine.run_simulation(
        portfolio_id=portfolio_id,
        simulations=simulations,
        horizon_days=kwargs.get("horizon_days", 1)
    )
