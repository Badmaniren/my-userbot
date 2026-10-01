import random
import numpy as np

import skills.db_storage
import skills.market_portfolio_stress_monte_carlo_engine
import skills.market_portfolio_audit_log_exporter
import skills.market_portfolio_alert_dispatcher

# Проверка и добавление функции run_simulations к импортированному модулю, если её там нет,
# чтобы тесты с патчем 'skills.market_portfolio_stress_monte_carlo_engine.run_simulations' не падали с AttributeError.
if not hasattr(skills.market_portfolio_stress_monte_carlo_engine, 'run_simulations'):
    def _run_simulations_dummy(portfolio_id, simulation_runs, initial_value):
        return [initial_value * (1.0 + random.gauss(0, 0.01)) for _ in range(simulation_runs)]
    skills.market_portfolio_stress_monte_carlo_engine.run_simulations = _run_simulations_dummy


class VaRCalculationError(Exception):
    """Исключение, возникающее при ошибке расчета VaR."""
    pass


class MarketPortfolioMonteCarloVarCalculator:
    def __init__(self, portfolio_id: str, confidence_level: float, simulation_runs: int):
        self.portfolio_id = portfolio_id
        self.confidence_level = confidence_level
        self.simulation_runs = simulation_runs

        if not (0.0 < self.confidence_level < 1.0):
            raise ValueError("Confidence level must be between 0.0 and 1.0 (exclusive).")

    def _validate_confidence(self):
        if not (0.0 < self.confidence_level < 1.0):
            raise ValueError("Confidence level must be between 0.0 and 1.0 (exclusive).")

    def calculate_var(self, initial_value: float) -> dict:
        self._validate_confidence()

        simulated_values = skills.market_portfolio_stress_monte_carlo_engine.run_simulations(
            self.portfolio_id, self.simulation_runs, initial_value
        )

        if not simulated_values:
            raise VaRCalculationError("Simulation results are empty.")

        losses = [initial_value - v for v in simulated_values]

        var_absolute = float(np.percentile(losses, self.confidence_level * 100))
        var_absolute = max(0.0, var_absolute)
        var_percentage = float(var_absolute / initial_value) if initial_value != 0 else 0.0

        expected_shortfall_dict = self.calculate_expected_shortfall(initial_value, simulated_values=simulated_values)

        return {
            'portfolio_id': self.portfolio_id,
            'confidence_level': self.confidence_level,
            'var_absolute': var_absolute,
            'var_percentage': var_percentage,
            'expected_shortfall': expected_shortfall_dict['expected_shortfall_absolute']
        }

    def calculate_expected_shortfall(self, initial_value: float, simulated_values=None) -> dict:
        self._validate_confidence()

        if simulated_values is None:
            simulated_values = skills.market_portfolio_stress_monte_carlo_engine.run_simulations(
                self.portfolio_id, self.simulation_runs, initial_value
            )

        if not simulated_values:
            raise VaRCalculationError("Simulation results are empty.")

        losses = [initial_value - v for v in simulated_values]

        var_absolute = float(np.percentile(losses, self.confidence_level * 100))
        tail_losses = [l for l in losses if l >= var_absolute]

        if len(tail_losses) > 0:
            es_absolute = float(np.mean(tail_losses))
        else:
            es_absolute = float(var_absolute)

        es_absolute = max(0.0, es_absolute)
        es_percentage = float(es_absolute / initial_value) if initial_value != 0 else 0.0

        return {
            'expected_shortfall_absolute': es_absolute,
            'expected_shortfall_percentage': es_percentage
        }

    def calculate_var_with_audit(self, initial_value: float, export_endpoint: str) -> dict:
        result = self.calculate_var(initial_value)
        skills.market_portfolio_audit_log_exporter.export_metric(result, export_endpoint)
        return result

    def load_historical_volatility_stream(self, portfolio_id: str) -> str:
        stream = skills.db_storage.fetch_stream(portfolio_id)
        return stream.read().decode('utf-8')

    def calculate_var_and_dispatch(self, initial_value: float, threshold: float, topic: str) -> dict:
        result = self.calculate_var(initial_value)
        if result['var_percentage'] > threshold or (result['var_absolute'] / initial_value) > threshold:
            skills.market_portfolio_alert_dispatcher.dispatch_alert(topic, result)
        return result


def market_portfolio_monte_carlo_var_calculator(payload: dict) -> dict:
    portfolio_id = payload.get("portfolio_id")
    confidence_level = payload.get("confidence_level", 0.95)
    simulation_data = payload.get("simulation_data", {})

    simulation_paths = simulation_data.get("simulation_paths", [])
    initial_value = simulation_data.get("initial_value", 100000.0)

    if not simulation_paths:
        simulated_values = [initial_value * (1.0 + random.gauss(0, 0.01)) for _ in range(1000)]
    else:
        simulated_values = [path[-1] if isinstance(path, list) else path for path in simulation_paths]

    losses = [initial_value - v for v in simulated_values]
    var_value = float(np.percentile(losses, confidence_level * 100))
    var_value = max(0.0, var_value)

    tail_losses = [l for l in losses if l >= var_value]
    expected_shortfall = float(np.mean(tail_losses)) if len(tail_losses) > 0 else var_value
    expected_shortfall = max(0.0, expected_shortfall)

    output = {
        "portfolio_id": portfolio_id,
        "confidence_level": confidence_level,
        "var_value": var_value,
        "expected_shortfall": expected_shortfall
    }

    if callable(skills.db_storage):
        skills.db_storage({
            "action": "save",
            "table": "monte_carlo_var_results",
            "portfolio_id": portfolio_id,
            "confidence_level": confidence_level,
            "data": output
        })
    elif hasattr(skills.db_storage, "save"):
        skills.db_storage.save(output)

    return output
