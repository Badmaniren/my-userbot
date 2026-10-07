import hashlib
from datetime import datetime
try:
    import requests
except ImportError:
    requests = None

from skills.db_storage import db_storage as default_db_storage
from skills.market_portfolio_stress_scenario_matrix_evaluator import market_portfolio_stress_scenario_matrix_evaluator
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine


class MarketPortfolioStressDeepImpactAnalyzer:
    def __init__(
        self,
        db_storage=None,
        scenario_evaluator=None,
        monte_carlo_engine=None,
        alert_dispatcher=None,
        **kwargs
    ):
        self.db_storage = db_storage if db_storage is not None else default_db_storage
        self.scenario_evaluator = scenario_evaluator if scenario_evaluator is not None else market_portfolio_stress_scenario_matrix_evaluator
        self.monte_carlo_engine = monte_carlo_engine if monte_carlo_engine is not None else market_portfolio_stress_monte_carlo_engine
        self.alert_dispatcher = alert_dispatcher

    def analyze_deep_impact(self, portfolio_id: str, scenario_code: str, simulations_count: int = 1000, **kwargs):
        if hasattr(self.scenario_evaluator, "evaluate_matrix"):
            try:
                matrix_res = self.scenario_evaluator.evaluate_matrix(portfolio_id, scenario_code)
            except TypeError:
                matrix_res = self.scenario_evaluator.evaluate_matrix(portfolio_id)
        elif callable(self.scenario_evaluator):
            matrix_res = self.scenario_evaluator(portfolio_id, scenario_code)
        else:
            matrix_res = {}

        if not isinstance(matrix_res, dict):
            matrix_res = {}

        if hasattr(self.monte_carlo_engine, "run_simulation"):
            try:
                mc_res = self.monte_carlo_engine.run_simulation(portfolio_id, simulations_count)
            except TypeError:
                mc_res = self.monte_carlo_engine.run_simulation(portfolio_id=portfolio_id, simulations=simulations_count)
        elif callable(self.monte_carlo_engine):
            mc_res = self.monte_carlo_engine(portfolio_id, runs=simulations_count)
        else:
            mc_res = {}

        if not isinstance(mc_res, dict):
            mc_res = {}

        matrix_score = matrix_res.get("matrix_score", 0.0)
        var_95 = mc_res.get("var_95", 0.0)
        status = matrix_res.get("status", "COMPLETED")
        impact_score = round(matrix_score, 4)

        alert_triggered = bool(matrix_score >= 8.0 or status == "CRITICAL_BREACH")

        if alert_triggered and self.alert_dispatcher and hasattr(self.alert_dispatcher, "dispatch_alert"):
            self.alert_dispatcher.dispatch_alert({
                "portfolio_id": portfolio_id,
                "scenario_code": scenario_code,
                "matrix_score": matrix_score,
                "var_95": var_95,
                "status": status
            })

        timestamp = datetime.now().isoformat()

        result = {
            "portfolio_id": portfolio_id,
            "scenario_code": scenario_code,
            "matrix_score": matrix_score,
            "var_95": var_95,
            "impact_score": impact_score,
            "status": status,
            "alert_triggered": alert_triggered,
            "timestamp": timestamp
        }

        if self.db_storage and hasattr(self.db_storage, "save_impact_analysis"):
            self.db_storage.save_impact_analysis(result)
        elif self.db_storage and callable(self.db_storage):
            self.db_storage(f"save_stress_impact_{portfolio_id}", result)

        return result

    def load_external_matrix_stream(self, url: str):
        if requests is None:
            raise RuntimeError("requests library is not available")
        response = requests.get(url, timeout=10)
        stream_bytes = response.content
        stream_hash = hashlib.sha256(stream_bytes).hexdigest()
        raw_bytes_length = len(stream_bytes)
        return {
            "stream_hash": stream_hash,
            "raw_bytes_length": raw_bytes_length
        }


def market_portfolio_stress_deep_impact_analyzer(
    portfolio_id=None,
    matrix_data=None,
    monte_carlo_data=None,
    scenario_code="DEFAULT",
    simulations_count=1000,
    **kwargs
):
    if matrix_data is not None or monte_carlo_data is not None:
        m_data = matrix_data if isinstance(matrix_data, dict) else {}
        mc_data = monte_carlo_data if isinstance(monte_carlo_data, dict) else {}

        matrix_score = m_data.get("matrix_score", 5.0)
        var_95 = mc_data.get("var_95", 10000.0)
        status = m_data.get("status", "COMPLETED")
        impact_score = round(matrix_score, 4)
        alert_triggered = bool(matrix_score >= 8.0 or status == "CRITICAL_BREACH")
        timestamp = datetime.now().isoformat()

        result = {
            "portfolio_id": portfolio_id,
            "scenario_code": scenario_code,
            "matrix_score": matrix_score,
            "var_95": var_95,
            "impact_score": impact_score,
            "status": status,
            "alert_triggered": alert_triggered,
            "timestamp": timestamp
        }

        if hasattr(default_db_storage, "save_impact_analysis"):
            default_db_storage.save_impact_analysis(result)
        elif callable(default_db_storage):
            default_db_storage(f"save_stress_impact_{portfolio_id}", result)

        return result

    analyzer = MarketPortfolioStressDeepImpactAnalyzer(**kwargs)
    return analyzer.analyze_deep_impact(portfolio_id, scenario_code, simulations_count, **kwargs)
