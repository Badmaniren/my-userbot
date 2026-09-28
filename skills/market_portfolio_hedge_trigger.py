import uuid
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from skills.db_storage import DBStorage
except ImportError:
    try:
        from db_storage import DBStorage
    except ImportError:
        DBStorage = None

try:
    from skills.market_portfolio_valuation import MarketPortfolioValuation
except ImportError:
    try:
        from market_portfolio_valuation import MarketPortfolioValuation
    except ImportError:
        MarketPortfolioValuation = None

try:
    from skills.market_portfolio_stress_scenario_pipeline import MarketPortfolioStressScenarioPipeline
except ImportError:
    try:
        from market_portfolio_stress_scenario_pipeline import MarketPortfolioStressScenarioPipeline
    except ImportError:
        MarketPortfolioStressScenarioPipeline = None


class HedgeTrigger:
    def __init__(self, db_storage=None, market_portfolio_performance_analytics=None, valuation=None, stress_pipeline=None):
        self.db_storage = db_storage
        self.analytics = market_portfolio_performance_analytics
        self.valuation = valuation
        self.stress_pipeline = stress_pipeline

    def evaluate_hedge_signal(self, portfolio_id: str, var_limit: float, cvar_limit: float) -> dict:
        if self.analytics is not None:
            metrics = self.analytics.get_tail_risk(portfolio_id)
        else:
            metrics = {"var": 0.0, "cvar": 0.0}

        current_var = metrics.get("var", 0.0)
        current_cvar = metrics.get("cvar", 0.0)

        hedge_required = (current_var > var_limit) or (current_cvar > cvar_limit)

        if hedge_required:
            excess_var = max(0.0, current_var - var_limit)
            excess_cvar = max(0.0, current_cvar - cvar_limit)
            coverage_ratio = float(round(max(excess_var, excess_cvar) * 10.0, 4))
            if coverage_ratio == 0.0:
                coverage_ratio = 0.5
        else:
            coverage_ratio = 0.0

        return {
            'portfolio_id': portfolio_id,
            'hedge_required': hedge_required,
            'coverage_ratio': coverage_ratio
        }

    def log_trigger_event(self, status: str):
        event_id = uuid.uuid4().hex
        event_data = {
            'event_id': event_id,
            'status': status
        }
        if self.db_storage is not None:
            self.db_storage.save_event(event_data)

    def process_external_risk_feed(self, path: str) -> str:
        with open(path, 'rb') as f:
            content = f.read()
        return content.decode('utf-8', errors='ignore')

    def determine_hedge_signal(self, portfolio_id: str, cvar: float, threshold: float) -> dict:
        signal_id = str(uuid.uuid4())
        hedge_required = cvar > threshold
        coverage_ratio = float(round(cvar, 4)) if hedge_required else 0.0

        result = {
            'signal_id': signal_id,
            'portfolio_id': portfolio_id,
            'activation_signal': hedge_required,
            'coverage_ratio': coverage_ratio
        }

        if self.db_storage is not None:
            self.db_storage.save_hedge_signal(portfolio_id, result)

        return result


class MarketPortfolioHedgeTrigger(HedgeTrigger):
    pass