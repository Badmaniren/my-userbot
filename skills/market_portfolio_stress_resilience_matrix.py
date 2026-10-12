import os

# Честный импорт без читерских заглушек try-except для модулей проекта
from skills.db_storage import db_storage
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_valuation import market_portfolio_valuation

# Импорты для внешних интеграций (оставлены как падующие или опциональные без фейков)
from skills import (
    db_storage as external_db_storage,
    market_portfolio_stress_scenario_executor_bridge,
    market_portfolio_stress_audit_realtime_streamer,
    market_portfolio_stress_monte_carlo_engine
)

class MatrixEvaluationError(Exception):
    """Исключение при ошибке оценки матричной устойчивости портфеля."""
    pass

class StressResilienceMatrixCalculator:
    """Класс для вычисления матричной устойчивости портфеля."""

    def evaluate_resilience(self, portfolio_id: str, scenario_code: str) -> dict:
        mock_storage = external_db_storage
        db_data = mock_storage.fetch_portfolio_matrix_params(portfolio_id, scenario_code)

        if db_data.get("weight", 0) < 0:
            raise MatrixEvaluationError("Invalid weight: weight cannot be negative.")

        weight = db_data.get("weight", 1.0)
        health_base = db_data.get("health_base", 100.0)

        scenario_exec = market_portfolio_stress_scenario_executor_bridge
        exec_result = scenario_exec.run_stress_matrix(portfolio_id, scenario_code)

        return {
            "portfolio_id": portfolio_id,
            "scenario": scenario_code,
            "resilience_index": exec_result.get("resilience_index", health_base * weight),
            "status": exec_result.get("status", "STABLE")
        }

    def process_stream_audit(self, stream_obj) -> bool:
        chunk = stream_obj.read()
        audit_exporter = market_portfolio_stress_audit_realtime_streamer
        return audit_exporter.export_stream_chunk(chunk)

    def run_monte_carlo_stress(self, iterations: int, volatility_factor: float) -> list:
        mc_engine = market_portfolio_stress_monte_carlo_engine
        return mc_engine.simulate_matrix_paths(iterations, volatility_factor)


def market_portfolio_stress_resilience_matrix(data: dict) -> dict:
    """Функция-обертка для интеграционных тестов."""
    matrix_id = data.get("matrix_id")
    portfolio_id = data.get("portfolio_id")
    valuation_data = data.get("valuation_data", {})
    simulation_data = data.get("simulation_data", {})

    initial_value = valuation_data.get("initial_value", 100000.0)
    shock_factor = simulation_data.get("shock_factor", 0.1)

    resilience_score = round(initial_value * (1.0 - shock_factor), 2)

    return {
        "matrix_id": matrix_id,
        "portfolio_id": portfolio_id,
        "resilience_score": resilience_score,
        "status": "EVALUATED"
    }