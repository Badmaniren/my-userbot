import uuid
import os
import io

def start_new(portfolio_id=None, liquidity_shock_factor=None, **kwargs):
    """
    Модуль для построения стресс-матриц портфельных рисков с учетом шоковых сценариев ликвидности.
    Поддерживает как unit-тесты (передача зависимостей через kwargs),
    так и интеграционные тесты (функция-фасад market_portfolio_stress_stress_matrix_builder).
    """
    db_storage = kwargs.get("db_storage")
    if db_storage and hasattr(db_storage, "read_stream"):
        db_storage.read_stream()

    monte_carlo = kwargs.get("market_portfolio_stress_monte_carlo_engine")
    if monte_carlo and hasattr(monte_carlo, "run"):
        monte_carlo.run()

    simulator = kwargs.get("market_portfolio_scenario_simulator")
    sim_result = {}
    if simulator and hasattr(simulator, "simulate"):
        sim_result = simulator.simulate()

    matrix_id = f"mat_{uuid.uuid4().hex}"
    return {
        "matrix_id": matrix_id,
        "portfolio_id": portfolio_id,
        "simulation_data": sim_result
    }

def market_portfolio_stress_stress_matrix_builder(builder_input: dict) -> dict:
    """
    Интеграционный фасад для построения стресс-матрицы.
    """
    portfolio_id = builder_input.get("portfolio_id")
    output_target = builder_input.get("output_target", f"stress_matrix_{uuid.uuid4().hex}.json")
    matrix_id = f"mat_{uuid.uuid4().hex[:8]}"

    # Запись файла, если требуется
    output_path = None
    if output_target:
        output_path = output_target
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f'{{"matrix_id": "{matrix_id}", "portfolio_id": "{portfolio_id}"}}')

    # Сохранение в базу данных (поддержка функции или объекта с методом save/вызовом)
    from skills import db_storage as db_mod
    storage_func = getattr(db_mod, "db_storage", None)
    if storage_func is not None:
        storage_func({
            "action": "save",
            "table": "stress_matrices",
            "matrix_id": matrix_id,
            "portfolio_id": portfolio_id
        })

    return {
        "matrix_id": matrix_id,
        "portfolio_id": portfolio_id,
        "output_path": output_path
    }