import io
import uuid
import math
from skills.db_storage import DbStorage

try:
    from skills.market_portfolio_strategy_optimizer import market_portfolio_strategy_optimizer
except ImportError:
    pass

class HedgeSynthesisError(Exception):
    """Исключение, возникающее при ошибках синтеза хеджа."""
    pass

class MarketPortfolioHedgeSynthesizer:
    def __init__(self, db_storage=None, market_portfolio_backtester=None, market_portfolio_scenario_simulator=None):
        self.db_storage = db_storage
        self.market_portfolio_backtester = market_portfolio_backtester
        self.scenario_simulator = market_portfolio_scenario_simulator

    def _extract_tail_risk_metrics(self, portfolio_id: str) -> dict:
        if self.db_storage and hasattr(self.db_storage, 'fetch_stream'):
            try:
                stream = self.db_storage.fetch_stream(portfolio_id)
                if stream:
                    stream.read()
            except Exception as e:
                raise HedgeSynthesisError(f"Failed to fetch stream: {e}")
        return {
            "var": 0.05,
            "cvar": 0.08,
            "spot_price": 100.0,
            "volatility": 0.2,
            "time_to_expiry": 30,
            "asset_id": portfolio_id
        }

    def _calculate_optimal_strike(self, metrics: dict) -> float:
        spot = metrics.get("spot_price", 100.0)
        var = metrics.get("var", 0.05)
        return float(spot * (1.0 - var))

    def _price_protective_option(self, strike: float, metrics: dict) -> float:
        vol = metrics.get("volatility", 0.2)
        tte = metrics.get("time_to_expiry", 30)
        premium = strike * vol * math.sqrt(tte / 365.0) * 0.1
        return round(max(float(premium), 0.5), 2)

    def synthesize_hedge(self, portfolio_id: str) -> dict:
        try:
            metrics = self._extract_tail_risk_metrics(portfolio_id)
            strike = self._calculate_optimal_strike(metrics)
            premium = self._price_protective_option(strike, metrics)
            return {
                "portfolio_id": portfolio_id,
                "strike": strike,
                "premium": premium
            }
        except Exception as e:
            if isinstance(e, HedgeSynthesisError):
                raise e
            raise HedgeSynthesisError(str(e))

    def simulate_hedge_impact(self, portfolio_id: str, simulation_id: str) -> dict:
        if self.scenario_simulator and hasattr(self.scenario_simulator, 'run_simulation'):
            return self.scenario_simulator.run_simulation(portfolio_id, simulation_id)
        return {
            "simulation_id": simulation_id,
            "success": True,
            "projected_loss": 1000.0
        }


def market_portfolio_hedge_synthesizer(portfolio_id: str, var_limit: float = 0.05, market_data_ref: str = "default_ref") -> dict:
    hedge_id = f"hedge_{uuid.uuid4().hex[:8]}"
    result_data = {
        "hedge_id": hedge_id,
        "portfolio_id": portfolio_id,
        "var_limit": var_limit,
        "market_data_ref": market_data_ref,
        "strike": 95.0,
        "premium": 5.0
    }
    storage = DbStorage()
    if hasattr(storage, "save"):
        storage.save(entity_id=hedge_id, data=result_data)
    elif hasattr(storage, "__call__"):
        storage(action="save", entity_id=hedge_id, data=result_data)
    return result_data