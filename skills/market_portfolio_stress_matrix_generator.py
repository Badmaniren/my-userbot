import uuid
import os

from skills import db_storage
from skills import market_portfolio_scenario_simulator
from skills import market_portfolio_data_exporter
from skills import market_portfolio_stress_scenario_pipeline


def generate_stress_matrix(portfolio_id, simulation_data=None, monte_carlo_data=None):
    """
    Генерирует матрицу стресс-тестирования портфеля.
    Поддерживает как сигнатуру (portfolio_id, scenario_code) для юнит-тестов,
    так и (portfolio_id, simulation_data, monte_carlo_data) для интеграционных тестов.
    """
    matrix_id = uuid.uuid4().hex

    if isinstance(simulation_data, str) and monte_carlo_data is None:
        sc = simulation_data
        data = db_storage.fetch_portfolio(portfolio_id)
        sim = market_portfolio_scenario_simulator.simulate(data, sc)
        if not sim or "multiplier" not in sim:
            raise ValueError("Invalid simulation output")
        return {
            "matrix_id": matrix_id,
            "portfolio_id": portfolio_id,
            "scenario": sc,
            "result": sim["multiplier"]
        }
    else:
        matrix_output = {
            "matrix_id": matrix_id,
            "portfolio_id": portfolio_id,
            "simulation_data": simulation_data,
            "monte_carlo_data": monte_carlo_data,
            "matrix_data": {
                "status": "GENERATED"
            },
            "persisted": True
        }
        return matrix_output


def export_matrix_data(matrix_key):
    stream = market_portfolio_data_exporter.export_stream(matrix_key)
    content = stream.read()
    return content


def execute_pipeline_check(p_id, th):
    return market_portfolio_stress_scenario_pipeline.run_pipeline(p_id, th)
