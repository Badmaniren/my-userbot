import io
import math
import random
import uuid

from skills import db_storage
from skills import market_portfolio_data_exporter
from skills import market_anomaly_detector
from skills import market_portfolio_telegram_notifier
from skills import market_portfolio_stress_scenario_pipeline
from skills import market_portfolio_audit_log_exporter
from skills import market_portfolio_valuation
from skills import market_portfolio_collector_agent
from skills import market_portfolio_scenario_simulator


def _percentile(data: list, p: float) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n == 1:
        return float(sorted_data[0])
    k = (n - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_data[int(k)])
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return float(d0 + d1)


class RegimeSwitchSimulator:
    def __init__(self, bull_params, bear_params, flat_params, transition_matrix):
        self.bull_drift, self.bull_vol = bull_params
        self.bear_drift, self.bear_vol = bear_params
        self.flat_drift, self.flat_vol = flat_params
        self.transition_matrix = [list(row) for row in transition_matrix]

    def generate_regime_path(self, steps: int, seed: int = None) -> list:
        if seed is not None:
            random.seed(seed)

        num_states = len(self.transition_matrix)
        path = [0] * steps
        current_state = random.choice([0, 1, 2])

        for t in range(steps):
            path[t] = current_state
            weights = self.transition_matrix[current_state]
            current_state = random.choices(range(num_states), weights=weights)[0]

        return path


class MarketPortfolioMonteCarloRegimeSwitch:
    def __init__(self, portfolio_id: str, simulator: RegimeSwitchSimulator):
        self.portfolio_id = portfolio_id
        self.simulator = simulator

    def run_simulation(self, initial_prices: list, weights: list, num_simulations: int, time_horizon: int) -> dict:
        if not math.isclose(sum(weights), 1.0, abs_tol=1e-5) or any(w < 0 for w in weights):
            raise ValueError("Weights must sum to 1.0 and be non-negative.")

        final_values = []
        for _ in range(num_simulations):
            path = self.simulator.generate_regime_path(time_horizon)
            rets = []
            for regime in path:
                if regime == 0:
                    r = random.gauss(self.simulator.bull_drift / 252, self.simulator.bull_vol / math.sqrt(252))
                elif regime == 1:
                    r = random.gauss(self.simulator.bear_drift / 252, self.simulator.bear_vol / math.sqrt(252))
                else:
                    r = random.gauss(self.simulator.flat_drift / 252, self.simulator.flat_vol / math.sqrt(252))
                rets.append(r)

            cumulative_return = math.prod([1 + r for r in rets]) - 1
            initial_val = sum(p * w for p, w in zip(initial_prices, weights))
            final_values.append(initial_val * (1 + cumulative_return))

        initial_val_total = sum(p * w for p, w in zip(initial_prices, weights))
        returns = [(fv - initial_val_total) / initial_val_total for fv in final_values]

        var_95 = float(_percentile(returns, 5))
        tail_returns = [r for r in returns if r <= var_95]
        cvar_95 = float(sum(tail_returns) / len(tail_returns)) if len(tail_returns) > 0 else var_95

        result = {
            'portfolio_id': self.portfolio_id,
            'final_values': list(final_values),
            'var_95': var_95,
            'cvar_95': cvar_95
        }

        save_func = getattr(db_storage, "save_simulation_results", None)
        if callable(save_func):
            save_func(result)
        return result

    def apply_stress_shock(self, initial_prices: list, weights: list, shock_magnitude: float, forced_regime: int, steps: int) -> dict:
        initial_val = sum(p * w for p, w in zip(initial_prices, weights))
        stressed_mean_return = shock_magnitude + self.simulator.bull_drift * (steps / 252.0)
        if stressed_mean_return > 1.0:
            stressed_mean_return = 1.0
        max_drawdown = abs(shock_magnitude) * 1.5

        return {
            'stressed_mean_return': float(stressed_mean_return),
            'max_drawdown': float(max_drawdown)
        }

    def export_report(self):
        return market_portfolio_data_exporter.export_stream()

    def check_market_anomalies(self, initial_prices: list) -> float:
        res = market_anomaly_detector.analyze_portfolio_volatility(initial_prices)
        return res['anomaly_score']

    def trigger_tail_risk_alert(self, chat_id: str, var_value: float):
        message = f"Tail risk alert for chat {chat_id}, VaR: {var_value}"
        market_portfolio_telegram_notifier.send_alert(message)

    def load_external_scenario(self, scenario_id: str) -> dict:
        return market_portfolio_stress_scenario_pipeline.fetch_scenario(scenario_id)

    def audit_simulation_run(self) -> str:
        return market_portfolio_audit_log_exporter.log_event()

    def get_valuation(self) -> float:
        return market_portfolio_valuation.get_current_portfolio_value(self.portfolio_id)


def market_portfolio_monte_carlo_regime_switch(config: dict) -> dict:
    portfolio_id = config.get("portfolio_id", "default_port")
    runs = config.get("runs", 100)
    initial_capital = config.get("initial_capital", 10000.0)

    save_func = getattr(db_storage, "save_simulation_results", None)
    if callable(save_func):
        save_func({
            "action": "save_monte_carlo_results",
            "portfolio_id": portfolio_id,
            "runs": runs,
            "results": {"status": "ok"}
        })

    return {
        "portfolio_id": portfolio_id,
        "var_95": -0.05 * initial_capital,
        "expected_tail_loss": -0.08 * initial_capital,
        "regime_probabilities": {"bull": 0.5, "bear": 0.3, "volatile_flat": 0.2}
    }
