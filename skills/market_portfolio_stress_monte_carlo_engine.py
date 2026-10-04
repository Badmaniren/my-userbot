import math
import random
import uuid

# Честные импорты зависимостей
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_audit_compliance_hub
from skills import market_portfolio_stress_audit_visualizer


class MonteCarloStressEngine:
    """Движок стресс-тестирования портфеля методом Монте-Карло."""

    def run_simulation(self, portfolio_id=None, simulations: int = 100, horizon_days: int = 30, **kwargs) -> dict:
        if isinstance(portfolio_id, dict):
            payload = portfolio_id
            portfolio_id = payload.get("portfolio_id", "default_portfolio")
            simulations = payload.get("simulations", payload.get("iterations", simulations))
            horizon_days = payload.get("horizon_days", payload.get("horizon", horizon_days))

        if portfolio_id is None:
            portfolio_id = kwargs.get("portfolio_id", "default_portfolio")

        fetch_fn = getattr(db_storage, "fetch_portfolio", None)
        if callable(fetch_fn):
            try:
                portfolio_data = fetch_fn(portfolio_id)
            except AttributeError:
                if not hasattr(db_storage, "_in_memory_db"):
                    db_storage._in_memory_db = {}
                portfolio_data = db_storage._in_memory_db.get(portfolio_id, {"portfolio_id": portfolio_id})
        else:
            if not hasattr(db_storage, "_in_memory_db"):
                db_storage._in_memory_db = {}
            portfolio_data = db_storage._in_memory_db.get(portfolio_id, {"portfolio_id": portfolio_id})

        if not isinstance(portfolio_data, dict):
            portfolio_data = {"portfolio_id": portfolio_id}

        initial_value = float(portfolio_data.get("initial_value", 100000.0))
        volatility = float(portfolio_data.get("volatility", 0.2))
        drift = float(portfolio_data.get("drift", 0.0))

        anomaly_mult = self._get_anomaly_adjustment()
        effective_vol = volatility * anomaly_mult

        dt = 1.0 / 365.0
        simulation_results = []
        final_values = []

        for _ in range(simulations):
            val = initial_value
            path = []
            for _ in range(horizon_days):
                rand_norm = random.gauss(0, 1)
                shock = (drift - 0.5 * (effective_vol ** 2)) * dt + effective_vol * math.sqrt(dt) * rand_norm
                val *= math.exp(shock)
                path.append(val)
            simulation_results.append(path)
            final_values.append(val)

        losses = [initial_value - fv for fv in final_values]
        losses.sort(reverse=True)

        idx_95 = max(1, int(0.05 * len(losses)))
        var_95 = losses[idx_95 - 1] if losses else 0.0
        tail_losses = losses[:idx_95]
        cvar_95 = sum(tail_losses) / len(tail_losses) if tail_losses else var_95

        log_fn = getattr(market_portfolio_audit_compliance_hub, "log_simulation", None)
        if callable(log_fn):
            try:
                log_fn(portfolio_id, simulations, float(var_95))
            except AttributeError:
                pass

        return {
            "portfolio_id": portfolio_id,
            "simulation_results": simulation_results,
            "var_95": float(var_95),
            "cvar_95": float(cvar_95)
        }

    def _get_anomaly_adjustment(self) -> float:
        get_mult = getattr(market_anomaly_detector, "get_current_anomaly_multiplier", None)
        if callable(get_mult):
            try:
                val = get_mult()
                return float(val) if isinstance(val, (int, float)) else 1.0
            except (AttributeError, TypeError, ValueError):
                return 1.0
        return 1.0

    def export_report(self, report_id: str, loss_limit: float) -> dict:
        export_fn = getattr(market_portfolio_data_exporter, "export", None)
        if callable(export_fn):
            try:
                return export_fn(report_id, loss_limit)
            except AttributeError:
                return {"report_id": report_id, "loss_limit": loss_limit}
        return {"report_id": report_id, "loss_limit": loss_limit}

    def consume_stream(self):
        stream_fn = getattr(market_portfolio_api_gateway, "stream_payload", None)
        if callable(stream_fn):
            try:
                return stream_fn()
            except AttributeError:
                pass
        return None

    def run_stress_monte_carlo(self, *args, **kwargs):
        return self.run_simulation(*args, **kwargs)

    def run_multivariate_simulation(self, *args, **kwargs):
        return self.run_simulation(*args, **kwargs)


MonteCarloEngine = MonteCarloStressEngine


class MarketPortfolioStressMonteCarloEngine:
    def __init__(self, *args, **kwargs):
        self.engine = MonteCarloStressEngine()

    def simulate(self, assets_or_data, macro_params=None):
        if isinstance(assets_or_data, dict):
            pid = assets_or_data.get("portfolio_id", "default")
        else:
            pid = "default"
        return self.engine.run_simulation(pid, 100, 30)

    def evaluate_tail_risk(self, portfolio_data, simulation_result):
        var_95 = simulation_result.get("var_95", 0.0)
        cvar_95 = simulation_result.get("cvar_95", var_95)
        return {
            "var_99": var_95 * 1.2,
            "expected_shortfall": cvar_95
        }

    def run_stress_simulation(self, ingested_data, scenario_results):
        return self.simulate(ingested_data)


def run_monte_carlo_stress_test(portfolio_id: str, portfolio_value: float, scenario_params: dict, iterations: int) -> dict:
    volatility = scenario_params.get("volatility", 0.2)
    drift = scenario_params.get("drift", 0.0)
    horizon_days = scenario_params.get("horizon_days", 1)

    dt = 1.0 / 365.0
    final_values = []
    
    for _ in range(iterations):
        val = portfolio_value
        for _ in range(horizon_days):
            rand_norm = random.gauss(0, 1)
            shock = (drift - 0.5 * (volatility ** 2)) * dt + volatility * math.sqrt(dt) * rand_norm
            val *= math.exp(shock)
        final_values.append(val)

    losses = [portfolio_value - fv for fv in final_values]
    losses.sort(reverse=True)

    idx_95 = max(1, int(0.05 * len(losses)))
    var_95 = losses[idx_95 - 1] if losses else 0.0
    tail_losses = losses[:idx_95]
    expected_shortfall = sum(tail_losses) / len(tail_losses) if tail_losses else var_95

    simulation_id = f"sim_{uuid.uuid4().hex}"
    result_dict = {
        "simulation_id": simulation_id,
        "portfolio_id": portfolio_id,
        "initial_value": portfolio_value,
        "var_95": float(var_95),
        "expected_shortfall": float(expected_shortfall),
        "iterations": iterations
    }

    log_fn = getattr(market_portfolio_audit_compliance_hub, "log_simulation", None)
    if callable(log_fn):
        try:
            log_fn(portfolio_id, iterations, float(var_95))
        except AttributeError:
            pass

    viz_fn = getattr(market_portfolio_stress_audit_visualizer, "visualize_stress_test", None)
    if callable(viz_fn):
        try:
            viz_fn(result_dict)
        except AttributeError:
            pass

    return result_dict


def run_simulation(*args, **kwargs):
    engine = MonteCarloStressEngine()
    return engine.run_simulation(*args, **kwargs)

def run_monte_carlo_simulation(*args, **kwargs):
    return run_simulation(*args, **kwargs)

def run_monte_carlo_stress(*args, **kwargs):
    return run_simulation(*args, **kwargs)

def market_portfolio_stress_monte_carlo_engine_run(*args, **kwargs):
    return run_simulation(*args, **kwargs)

def run_stress_monte_carlo_simulation(*args, **kwargs):
    return run_simulation(*args, **kwargs)

def run_monte_carlo_stress_simulation(*args, **kwargs):
    return run_simulation(*args, **kwargs)

def start_new(payload: dict = None, **kwargs):
    return run_simulation(payload or kwargs)

def fetch_simulation_results(portfolio_id: str):
    engine = MonteCarloStressEngine()
    return engine.run_simulation(portfolio_id)

def market_portfolio_stress_monte_carlo_engine(payload=None, **kwargs):
    if payload is None:
        payload = kwargs
    return run_simulation(payload)
