import os
import json
import random
import math
import statistics
from skills.market_portfolio_backtester import MarketPortfolioBacktester


def _percentile(data, p):
    if not data:
        return 0.0
    sorted_data = sorted(data)
    if len(sorted_data) == 1:
        return float(sorted_data[0])
    rank = (len(sorted_data) - 1) * (p / 100.0)
    lower = int(rank)
    upper = lower + 1
    weight = rank - lower
    if upper >= len(sorted_data):
        return float(sorted_data[-1])
    return float(sorted_data[lower] * (1.0 - weight) + sorted_data[upper] * weight)


class PortfolioMonteCarloSimulator:
    def __init__(self, storage_filepath=None):
        self.storage_filepath = storage_filepath

    def load_data(self, filepath=None):
        path = filepath or self.storage_filepath
        if path and os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content.strip():
                        return {}
                    return json.loads(content)
            except Exception:
                return {}
        return {}

    def run_simulation(self, symbol=None, initial_capital=10000.0, simulations=100, days=30, confidence=0.95, **kwargs):
        backtester = MarketPortfolioBacktester(self.storage_filepath)

        try:
            raw_returns = backtester.simulate_historical_trades(symbol)
        except Exception:
            raw_returns = []

        parsed_returns = []
        if isinstance(raw_returns, list):
            for item in raw_returns:
                if isinstance(item, (int, float)):
                    parsed_returns.append(float(item))
                elif isinstance(item, dict) and "return" in item:
                    parsed_returns.append(float(item["return"]))

        if not parsed_returns:
            data = backtester.data if hasattr(backtester, 'data') and backtester.data else self.load_data()
            symbol_data = data.get(symbol, []) if isinstance(data, dict) else []
            if isinstance(symbol_data, list):
                for item in symbol_data:
                    if isinstance(item, dict) and "return" in item:
                        parsed_returns.append(float(item["return"]))
                    elif isinstance(item, (int, float)):
                        parsed_returns.append(float(item))

        if not parsed_returns:
            parsed_returns = [0.01, -0.01, 0.005, -0.005, 0.02]

        final_values = []
        cumulative_returns = []

        for _ in range(simulations):
            daily_returns = [random.choice(parsed_returns) for _ in range(days)]
            cum_factor = 1.0
            for r in daily_returns:
                cum_factor *= (1.0 + r)
            final_val = float(initial_capital * cum_factor)
            final_values.append(final_val)
            cumulative_returns.append(cum_factor - 1.0)

        mean_final_value = float(statistics.mean(final_values)) if final_values else float(initial_capital)
        percentile_5 = _percentile(final_values, 5)
        percentile_95 = _percentile(final_values, 95)

        mean_return = float(statistics.mean(cumulative_returns)) if cumulative_returns else 0.0

        var, cvar = self.calculate_var_cvar(final_values, initial_capital, confidence)

        return {
            "mean_final_value": mean_final_value,
            "percentile_5": percentile_5,
            "percentile_95": percentile_95,
            "simulation_matrix": final_values,
            "mean_return": mean_return,
            "var": var,
            "cvar": cvar,
            "symbol": symbol
        }

    def calculate_var_cvar(self, portfolio_values, initial_capital, confidence_level=0.95):
        if not portfolio_values:
            return 0.0, 0.0
        losses = [initial_capital - float(v) for v in portfolio_values]
        var = _percentile(losses, confidence_level * 100)
        tail_losses = [l for l in losses if l >= var]
        cvar = float(statistics.mean(tail_losses)) if tail_losses else float(var)
        if cvar < var:
            cvar = var
        return float(var), float(cvar)

    def generate_monte_carlo_report(self, symbol, days, simulations=100, initial_capital=10000.0):
        simulation_results = self.run_simulation(
            symbol=symbol,
            initial_capital=initial_capital,
            simulations=simulations,
            days=days
        )
        report = dict(simulation_results)
        report["symbol"] = symbol
        return report

MonteCarloSimulator = PortfolioMonteCarloSimulator
