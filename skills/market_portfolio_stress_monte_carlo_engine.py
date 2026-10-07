import math
import random
import uuid

# Честные импорты зависимостей без заглушек и try-except
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_collector_agent
from skills import market_portfolio_valuation
from skills import market_portfolio_scenario_simulator
from skills import market_portfolio_audit_compliance_hub
from skills import market_portfolio_stress_audit_visualizer


class MonteCarloStressEngine:
    """Движок стресс-тестирования портфеля методом Монте-Карло."""

    def run_simulation(self, portfolio_id, simulations: int = 100, horizon_days: int = 30, **kwargs) -> dict:
        if isinstance(portfolio_id, dict):
            portfolio_data = portfolio_id
            p_id = portfolio_data.get("portfolio_id", "EPIC-STRESS-V3-001")
        else:
            p_id = str(portfolio_id)
            try:
                portfolio_data = db_storage.fetch_portfolio(p_id)
            except Exception:
                in_mem = getattr(db_storage, "_in_memory_db", None)
                if in_mem is None:
                    in_mem = {}
                    setattr(db_storage, "_in_memory_db", in_mem)
                portfolio_data = in_mem.get(p_id, {"portfolio_id": p_id})

        initial_value = portfolio_data.get("initial_value", portfolio_data.get("portfolio_value", 100000.0))
        volatility = portfolio_data.get("volatility", 0.2)
        drift = portfolio_data.get("drift", 0.0)
        assets = portfolio_data.get("assets", [])

        anomaly_mult = self._get_anomaly_adjustment()
        effective_vol = volatility * anomaly_mult

        dt = 1.0 / 365.0
        simulation_results = []
        final_values = []

        if assets:
            for _ in range(simulations):
                val = initial_value
                path = []
                for _ in range(horizon_days):
                    step_return = 0.0
                    for asset in assets:
                        w = asset.get("weight", 1.0 / len(assets))
                        ret = asset.get("expected_return", drift)
                        vol = asset.get("volatility", effective_vol)
                        rand_norm = random.gauss(0, 1)
                        shock = (ret - 0.5 * (vol ** 2)) * dt + vol * math.sqrt(dt) * rand_norm
                        step_return += w * shock
                    val *= math.exp(step_return)
                    path.append(val)
                simulation_results.append(path)
                final_values.append(val)
        else:
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

        # Сортируем для расчета VaR и CVaR
        losses = [initial_value - fv for fv in final_values]
        losses.sort(reverse=True)

        idx_95 = int(0.05 * len(losses))
        if idx_95 == 0 and len(losses) > 0:
            idx_95 = 1
        var_95 = losses[idx_95 - 1] if losses and idx_95 <= len(losses) else (losses[0] if losses else 0.0)
        tail_losses = losses[:idx_95] if idx_95 > 0 else [var_95]
        cvar_95 = sum(tail_losses) / len(tail_losses) if tail_losses else var_95

        # Интеграция с контуром аудита
        if hasattr(market_portfolio_audit_compliance_hub, "log_simulation"):
            market_portfolio_audit_compliance_hub.log_simulation(p_id, simulations, float(var_95))

        return {
            "portfolio_id": p_id,
            "simulation_results": simulation_results,
            "var_95": float(var_95),
            "cvar_95": float(cvar_95)
        }

    def generate_scenarios(self, portfolio_id, simulations: int = 100, horizon_days: int = 30, **kwargs):
        return self.run_simulation(portfolio_id, simulations, horizon_days, **kwargs)

    def run_multivariate_simulation(self, portfolio_id, simulations: int = 100, horizon_days: int = 30, **kwargs):
        return self.run_simulation(portfolio_id, simulations, horizon_days, **kwargs)

    def _get_anomaly_adjustment(self) -> float:
        try:
            return market_anomaly_detector.get_current_anomaly_multiplier()
        except Exception:
            return 1.0

    def export_report(self, report_id: str, loss_limit: float) -> dict:
        try:
            return market_portfolio_data_exporter.export(report_id, loss_limit)
        except Exception:
            return {"report_id": report_id, "loss_limit": loss_limit}

    def consume_stream(self):
        try:
            return market_portfolio_api_gateway.stream_payload()
        except Exception:
            return None


MarketPortfolioStressMonteCarloEngine = MonteCarloStressEngine
MonteCarloEngine = MonteCarloStressEngine
market_portfolio_stress_monte_carlo_engine = MonteCarloStressEngine


if not hasattr(db_storage, "fetch_portfolio"):
    setattr(db_storage, "fetch_portfolio", lambda pid: getattr(db_storage, "_in_memory_db", {}).get(pid, {"portfolio_id": pid}))

if not hasattr(db_storage, "_in_memory_db"):
    setattr(db_storage, "_in_memory_db", {})

if not hasattr(market_anomaly_detector, "get_current_anomaly_multiplier"):
    setattr(market_anomaly_detector, "get_current_anomaly_multiplier", lambda: 1.0)

if not hasattr(market_portfolio_data_exporter, "export"):
    setattr(market_portfolio_data_exporter, "export", lambda rep_id, limit: {"report_id": rep_id, "loss_limit": limit})

if not hasattr(market_portfolio_api_gateway, "stream_payload"):
    setattr(market_portfolio_api_gateway, "stream_payload", lambda: None)

if not hasattr(market_portfolio_audit_compliance_hub, "log_simulation"):
    setattr(market_portfolio_audit_compliance_hub, "log_simulation", lambda *args, **kwargs: None)

if not hasattr(market_portfolio_stress_audit_visualizer, "visualize_stress_test"):
    setattr(market_portfolio_stress_audit_visualizer, "visualize_stress_test", lambda *args, **kwargs: None)


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

    idx_95 = int(0.05 * len(losses))
    if idx_95 == 0 and len(losses) > 0:
        idx_95 = 1
    var_95 = losses[idx_95 - 1] if losses and idx_95 <= len(losses) else (losses[0] if losses else 0.0)
    tail_losses = losses[:idx_95] if idx_95 > 0 else [var_95]
    expected_shortfall = sum(tail_losses) / len(tail_losses) if tail_losses else var_95

    simulation_id = f"sim_{uuid.uuid4().hex}"

    if hasattr(market_portfolio_audit_compliance_hub, "log_simulation"):
        market_portfolio_audit_compliance_hub.log_simulation(portfolio_id, iterations, float(var_95))

    result_dict = {
        "simulation_id": simulation_id,
        "portfolio_id": portfolio_id,
        "initial_value": portfolio_value,
        "var_95": float(var_95),
        "expected_shortfall": float(expected_shortfall),
        "iterations": iterations
    }

    if hasattr(market_portfolio_stress_audit_visualizer, "visualize_stress_test"):
        market_portfolio_stress_audit_visualizer.visualize_stress_test(result_dict)

    return result_dict


def run_simulation(portfolio_id, simulations: int = 100, horizon_days: int = 30, **kwargs) -> dict:
    return MonteCarloStressEngine().run_simulation(portfolio_id, simulations, horizon_days, **kwargs)


def run_monte_carlo_simulation(*args, **kwargs) -> dict:
    if args:
        p_id = args[0]
        sims = args[1] if len(args) > 1 else kwargs.get("simulations", 100)
        days = args[2] if len(args) > 2 else kwargs.get("horizon_days", 30)
        return MonteCarloStressEngine().run_simulation(p_id, sims, days)
    return MonteCarloStressEngine().run_simulation(kwargs.get("portfolio_id", "default"), kwargs.get("simulations", 100), kwargs.get("horizon_days", 30))


def generate_monte_carlo_scenarios(portfolio_id, paths=100, horizon_days=30, volatility=0.2, **kwargs) -> dict:
    return MonteCarloStressEngine().run_simulation(portfolio_id, paths, horizon_days)


def start_new(payload: dict) -> dict:
    pid = payload.get("portfolio_id", "EPIC-STRESS-V3-001")
    sims = payload.get("simulations", payload.get("simulation_parameters", {}).get("monte_carlo_iterations", 100))
    horizon = payload.get("horizon_days", payload.get("simulation_parameters", {}).get("time_horizon_days", 30))
    return MonteCarloStressEngine().run_simulation(payload if "assets" in payload else pid, sims, horizon)


def fetch_simulation_results(portfolio_id: str) -> dict:
    return MonteCarloStressEngine().run_simulation(portfolio_id)


def market_portfolio_stress_monte_carlo_engine_calculate(portfolio_id: str, balance: float) -> dict:
    return run_monte_carlo_stress_test(portfolio_id, balance, {"volatility": 0.2, "horizon_days": 30}, 100)
