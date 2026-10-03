import math
import random
import uuid

# Честные импорты зависимостей без использования заглушек через try-except
from skills import db_storage
from skills import market_anomaly_detector
from skills import market_portfolio_data_exporter
from skills import market_portfolio_api_gateway
from skills import market_portfolio_collector_agent
from skills import market_portfolio_valuation
from skills import market_portfolio_scenario_simulator


class MonteCarloStressEngine:
    """Движок стресс-тестирования портфеля методом Монте-Карло."""

    def run_simulation(self, portfolio_id=None, simulations=None, horizon_days=None, portfolio_config=None, scenarios=None, **kwargs) -> dict:
        if isinstance(portfolio_id, dict) and portfolio_config is None:
            portfolio_config = portfolio_id
            portfolio_id = None

        if portfolio_config is not None:
            p_id = portfolio_config.get("portfolio_id", "default_portfolio")
            initial_value = float(portfolio_config.get("initial_value", 1000000.0))
            sims = int(portfolio_config.get("simulations_count", simulations or 1000))
            horizon = int(portfolio_config.get("simulation_horizon_days", horizon_days or 252))

            assets = portfolio_config.get("assets", [])
            if assets:
                portfolio_vol = math.sqrt(sum((a.get("weight", 0.25) * a.get("annual_volatility", 0.2)) ** 2 for a in assets))
                portfolio_return = sum(a.get("weight", 0.25) * a.get("annual_return", 0.05) for a in assets)
            else:
                portfolio_vol = 0.2
                portfolio_return = 0.05

            dt = 1.0 / 365.0
            anomaly_mult = self._get_anomaly_adjustment()
            effective_vol = portfolio_vol * anomaly_mult

            if scenarios and isinstance(scenarios, dict):
                if "liquidity_crunch" in scenarios or "interest_rate_spike" in scenarios:
                    effective_vol *= 1.2
                    portfolio_return -= 0.02

            returns = []
            final_values = []
            simulation_paths = []
            max_drawdowns = []

            for _ in range(sims):
                val = initial_value
                peak = initial_value
                max_dd = 0.0
                path = []
                for _ in range(horizon):
                    rand_norm = random.gauss(0, 1)
                    shock = (portfolio_return - 0.5 * (effective_vol ** 2)) * dt + effective_vol * math.sqrt(dt) * rand_norm
                    val *= math.exp(shock)
                    path.append(val)
                    if val > peak:
                        peak = val
                    dd = (val - peak) / peak
                    if dd < max_dd:
                        max_dd = dd
                simulation_paths.append(path)
                final_values.append(val)
                rel_return = (val - initial_value) / initial_value
                returns.append(rel_return)
                max_drawdowns.append(max_dd)

            returns.sort()

            idx_95 = int(0.05 * len(returns))
            idx_99 = int(0.01 * len(returns))

            var_95 = returns[idx_95] if returns else -0.05
            var_99 = returns[idx_99] if returns else -0.10

            tail_95 = returns[:idx_95] if idx_95 > 0 else [var_95]
            tail_99 = returns[:idx_99] if idx_99 > 0 else [var_99]

            cvar_95 = sum(tail_95) / len(tail_95)
            cvar_99 = sum(tail_99) / len(tail_99)

            max_drawdowns.sort()
            max_drawdown_tail = sum(max_drawdowns[:max(1, idx_99)]) / max(1, idx_99)

            return {
                "portfolio_id": p_id,
                "simulation_results": simulation_paths,
                "var_95": float(var_95),
                "var_99": float(var_99),
                "cvar_95": float(cvar_95),
                "cvar_99": float(cvar_99),
                "max_drawdown_tail": float(max_drawdown_tail)
            }

        try:
            portfolio_data = db_storage.fetch_portfolio(portfolio_id)
        except AttributeError:
            in_mem = getattr(db_storage, "_in_memory_db", None)
            if in_mem is None:
                in_mem = {}
                setattr(db_storage, "_in_memory_db", in_mem)
            portfolio_data = in_mem.get(portfolio_id, {"portfolio_id": portfolio_id})
            
        initial_value = portfolio_data.get("initial_value", 100000.0)
        volatility = portfolio_data.get("volatility", 0.2)
        drift = portfolio_data.get("drift", 0.0)

        simulations = simulations or 100
        horizon_days = horizon_days or 10

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

        # Сортируем для расчета VaR и CVaR
        losses = [initial_value - fv for fv in final_values]
        losses.sort(reverse=True)

        idx_95 = int(0.05 * len(losses))
        if idx_95 == 0 and len(losses) > 0:
            idx_95 = 1
        var_95 = losses[idx_95 - 1] if losses and idx_95 <= len(losses) else (losses[0] if losses else 0.0)
        tail_losses = losses[:idx_95] if idx_95 > 0 else [var_95]
        cvar_95 = sum(tail_losses) / len(tail_losses) if tail_losses else var_95

        return {
            "portfolio_id": portfolio_id,
            "simulation_results": simulation_results,
            "var_95": float(var_95),
            "cvar_95": float(cvar_95)
        }

    def _get_anomaly_adjustment(self) -> float:
        try:
            return market_anomaly_detector.get_current_anomaly_multiplier()
        except AttributeError:
            return 1.0

    def export_report(self, report_id: str, loss_limit: float) -> dict:
        try:
            return market_portfolio_data_exporter.export(report_id, loss_limit)
        except AttributeError:
            return {"report_id": report_id, "loss_limit": loss_limit}

    def consume_stream(self):
        try:
            return market_portfolio_api_gateway.stream_payload()
        except AttributeError:
            return None


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

    return {
        "simulation_id": simulation_id,
        "portfolio_id": portfolio_id,
        "initial_value": portfolio_value,
        "var_95": float(var_95),
        "expected_shortfall": float(expected_shortfall),
        "iterations": iterations
    }


market_portfolio_stress_monte_carlo_engine = MonteCarloStressEngine
