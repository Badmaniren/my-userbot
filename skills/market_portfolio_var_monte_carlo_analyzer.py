import math
import random
import statistics
import io

from skills import market_portfolio_data_exporter
from skills import market_anomaly_detector


def _percentile(data, p):
    """Вычисление p-го перцентиля списка чисел (p от 0 до 100) методом линейной интерполяции."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    if p <= 0:
        return float(sorted_data[0])
    if p >= 100:
        return float(sorted_data[-1])

    k = (len(sorted_data) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_data[int(k)])
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return float(d0 + d1)


class MarketPortfolioVaRMonteCarloAnalyzer:
    def __init__(self, db_storage=None, market_portfolio_stress_monte_carlo_engine=None, market_portfolio_scenario_simulator=None):
        self.db_storage = db_storage
        self.stress_engine = market_portfolio_stress_monte_carlo_engine
        self.scenario_simulator = market_portfolio_scenario_simulator

    def _fetch_historical_data(self, portfolio_id):
        # Заглушка для получения исторических данных, переопределяется через patch в тестах
        return {
            'portfolio_id': portfolio_id,
            'initial_value': 100000.0,
            'returns_sample': [0.01, -0.015, 0.005, -0.002, 0.008]
        }

    def compute_var(self, portfolio_id, confidence_level, simulations, horizon_days):
        data = self._fetch_historical_data(portfolio_id)
        returns = data.get('returns_sample', [])

        if not returns:
            raise ValueError("Empty returns sample provided.")

        initial_value = data.get('initial_value', 100000.0)

        mean = statistics.mean(returns)
        std = statistics.stdev(returns) if len(returns) > 1 else 0.01
        if std == 0:
            std = 0.01

        # Симуляции Монте-Карло по геометрическому броуновскому движению / нормальному распределению доходностей
        simulated_returns = [
            random.gauss(mean * horizon_days, std * math.sqrt(horizon_days))
            for _ in range(simulations)
        ]
        simulated_portfolio_values = [initial_value * (1 + r) for r in simulated_returns]
        portfolio_losses = [initial_value - v for v in simulated_portfolio_values]

        # Расчет VaR и Expected Shortfall (CVaR)
        var_percentile = (1 - confidence_level) * 100
        var_value = _percentile(portfolio_losses, 100 - var_percentile)
        var_value = max(0.0, var_value)

        tail_losses = [loss for loss in portfolio_losses if loss >= var_value]
        expected_shortfall = float(statistics.mean(tail_losses)) if len(tail_losses) > 0 else var_value

        result = {
            'portfolio_id': portfolio_id,
            'var_value': var_value,
            'expected_shortfall': expected_shortfall,
            'simulation_stats': {
                'simulations_run': simulations,
                'horizon_days': horizon_days,
                'initial_portfolio_value': float(initial_value)
            }
        }

        if self.db_storage and hasattr(self.db_storage, 'save_var_analysis'):
            self.db_storage.save_var_analysis(portfolio_id, result)

        return result

    def compute_stressed_var(self, portfolio_id, scenario_name, confidence_level, simulations):
        data = self._fetch_historical_data(portfolio_id)
        initial_value = data.get('initial_value', 100000.0)

        stress_res = {}
        if self.stress_engine and hasattr(self.stress_engine, 'run_stress_monte_carlo'):
            stress_res = self.stress_engine.run_stress_monte_carlo(
                portfolio_id=portfolio_id,
                simulations=simulations,
                scenario_name=scenario_name
            )

        shock_applied = stress_res.get('shock_applied', 0.2)
        stressed_var = stress_res.get('stressed_var', initial_value * shock_applied)

        return {
            'portfolio_id': portfolio_id,
            'scenario': scenario_name,
            'shock_applied': shock_applied,
            'stressed_var': stressed_var
        }

    def export_analysis_report(self, portfolio_id):
        if hasattr(market_portfolio_data_exporter, 'export_stream'):
            return market_portfolio_data_exporter.export_stream(portfolio_id)
        elif hasattr(market_portfolio_data_exporter, 'fetch_simulation_stream'):
            return market_portfolio_data_exporter.fetch_simulation_stream(portfolio_id)
        return None

    def check_portfolio_var_anomaly(self, portfolio_id, current_var):
        if hasattr(market_anomaly_detector, 'evaluate_var_anomaly'):
            return market_anomaly_detector.evaluate_var_anomaly(portfolio_id, current_var)
        return False


# Функциональные обертки для поддержки интеграционных тестов

def market_portfolio_var_monte_carlo_analyzer(portfolio_id, confidence=0.95, simulations=1000, stress_context=None):
    analyzer = MarketPortfolioVaRMonteCarloAnalyzer()
    res = analyzer.compute_var(
        portfolio_id=portfolio_id,
        confidence_level=confidence,
        simulations=simulations,
        horizon_days=1
    )
    res['stress_context'] = stress_context
    return res
